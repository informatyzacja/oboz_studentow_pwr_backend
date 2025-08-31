from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers
from django.core.paginator import Paginator
from django.utils import timezone
import base64
from django.core.files.base import ContentFile
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from datetime import datetime

from .models import (
    BerealPost,
    BerealLike,
    BerealReport,
    BerealNotification,
)
from obozstudentow.models import Setting
from obozstudentow.api.notifications import send_notification, UserFCMToken

User = get_user_model()


class BeerealPostSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.first_name", read_only=True)
    user_photo = serializers.ImageField(source="user.tinderprofile.photo", read_only=True)
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
        return str(setting.value).lower() == "true"
    except Setting.DoesNotExist:
        return False


def get_today_bereal():
    today = timezone.now().date()
    return BerealNotification.objects.filter(date=today).first()


def get_last_sent_bereal():
    # Ostatnie wysłane powiadomienie (po polu "date")
    return BerealNotification.objects.filter(is_sent=True).order_by("-date").first()


def _safe_b64_to_content(b64_str: str, filename: str) -> ContentFile:
    """Dekoduje base64 z możliwym prefiksem data:*;base64, i zwraca ContentFile."""
    if ";base64," in b64_str:
        _, b64_data = b64_str.split(";base64,", 1)
    else:
        b64_data = b64_str
    try:
        return ContentFile(base64.b64decode(b64_data), name=filename)
    except Exception as e:
        raise ValueError(f"Nieprawidłowe dane obrazu base64: {e}")


def get_bereal_status(user=None):
    last_sent = get_last_sent_bereal()
    visible = last_sent is not None
    deadline_iso = None
    is_active_flag = False

    if visible and last_sent.deadline:
        try:
            dt_deadline = datetime.combine(last_sent.date, last_sent.deadline)
            if timezone.is_naive(dt_deadline):
                dt_deadline = timezone.make_aware(dt_deadline, timezone.get_current_timezone())
            deadline_iso = dt_deadline.isoformat()
            now = timezone.now()
            # Okno aktywne: powiadomienie wysłane, deadline ustawiony, teraz < deadline (tego samego dnia)
            is_active_flag = (
                bool(last_sent.is_sent)
                and now.date() == last_sent.date
                and now.time() < last_sent.deadline
            )
        except Exception:
            deadline_iso = None
            is_active_flag = False

    can_post = (
        visible
        and user is not None
        and not (
            last_sent
            and BerealPost.objects.filter(user=user, bereal_date=last_sent.date).exists()
        )
    )
    return {
        "is_active": is_active_flag,
        "was_today": bool(visible),
        "can_post": bool(can_post),
        "deadline": deadline_iso,
    }


@api_view(["POST"])
def upload_bereal_post(request):
    if not request.user.is_authenticated:
        return Response({"error": "Brak autoryzacji"}, status=401)

    if not bereal_active():
        return Response({"error": "BeReal jest obecnie wyłączony"}, status=400)
    
    last_sent = get_last_sent_bereal()
    if not last_sent:
        return Response({"error": "Nie było jeszcze powiadomienia BeReal"}, status=400)

    # Można zrobić BeReal tylko jeśli nie zrobiłeś go w tej rundzie
    if BerealPost.objects.filter(user=request.user, bereal_date=last_sent.date).exists():
        return Response({"error": "Już przesłałeś/aś zdjęcie na ten dzień", "redirect": True}, status=400)

    photo1_base64 = request.data.get("photo1")
    photo2_base64 = request.data.get("photo2")
    if not photo1_base64 or not photo2_base64:
        return Response({"error": "Brak zdjęcia"}, status=400)

    try:
        with transaction.atomic():
            photo1 = _safe_b64_to_content(photo1_base64, f"bereal_photo1_{request.user.id}_{last_sent.date}.jpeg")
            photo2 = _safe_b64_to_content(photo2_base64, f"bereal_photo2_{request.user.id}_{last_sent.date}.jpeg")

            post = BerealPost.objects.create(
                user=request.user,
                bereal_date=last_sent.date,
                is_late=not get_bereal_status(request.user)["is_active"],
                photo1=photo1,
                photo2=photo2,
            )
            serializer = BeerealPostSerializer(post, context={"request": request})
            return Response({"success": True, "post": serializer.data})
    except Exception as e:
        return Response({"error": f"Błąd podczas przesyłania zdjęcia: {str(e)}"}, status=400)


