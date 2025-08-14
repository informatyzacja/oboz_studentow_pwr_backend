from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers, status
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import get_user_model

import base64
from django.core.files.base import ContentFile

from ..models import BeerealPost, BeerealLike, BeerealReport, BeerealNotification, Setting
from ..api.notifications import send_notification, UserFCMToken

User = get_user_model()


class BeerealPostSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True) 
    user_photo = serializers.ImageField(source='user.photo', read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    class Meta:
        model = BeerealPost
        fields = [
            'id', 'user', 'user_name', 'user_last_name', 'user_photo', 
            'photo', 'created_at', 'is_late', 'bereal_date',
            'likes_count', 'is_liked_by_user'
        ]


class BeerealLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = BeerealLike
        fields = ['id', 'user', 'user_name', 'created_at']


def bereal_active():
    """Check if BeReal is currently active"""
    try:
        setting = Setting.objects.get(name="bereal_active")
        return setting.value.lower() == "true"
    except Setting.DoesNotExist:
        return False


def get_current_bereal():
    """Get the current active BeReal notification"""
    now = timezone.now()
    return BeerealNotification.objects.filter(
        date=now.date(),
        deadline__gt=now
    ).first()


def get_today_bereal():
    """Get today's BeReal notification (active or expired)"""
    today = timezone.now().date()
    return BeerealNotification.objects.filter(date=today).first()


@api_view(['GET'])
def bereal_home(request):
    """Home/main BeReal screen with paginated posts"""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    # Get all posts ordered by newest
    posts = BeerealPost.objects.select_related('user').prefetch_related('likes').order_by('-created_at')
    
    # Paginate
    paginator = Paginator(posts, page_size)
    page_obj = paginator.get_page(page)
    
    # Serialize posts
    serializer = BeerealPostSerializer(page_obj, many=True, context={'request': request})
    
    # Get current BeReal status
    current_bereal = get_current_bereal()
    today_bereal = get_today_bereal()
    
    bereal_status = {
        'is_active': current_bereal is not None,
        'was_today': today_bereal is not None,
        'can_post': current_bereal is not None or (today_bereal and today_bereal.is_late_period()),
        'deadline': current_bereal.deadline if current_bereal else None,
        'is_late_period': today_bereal.is_late_period() if today_bereal else False
    }
    
    return Response({
        'posts': serializer.data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_posts': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        },
        'bereal_status': bereal_status
    })


@api_view(['GET'])
def bereal_profile(request, user_id=None):
    """Profile endpoint - current user or specific user"""
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Użytkownik nie istnieje'}, status=404)
    else:
        user = request.user
    
    # Get user's posts
    posts = BeerealPost.objects.filter(user=user).order_by('-created_at')
    post_serializer = BeerealPostSerializer(posts, many=True, context={'request': request})
    
    return Response({
        'user': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'photo': user.photo.url if user.photo else None
        },
        'posts': post_serializer.data
    })


@api_view(['POST'])
def upload_bereal_post(request):
    """Upload new BeReal post with daily limit validation"""
    if not bereal_active():
        return Response({'error': 'BeReal jest obecnie wyłączony'}, status=400)
    
    today_bereal = get_today_bereal()
    if not today_bereal:
        return Response({'error': 'Dziś nie było jeszcze powiadomienia BeReal'}, status=400)
    
    if not today_bereal.is_late_period():
        return Response({'error': 'Czas na przesyłanie zdjęć już minął'}, status=400)
    
    # Check if user already posted today
    if BeerealPost.objects.filter(user=request.user, bereal_date=today_bereal.date).exists():
        return Response({'error': 'Już przesłałeś/aś zdjęcie na dzisiaj'}, status=400)
    
    photo_base64 = request.data.get('photo')
    if not photo_base64:
        return Response({'error': 'Brak zdjęcia'}, status=400)
    
    try:
        # Process base64 image
        format, imgstr = photo_base64.split(';base64,')
        ext = format.split('/')[-1]
        
        # Create the post
        post = BeerealPost.objects.create(
            user=request.user,
            bereal_date=today_bereal.date,
            is_late=not today_bereal.is_active()
        )
        
        # Save the photo
        post.photo.save(
            f"bereal_{request.user.id}_{today_bereal.date}.{ext}",
            ContentFile(base64.b64decode(imgstr)),
            save=True
        )
        
        serializer = BeerealPostSerializer(post, context={'request': request})
        return Response({
            'success': True,
            'post': serializer.data
        })
        
    except Exception as e:
        return Response({'error': f'Błąd podczas przesyłania zdjęcia: {str(e)}'}, status=400)


