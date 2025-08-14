from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers, status
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
import traceback
import base64
from django.core.files.base import ContentFile
from django.db import transaction

from ..models import (
    BerealPost,
    BerealLike,
    BerealReport,
    BerealNotification,
    Setting,
)
from ..api.notifications import send_notification, UserFCMToken

User = get_user_model()


class BeerealPostSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.first_name", read_only=True)
    # user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    user_photo = serializers.ImageField(
        source="user.tinderprofile.photo", read_only=True
    )
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    is_post_owner = serializers.SerializerMethodField()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_post_owner(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    class Meta:
        model = BerealPost
        fields = [
            "id",
            "user",
            "user_name",
            # "user_last_name",
            "user_photo",
            "photo1",
            "photo2",
            # "created_at",
            "is_late",
            # "bereal_date",
            "likes_count",
            "is_liked_by_user",
            "is_post_owner",
        ]


class BeerealLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.first_name", read_only=True)

    class Meta:
        model = BerealLike
        fields = ["id", "user", "user_name", "created_at"]


def bereal_active():
    """Check if BeReal is currently active"""
    try:
        setting = Setting.objects.get(name="bereal_active")
        return setting.value.lower() == "true"
    except Setting.DoesNotExist:
        return False


def get_today_bereal():
    """Get today's BeReal notification (active or expired)"""
    today = timezone.now().date()
    return BerealNotification.objects.filter(date=today).first()


def get_bereal_status(user=None):
    # Get current BeReal status
    today_bereal = get_today_bereal()

    bereal_status = {
        "is_active": bereal_active(),  # Czy bereal jest aktywowany w backendzie
        "was_today": today_bereal
        is not None,  # Czy dzisiaj zostało wysłane powiadomienie bereal
        "can_post": bool(
            today_bereal
            and user
            and not BerealPost.objects.filter(
                user=user, bereal_date=today_bereal.date
            ).exists()
        ),
        "deadline": today_bereal.deadline if today_bereal else None,
    }

    return bereal_status


@api_view(["GET"])
def bereal_home(request):
    """Home/main BeReal screen with paginated posts"""
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    # Get all posts ordered by newest
    posts = (
        BerealPost.objects.select_related("user")
        .prefetch_related("likes")
        .order_by("-created_at")
    )

    # Paginate
    paginator = Paginator(posts, page_size)
    page_obj = paginator.get_page(page)

    # Serialize posts
    serializer = BeerealPostSerializer(
        page_obj, many=True, context={"request": request}
    )

    return Response(
        {
            "posts": serializer.data,
            "pagination": {
                "current_page": page,
                "total_pages": paginator.num_pages,
                "total_posts": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
            "bereal_status": get_bereal_status(request.user),
        }
    )


@api_view(["GET"])
def bereal_profile(request, user_id=None):
    """Profile endpoint - current user or specific user"""
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "Użytkownik nie istnieje"}, status=404)
    else:
        user = request.user

    # Get user's posts
    posts = BerealPost.objects.filter(user=user).order_by("-created_at")
    post_serializer = BeerealPostSerializer(
        posts, many=True, context={"request": request}
    )

    photo_url = None
    tp = getattr(user, "tinderprofile", None)
    if tp and getattr(tp, "photo", None):
        try:
            photo_url = request.build_absolute_uri(tp.photo.url)
        except Exception:
            photo_url = None

    return Response(
        {
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "photo": photo_url,
            },
            "posts": post_serializer.data,
        }
    )


@api_view(["GET"])
def bereal_post_detail(request, post_id):
    """Get details of a specific BeReal post"""
    try:
        post = BerealPost.objects.get(id=post_id)
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje"}, status=404)

    serializer = BeerealPostSerializer(post, context={"request": request})
    return Response({"success": True, "post": serializer.data})


