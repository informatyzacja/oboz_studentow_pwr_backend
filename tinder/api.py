from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import serializers

import base64

from django.core.files.base import ContentFile
from django.utils import timezone

from obozstudentow.models import Setting, User
from tinder.models import TinderProfile, TinderAction
from obozstudentow_async.models import Chat
from obozstudentow.api.notifications import send_notification, UserFCMToken
import random


def tinder_register_active():
    active = Setting.objects.get(name="tinder_register_active").value.lower() == "true"
    if active and Setting.objects.get(name="tinder_register_activate_datetime").value:
        active = (
            timezone.datetime.strptime(
                Setting.objects.get(name="tinder_register_activate_datetime").value,
                "%Y-%m-%d %H:%M",
            )
            <= timezone.now()
        )

    return active


class TinderProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.first_name")

    class Meta:
        model = TinderProfile
        fields = "__all__"


def tinder_active():
    active = Setting.objects.get(name="tinder_swiping_active").value.lower() == "true"
    if active and Setting.objects.get(name="tinder_swiping_activate_datetime").value:
        active = (
            timezone.datetime.strptime(
                Setting.objects.get(name="tinder_swiping_activate_datetime").value,
                "%Y-%m-%d %H:%M",
            )
            <= timezone.now()
        )

    return active


@api_view(["POST"])
def uploadProfilePhoto(request):
    # Komentuję to bo ten endpoint jest też używany do dodawania zdjęć profilowych na BeerReal
    # if not tinder_register_active():
    #     return Response(
    #         {"error": "Rejestracja na Tinder jest obecnie wyłączona"}, status=400
    #     )

    profile = TinderProfile.objects.get_or_create(user=request.user)[0]

    photoBase64String = request.data.get("photo")

    if not photoBase64String:
        return Response({"error": "Brak zdjęcia"}, status=400)

    format, imgstr = photoBase64String.split(";base64,")
    ext = format.split("/")[-1]

    profile.photo.save(
        f"{request.user.id}.{ext}", ContentFile(base64.b64decode(imgstr)), save=True
    )

    return Response(
        {
            "success": True,
            "tinder_profile": TinderProfileSerializer(
                profile, context={"request": request}
            ).data,
        }
    )


@api_view(["POST"])
def uploadProfileData(request):
    if not tinder_register_active():
        return Response(
            {"error": "Rejestracja na Tinder jest obecnie wyłączona"}, status=400
        )

    profile = TinderProfile.objects.get_or_create(user=request.user)[0]

    if description := request.data.get("description"):
        profile.description = description

    profile.save()

    return Response(
        {
            "tinder_profile": TinderProfileSerializer(
                profile, context={"request": request}
            ).data
        }
    )


@api_view(["GET"])
def loadTinderProfiles(request):
    if not tinder_active():
        return Response(
            {"info": "Przeglądanie profili jest obecnie wyłączone"}, status=200
        )

    user = request.user

    if not TinderProfile.objects.filter(user=user).exists():
        return Response({"error": "Brak profilu"}, status=400)

    if user.tinderprofile.blocked:
        return Response({"error": "Zostałeś/aś zablokowany/a"}, status=400)

    exclude_user_ids = request.GET.get("skip_ids", "").split(",")
    exclude_user_ids = [int(id) for id in exclude_user_ids if id]

    profiles = (
        TinderProfile.objects.exclude(user=user)
        .exclude(user__tinderprofile__blocked=True)
        .exclude(user__tinderaction_target__user=user)
        .exclude(user__id__in=exclude_user_ids)
        .order_by("?")[:10]
    )

    serializer = TinderProfileSerializer(
        profiles, context={"request": request}, many=True
    )
    data = serializer.data

    # demo id randomization (kept from legacy implementation)
    import random

    for profile in data:
        profile["id"] = random.randint(1, 100000)

    return Response(data)


@api_view(["POST"])
def tinderAction(request):
    if not tinder_active():
        return Response({"error": "Funkcja swipingu jest wyłączona"}, status=400)

    user = request.user

    if not TinderProfile.objects.filter(user=user).exists():
        return Response({"error": "Brak profilu"}, status=400)

    if user.tinderprofile.blocked:
        return Response({"error": "Zostałeś/aś zablokowany/a"}, status=400)

    try:
        target = User.objects.get(id=request.data.get("target"))
    except User.DoesNotExist:
        return Response({"error": "Niepoprawny użytkownik"}, status=400)

    if target == user:
        return Response({"error": "Nie możesz oceniać siebie"}, status=400)

    action = request.data.get("action")

    tinderaction = TinderAction.objects.get_or_create(
        user=user, target=target, defaults={"action": 0}
    )[0]

    if action == "like":
        tinderaction.action = 1
    elif action == "dislike":
        tinderaction.action = 0
    elif action == "superlike":
        if not user.tinderprofile.super_like_used:
            user.tinderprofile.super_like_used = True
            user.tinderprofile.save()
        else:
            return Response({"error": "Już użyłeś/aś superlajka."}, status=400)
        tinderaction.action = 2
    else:
        return Response({"error": "Niepoprawna akcja"}, status=400)

    tinderaction.save()

    match = (
        tinderaction.action == 1
        and TinderAction.objects.filter(
            user=target, target=user, action__in=[1, 2]
        ).exists()
    ) or tinderaction.action == 2

    chat = None
    if match:
        chat = (
            Chat.objects.filter(name__startswith="tinder")
            .filter(users=user)
            .filter(users=target)
            .first()
        )
        if not chat:
            chat = Chat.objects.create(name=f"tinder ({user}, {target})")
            chat.users.add(user, target)

        if target.notifications:
            tokens = list(
                UserFCMToken.objects.filter(
                    user=target, user__notifications=True
                ).values_list("token", flat=True)
            )
            body_templates = [
                "Masz nowy match z {name}!",
                "Match! Ty i {name} polubiliście się.",
                "🔥 Iskra jest – rozpocznij rozmowę z {name}.",
                "To jest match! Przywitaj się z {name}.",
                "Wpadliście sobie w oko: Ty i {name}.",
            ]
            body = random.choice(body_templates).format(name=user.first_name)
            send_notification.delay(
                "It's a match!",
                body,
                tokens,
                link=f"/czat/{chat.id}",
            )

    return Response(
        {"success": True, "match": match, "chat_id": chat.id if match else None}
    )