@api_view(['DELETE'])
def delete_bereal_post(request, post_id):
    """Delete BeReal post (only own posts)"""
    try:
        post = BeerealPost.objects.get(id=post_id, user=request.user)
        post.delete()
        return Response({'success': True})
    except BeerealPost.DoesNotExist:
        return Response({'error': 'Post nie istnieje lub nie masz uprawnień'}, status=404)


@api_view(['POST'])
def like_bereal_post(request, post_id):
    """Like a BeReal post"""
    try:
        post = BeerealPost.objects.get(id=post_id)
    except BeerealPost.DoesNotExist:
        return Response({'error': 'Post nie istnieje'}, status=404)
    
    like, created = BeerealLike.objects.get_or_create(user=request.user, post=post)
    
    if not created:
        return Response({'error': 'Już polajkowałeś/aś ten post'}, status=400)
    
    return Response({'success': True, 'likes_count': post.likes.count()})


@api_view(['DELETE'])
def unlike_bereal_post(request, post_id):
    """Unlike a BeReal post"""
    try:
        post = BeerealPost.objects.get(id=post_id)
        like = BeerealLike.objects.get(user=request.user, post=post)
        like.delete()
        return Response({'success': True, 'likes_count': post.likes.count()})
    except (BeerealPost.DoesNotExist, BeerealLike.DoesNotExist):
        return Response({'error': 'Post lub lajk nie istnieje'}, status=404)


@api_view(['POST'])
def report_bereal_post(request, post_id):
    """Report a BeReal post"""
    try:
        post = BeerealPost.objects.get(id=post_id)
    except BeerealPost.DoesNotExist:
        return Response({'error': 'Post nie istnieje'}, status=404)
    
    reason = request.data.get('reason', '')
    if not reason:
        return Response({'error': 'Podaj powód zgłoszenia'}, status=400)
    
    # Check if already reported by this user
    if BeerealReport.objects.filter(reporter=request.user, post=post).exists():
        return Response({'error': 'Już zgłosiłeś/aś ten post'}, status=400)
    
    # Create report
    report = BeerealReport.objects.create(
        reporter=request.user,
        post=post,
        reason=reason
    )
    
    # Send notification to admins
    try:
        admin_tokens = list(UserFCMToken.objects.filter(
            user__groups__name__in=['Kadra', 'Sztab', 'Admin']
        ).values_list('token', flat=True))
        
        if admin_tokens:
            title = "Nowe zgłoszenie BeReal"
            content = f"Post użytkownika {post.user.first_name} został zgłoszony przez {request.user.first_name}"
            send_notification(title, content, admin_tokens)
    except Exception:
        pass  # Don't fail if notification sending fails
    
    return Response({'success': True})


@api_view(['GET'])
def bereal_status(request):
    """Get current BeReal status for background checking"""
    current_bereal = get_current_bereal()
    today_bereal = get_today_bereal()
    
    return Response({
        'is_active': current_bereal is not None,
        'was_today': today_bereal is not None,
        'can_post': current_bereal is not None or (today_bereal and today_bereal.is_late_period()),
        'deadline': current_bereal.deadline if current_bereal else None,
        'is_late_period': today_bereal.is_late_period() if today_bereal else False,
        'bereal_enabled': bereal_active()
    })


@api_view(['POST'])
def update_profile_photo(request):
    """Update user's profile photo (reusing Tinder upload logic)"""
    photo_base64 = request.data.get('photo')
    if not photo_base64:
        return Response({'error': 'Brak zdjęcia'}, status=400)

    try:
        format, imgstr = photo_base64.split(';base64,')
        ext = format.split('/')[-1]

        request.user.photo.save(
            f"profile_{request.user.id}.{ext}",
            ContentFile(base64.b64decode(imgstr)),
            save=True
        )

        return Response({
            'success': True,
            'photo_url': request.user.photo.url if request.user.photo else None
        })

    except Exception as e:
        return Response({'error': f'Błąd podczas przesyłania zdjęcia: {str(e)}'}, status=400)