@api_view(["GET"])
def bereal_home(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))
    scope = request.GET.get("scope")  # 'oboz' | 'frakcja' | None
    time_filter = request.GET.get("time")  # 'dzisiaj' | 'all'
    sort = request.GET.get("sort")  # 'popular' | 'recent'

    today = timezone.now().date()
    today_bereal = get_today_bereal()

    posts_qs = (
        BerealPost.objects.select_related("user", "user__tinderprofile")
        .prefetch_related("likes")
        .annotate(likes_count=Count("likes"))
    )

    # Time filter
    if time_filter == "dzisiaj":
        # Pokazuj dzisiejsze posty tylko jeśli powiadomienie wysłane
        if today_bereal and today_bereal.is_sent:
            posts_qs = posts_qs.filter(bereal_date=today_bereal.date)
        else:
            posts_qs = posts_qs.none()
    else:
        # W trybie "all" chowaj dzisiejsze posty jeśli powiadomienie nie wysłane
        if not (today_bereal and today_bereal.is_sent):
            posts_qs = posts_qs.exclude(bereal_date=today)

    # Scope filter
    def _detect_profile_field_and_value(user):
        if not user or not getattr(user, "is_authenticated", False):
            return (None, None)
        tp = getattr(user, "tinderprofile", None)
        if tp is not None:
            for field in ("oboz", "camp", "frakcja", "group"):
                if hasattr(tp, field):
                    return (f"user__tinderprofile__{field}", getattr(tp, field))
        for field in ("oboz", "camp", "frakcja", "group"):
            if hasattr(user, field):
                return (f"user__{field}", getattr(user, field))
        try:
            groups = user.groups.all()
            if groups.exists():
                return ("user__groups__in", list(groups.values_list("id", flat=True)))
        except Exception:
            pass
        return (None, None)

    if scope in ("oboz", "frakcja"):
        field_name, value = _detect_profile_field_and_value(request.user)
        if field_name and value is not None:
            posts_qs = posts_qs.filter(**{field_name: value})

    # Sorting
    if sort == "popular":
        posts_qs = posts_qs.order_by("-likes_count", "-created_at")
    else:
        posts_qs = posts_qs.order_by("-created_at")

    paginator = Paginator(posts_qs, page_size)
    page_obj = paginator.get_page(page)
    serializer = BeerealPostSerializer(page_obj, many=True, context={"request": request})
    return Response(
        {
            "posts": serializer.data,
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "total_posts": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
            "bereal_status": get_bereal_status(request.user if request.user.is_authenticated else None),
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
        if not request.user.is_authenticated:
            return Response({"error": "Brak autoryzacji"}, status=401)
        user = request.user

    posts = BerealPost.objects.filter(user=user).order_by("-created_at")
    post_serializer = BeerealPostSerializer(posts, many=True, context={"request": request})

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
    if not request.user.is_authenticated:
        return Response({"error": "Brak autoryzacji"}, status=401)
    try:
        post = BerealPost.objects.get(id=post_id, user=request.user)
        post.delete()
        return Response({"success": True})
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje lub nie masz uprawnień"}, status=404)


@api_view(["POST"])
def like_bereal_post(request, post_id):
    if not request.user.is_authenticated:
        return Response({"error": "Brak autoryzacji"}, status=401)
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
    if not request.user.is_authenticated:
        return Response({"error": "Brak autoryzacji"}, status=401)
    try:
        post = BerealPost.objects.get(id=post_id)
        like = BerealLike.objects.get(user=request.user, post=post)
        like.delete()
        return Response({"success": True, "likes_count": post.likes.count()})
    except (BerealPost.DoesNotExist, BerealLike.DoesNotExist):
        return Response({"error": "Post lub lajk nie istnieje"}, status=404)


@api_view(["POST"])
def report_bereal_post(request, post_id):
    if not request.user.is_authenticated:
        return Response({"error": "Brak autoryzacji"}, status=401)
    try:
        post = BerealPost.objects.get(id=post_id)
    except BerealPost.DoesNotExist:
        return Response({"error": "Post nie istnieje"}, status=404)

    reason = request.data.get("reason", "").strip()
    if not reason:
        return Response({"error": "Podaj powód zgłoszenia"}, status=400)

    if BerealReport.objects.filter(reporter=request.user, post=post).exists():
        return Response({"error": "Już zgłosiłeś/aś ten post"}, status=400)

    BerealReport.objects.create(reporter=request.user, post=post, reason=reason)

    # Powiadom adminów (bez twardego crasha, jeśli coś pójdzie nie tak)
    try:
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
    return Response(get_bereal_status(request.user if request.user.is_authenticated else None))


@api_view(["POST"])
def update_profile_photo(request):
    if not request.user.is_authenticated:
        return Response({"error": "Brak autoryzacji"}, status=401)

    photo_base64 = request.data.get("photo")
    if not photo_base64:
        return Response({"error": "Brak zdjęcia"}, status=400)

    try:
        # Wyciągnij rozszerzenie, jeśli jest prefiks data:...
        ext = "jpg"
        if photo_base64.startswith("data:") and ";base64," in photo_base64:
            header, _ = photo_base64.split(";base64,", 1)
            # data:image/png
            if "/" in header:
                ext = header.split("/")[-1]
        content = _safe_b64_to_content(photo_base64, f"profile_{request.user.id}.{ext}")

        # Uwaga: tu zakładamy pole ImageField na modelu User: user.photo
        # Jeśli zdjęcie jest na user.tinderprofile.photo, dostosuj poniższą linię.
        if hasattr(request.user, "photo"):
            request.user.photo.save(content.name, content, save=True)
        elif hasattr(request.user, "tinderprofile") and hasattr(request.user.tinderprofile, "photo"):
            request.user.tinderprofile.photo.save(content.name, content, save=True)
            request.user.tinderprofile.save(update_fields=["photo"])
        else:
            return Response({"error": "Nie znaleziono pola na zdjęcie u użytkownika"}, status=400)

        photo_url = None
        try:
            if hasattr(request.user, "photo") and request.user.photo:
                photo_url = request.build_absolute_uri(request.user.photo.url)
            elif hasattr(request.user, "tinderprofile") and request.user.tinderprofile.photo:
                photo_url = request.build_absolute_uri(request.user.tinderprofile.photo.url)
        except Exception:
            photo_url = None

        return Response({"success": True, "photo_url": photo_url})
    except Exception as e:
        return Response({"error": f"Błąd podczas przesyłania zdjęcia: {str(e)}"}, status=400)
