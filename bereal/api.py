from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers
from django.core.paginator import Paginator
from django.utils import timezone
import base64
from django.core.files.base import ContentFile
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import (
    BerealPost,
    BerealLike,
    BerealReport,
    BerealNotification,
)
from obozstudentow.models import Setting
from obozstudentow.api.notifications import send_notification, UserFCMToken
from datetime import datetime

User = get_user_model()


class BeerealPostSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.first_name", read_only=True)
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
            "user_photo",
            "photo1",
            "photo2",
            "is_late",
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
    try:
        setting = Setting.objects.get(name="bereal_active")
        return setting.value.lower() == "true"
    except Setting.DoesNotExist:
        return False


def get_today_bereal():
    today = timezone.now().date()
    return BerealNotification.objects.filter(date=today).first()


def get_last_sent_bereal():
    return BerealNotification.objects.filter(is_sent=True).order_by("-date").first()

def get_bereal_status(user=None):
    last_sent = get_last_sent_bereal()
    visible = last_sent is not None
    deadline_dt = None
    if visible and last_sent.deadline:
         deadline_dt = last_sent.deadline_at
    can_post = (
        visible
        and user
        and not BerealPost.objects.filter(user=user, bereal_date=last_sent.date).exists()
    )
    return {
        "is_active": bereal_active(),
        "was_today": bool(visible),
        "can_post": can_post,
        "deadline": deadline_dt,
    }

@api_view(["POST"])
def upload_bereal_post(request):
    if not bereal_active():
        return Response({"error": "BeReal jest obecnie wyłączony"}, status=400)
    last_sent = get_last_sent_bereal()
    if not last_sent:
        return Response({"error": "Nie było jeszcze powiadomienia BeReal"}, status=400)
    if BerealPost.objects.filter(user=request.user, bereal_date=last_sent.date).exists():
        return Response(
            {"error": "Już przesłałeś/aś zdjęcie na ten dzień", "redirect": True}, status=400
        )
    photo1_base64 = request.data.get("photo1")
    photo2_base64 = request.data.get("photo2")
    if not photo1_base64 or not photo2_base64:
        return Response({"error": "Brak zdjęcia"}, status=400)
    try:
        with transaction.atomic():
            photo1 = ContentFile(
                base64.b64decode(photo1_base64),
                f"bereal_photo1_{request.user.id}_{last_sent.date}.jpeg",
            )
            photo2 = ContentFile(
                base64.b64decode(photo2_base64),
                f"bereal_photo2_{request.user.id}_{last_sent.date}.jpeg",
            )
            post = BerealPost.objects.create(
                user=request.user,
                bereal_date=last_sent.date,
                is_late=not last_sent.is_active(),
                photo1=photo1,
                photo2=photo2,
            )
            serializer = BeerealPostSerializer(post, context={"request": request})
            return Response({"success": True, "post": serializer.data})
    except Exception as e:
        return Response(
            {"error": f"Błąd podczas przesyłania zdjęcia: {str(e)}"}, status=400
        )

@api_view(["GET"])
def bereal_home(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    # Posty dnia również powinny stać się widoczne dopiero po wysłaniu powiadomienia.
    today = timezone.now().date()
    today_bereal = get_today_bereal()
    posts_qs = (
        BerealPost.objects.select_related("user")
        .prefetch_related("likes")
        .order_by("-created_at")
    )
    if not (today_bereal and today_bereal.is_sent):
        # ukryj dzisiejsze posty, zwracaj tylko wcześniejsze
        posts_qs = posts_qs.exclude(bereal_date=today)
    posts = posts_qs
    paginator = Paginator(posts, page_size)
    page_obj = paginator.get_page(page)
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
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "Użytkownik nie istnieje"}, status=404)
    else:
        user = request.user

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
    try:
        post = BerealPost.objects.get(id=post_id)
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje"}, status=404)
    serializer = BeerealPostSerializer(post, context={"request": request})
    return Response({"success": True, "post": serializer.data})


@api_view(["DELETE"])
def delete_bereal_post(request, post_id):
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
    try:
        post = BerealPost.objects.get(id=post_id)
        like = BerealLike.objects.get(user=request.user, post=post)
        like.delete()
        return Response({"success": True, "likes_count": post.likes.count()})
    except (BerealPost.DoesNotExist, BerealLike.DoesNotExist):
        return Response({"error": "Post lub lajk nie istnieje"}, status=404)


@api_view(["POST"])
def report_bereal_post(request, post_id):
    try:
        post = BerealPost.objects.get(id=post_id)
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje"}, status=404)
    reason = request.data.get("reason", "")
    if not reason:
        return Response({"error": "Podaj powód zgłoszenia"}, status=400)
    if BerealReport.objects.filter(reporter=request.user, post=post).exists():
        return Response({"error": "Już zgłosiłeś/aś ten post"}, status=400)
    BerealReport.objects.create(reporter=request.user, post=post, reason=reason)
    try:
        # Użytkownicy uprawnieni do zobaczenia modelu BerealReport w adminie
        bereal_perms = [
            "view_berealreport",
            "change_berealreport",
            "add_berealreport",
            "delete_berealreport",
        ]
        admin_users = (
            User.objects.filter(
                Q(is_superuser=True)
                | Q(
                    user_permissions__codename__in=bereal_perms,
                    user_permissions__content_type__app_label="bereal",
                )
                | Q(
                    groups__permissions__codename__in=bereal_perms,
                    groups__permissions__content_type__app_label="bereal",
                )
            )
            .distinct()
            .values_list("id", flat=True)
        )
        admin_tokens = list(
            UserFCMToken.objects.filter(
                user__notifications=True, user_id__in=admin_users
            ).values_list("token", flat=True)
        )
        if admin_tokens:
            title = "Nowe zgłoszenie BeReal"
            content = f"Post użytkownika {post.user.first_name} został zgłoszony przez {request.user.first_name}"
            send_notification.delay(title, content, admin_tokens)
    except Exception:
        pass
    return Response({"success": True})


@api_view(["GET"])
def bereal_status(request):
    return Response(get_bereal_status(request.user))


@api_view(["POST"])
def update_profile_photo(request):
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