@api_view(["POST"])
def upload_bereal_post(request):
    """Upload new BeReal post with daily limit validation"""
    if not bereal_active():
        return Response({"error": "BeReal jest obecnie wyłączony"}, status=400)

    today_bereal = get_today_bereal()
    if not today_bereal:
        return Response(
            {"error": "Dziś nie było jeszcze powiadomienia BeReal"}, status=400
        )

    # Check if user already posted today
    if BerealPost.objects.filter(
        user=request.user, bereal_date=today_bereal.date
    ).exists():
        return Response({"error": "Już przesłałeś/aś zdjęcie na dzisiaj"}, status=400)

    photo1_base64 = request.data.get("photo1")
    photo2_base64 = request.data.get("photo2")
    if not photo1_base64 or not photo2_base64:
        return Response({"error": "Brak zdjęcia"}, status=400)

    try:
        with transaction.atomic():
            photo1 = ContentFile(
                base64.b64decode(photo1_base64),
                f"bereal_photo1_{request.user.id}_{today_bereal.date}.jpeg",
            )
            photo2 = ContentFile(
                base64.b64decode(photo2_base64),
                f"bereal_photo2_{request.user.id}_{today_bereal.date}.jpeg",
            )

            # Create the post
            post = BerealPost.objects.create(
                user=request.user,
                bereal_date=today_bereal.date,
                is_late=not today_bereal.is_active(),
                photo1=photo1,
                photo2=photo2,
            )

            serializer = BeerealPostSerializer(post, context={"request": request})
            return Response({"success": True, "post": serializer.data})

    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": f"Błąd podczas przesyłania zdjęcia: {str(e)}"}, status=400
        )


@api_view(["DELETE"])
def delete_bereal_post(request, post_id):
    """Delete BeReal post (only own posts)"""
    try:
        post = BerealPost.objects.get(id=post_id, user=request.user)
        post.delete()
        return Response({"success": True})
    except BerealPost.DoesNotExist:
        return Response(
            {"error": "Post nie istnieje lub nie masz uprawnień"}, status=404
        )


@api_view(["POST"])
def like_bereal_post(request, post_id):
    """Like a BeReal post"""
    try:
        post = BerealPost.objects.get(id=post_id)
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje"}, status=404)

    like, created = BerealLike.objects.get_or_create(user=request.user, post=post)

    if not created:
        return Response({"error": "Już polajkowałeś/aś ten post"}, status=400)

    return Response({"success": True, "likes_count": post.likes.count()})


@api_view(["DELETE"])
def unlike_bereal_post(request, post_id):
    """Unlike a BeReal post"""
    try:
        post = BerealPost.objects.get(id=post_id)
        like = BerealLike.objects.get(user=request.user, post=post)
        like.delete()
        return Response({"success": True, "likes_count": post.likes.count()})
    except (BerealPost.DoesNotExist, BerealLike.DoesNotExist):
        return Response({"error": "Post lub lajk nie istnieje"}, status=404)


@api_view(["POST"])
def report_bereal_post(request, post_id):
    """Report a BeReal post"""
    try:
        post = BerealPost.objects.get(id=post_id)
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje"}, status=404)

    reason = request.data.get("reason", "")
    if not reason:
        return Response({"error": "Podaj powód zgłoszenia"}, status=400)

    # Check if already reported by this user
    if BerealReport.objects.filter(reporter=request.user, post=post).exists():
        return Response({"error": "Już zgłosiłeś/aś ten post"}, status=400)

    # Create report
    report = BerealReport.objects.create(
        reporter=request.user, post=post, reason=reason
    )

    # Send notification to admins
    try:
        admin_tokens = list(
            UserFCMToken.objects.filter(
                user__groups__name__in=["Kadra", "Sztab", "Admin"]
            ).values_list("token", flat=True)
        )

        if admin_tokens:
            title = "Nowe zgłoszenie BeReal"
            content = f"Post użytkownika {post.user.first_name} został zgłoszony przez {request.user.first_name}"
            send_notification(title, content, admin_tokens)
    except Exception:
        pass  # Don't fail if notification sending fails

    return Response({"success": True})


@api_view(["GET"])
def bereal_status(request):
    """Get current BeReal status for background checking"""

    return Response(get_bereal_status(request.user))


@api_view(["POST"])
def update_profile_photo(request):
    """Update user's profile photo (reusing Tinder upload logic)"""
    photo_base64 = request.data.get("photo")
    if not photo_base64:
        return Response({"error": "Brak zdjęcia"}, status=400)

    try:
        format, imgstr = photo_base64.split(";base64,")
        ext = format.split("/")[-1]

        request.user.photo.save(
            f"profile_{request.user.id}.{ext}",
            ContentFile(base64.b64decode(imgstr)),
            save=True,
        )

        return Response(
            {
                "success": True,
                "photo_url": request.user.photo.url if request.user.photo else None,
            }
        )

    except Exception as e:
        return Response(
            {"error": f"Błąd podczas przesyłania zdjęcia: {str(e)}"}, status=400
        )
