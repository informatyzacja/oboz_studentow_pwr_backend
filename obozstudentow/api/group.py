from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q

from ..models import Group, GroupMember, GroupWarden, GroupType, UserFCMToken

from .notifications import send_notification

from .people import StaffSerializer
from ..models import User

from django.utils import timezone

from django.db import transaction

from .people import ParticipantForAnotherParticipantSerializer


class GroupSerializer(serializers.ModelSerializer):
    wardens = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    def get_wardens(self, obj):
        return StaffSerializer(
            User.objects.filter(
                id__in=GroupWarden.objects.filter(group=obj).values("user")
            ),
            many=True,
            context=self.context,
        ).data

    def get_members(self, obj):
        if self.context["request"].user.groupwarden_set.filter(group=obj).exists():
            return ParticipantForAnotherParticipantSerializer(
                User.objects.filter(
                    id__in=GroupMember.objects.filter(group=obj).values("user")
                ),
                many=True,
                context=self.context,
            ).data
        return None

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "type",
            "logo",
            "map",
            "wardens",
            "description",
            "messenger",
            "background",
            "members",
        )
        depth = 1


class GroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupType
        fields = ("id", "name")


class GroupTypeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


from ..models import Setting
from rest_framework.decorators import api_view
from rest_framework.response import Response


def night_game_signup_active():
    active = (
        Setting.objects.get(name="night_game_signup_active").value.lower() == "true"
    )
    if active and Setting.objects.get(name="night_game_signup_start_datetime").value:
        active = (
            timezone.datetime.strptime(
                Setting.objects.get(name="night_game_signup_start_datetime").value,
                "%Y-%m-%d %H:%M",
            )
            <= timezone.now()
        )

    return active


@api_view(["GET"])
def get_group_signup_info(request):
    free_places = Group.objects.filter(~Q(type__name="Frakcja")).count() < int(
        Setting.objects.get(name="group_limit").value
    )
    group_user_min = int(Setting.objects.get(name="group_user_min").value)
    group_user_max = int(Setting.objects.get(name="group_user_max").value)
    user_in_group = (
        GroupMember.objects.filter(user=request.user)
        .filter(~Q(group__type__name="Frakcja"))
        .exists()
    )
    night_game_date = Setting.objects.get(name="night_game_date").value
    night_game_signup_start_datetime = Setting.objects.get(
        name="night_game_signup_start_datetime"
    ).value

    return Response(
        {
            "free_places": free_places,
            "group_user_min": group_user_min,
            "group_user_max": group_user_max,
            "user_in_group": user_in_group,
            "night_game_date": night_game_date,
            "night_game_signup_active": night_game_signup_active(),
            "night_game_signup_start_datetime": night_game_signup_start_datetime,
        }
    )


from ..models import NightGameSignup


@api_view(["POST"])
def signup_group(request):
    with transaction.atomic():
        free_places = Group.objects.filter(~Q(type__name="Frakcja")).count() < int(
            Setting.objects.get(name="group_limit").value
        )
        if not free_places:
            return Response(
                {"success": False, "error": "Brak wolnych miejsc", "error_code": 1}
            )

        if not night_game_signup_active():
            return Response(
                {"success": False, "error": "Zapisy nieaktywne", "error_code": 10}
            )

        if not "group_name" in request.data:
            return Response(
                {"success": False, "error": "Brak nazwy grupy", "error_code": 2}
            )

        if not "people" in request.data:
            return Response(
                {"success": False, "error": "Brak listy osób", "error_code": 3}
            )

        if len(request.data["people"]) + 1 < int(
            Setting.objects.get(name="group_user_min").value
        ):
            return Response(
                {"success": False, "error": "Za mało osób w grupie", "error_code": 4}
            )

        if len(request.data["people"]) + 1 > int(
            Setting.objects.get(name="group_user_max").value
        ):
            return Response(
                {"success": False, "error": "Za dużo osób w grupie", "error_code": 5}
            )

        if NightGameSignup.objects.filter(addedBy=request.user).exists():
            return Response(
                {
                    "success": False,
                    "error": "Już zapisałeś grupę na grę nocną",
                    "error_code": 6,
                }
            )

        group_name = request.data["group_name"]
        group_type = GroupType.objects.get(name="Gra nocna")

        if Group.objects.filter(name=group_name, type=group_type).exists():
            return Response(
                {
                    "success": False,
                    "error": "Grupa o tej nazwie już istnieje",
                    "error_code": 7,
                }
            )

        group = Group.objects.create(name=group_name, type=group_type)
        group.save()

        night_game_start = timezone.datetime.strptime(
            Setting.objects.get(name="night_game_date").value, "%Y-%m-%d"
        )

        # user making request
        nightGameSignup = NightGameSignup.objects.create(
            user_band=request.user.bandId.zfill(6),
            user_first_name=request.user.first_name,
            group=group,
            addedBy=request.user,
        )

        if request.user.birthDate and (
            night_game_start.year
            - request.user.birthDate.year
            - (
                (night_game_start.month, night_game_start.day)
                < (request.user.birthDate.month, request.user.birthDate.day)
            )
            < 18
        ):
            nightGameSignup.failed = True
            nightGameSignup.error = "Użytkownik nie jest pełnoletni"
            nightGameSignup.save()
            group.delete()
            userError = f"Użytkownik {request.user.first_name} nie jest pełnoletni"
            return Response({"success": False, "error": userError, "error_code": 9})

        elif GroupMember.objects.filter(
            user=request.user, group__type=group_type
        ).exists():
            nightGameSignup.failed = True
            nightGameSignup.error = "Użytkownik jest już w jakiejś grupie"
            nightGameSignup.save()
            group.delete()
            return Response(
                {
                    "success": False,
                    "error": f"Użytkownik {request.user.first_name} jest już w jakiejś grupie",
                    "error_code": 8,
                }
            )
        else:
            GroupMember.objects.create(user=request.user, group=group).save()

        nightGameSignup.save()

        # other people
        for person in request.data["people"]:
            nightGameSignup = NightGameSignup.objects.create(
                user_band=person["band"],
                # user_first_name = person['first_name'],
                group=group,
                addedBy=request.user,
            )
            userError = ""

            if User.objects.filter(bandId=person["band"].zfill(6)).exists():
                user = User.objects.get(bandId=person["band"].zfill(6))

                if user.birthDate and (
                    night_game_start.year
                    - user.birthDate.year
                    - (
                        (night_game_start.month, night_game_start.day)
                        < (user.birthDate.month, user.birthDate.day)
                    )
                    < 18
                ):
                    nightGameSignup.failed = True
                    nightGameSignup.error = "Użytkownik nie jest pełnoletni"
                    userError = f"Użytkownik {user.first_name} nie jest pełnoletni"

                elif GroupMember.objects.filter(
                    user=user, group__type=group_type
                ).exists():
                    nightGameSignup.failed = True
                    nightGameSignup.error = "Użytkownik jest już w jakiejś grupie"
                    userError = (
                        f"Użytkownik {user.first_name} jest już w jakiejś grupie"
                    )

                else:
                    GroupMember.objects.create(user=user, group=group).save()

            # elif User.objects.filter(bandId=person['band'].zfill(6)).exists():
            #     user = User.objects.get(bandId=person['band'].zfill(6))
            #     nightGameSignup.failed = True
            #     nightGameSignup.error = f"Nie znaleziono użytkownika o podanym imieniu. Znaleziony użytkownik to: {user.first_name} {user.last_name}, ID: {user.pk}, opaska: {user.bandId if user.bandId else 'brak numeru opaski'}"
            #     userError = f"Nie znaleziono użytkownika o podanych danych: {person['first_name'].strip()}, opaska: {person['band']}"

            else:
                nightGameSignup.failed = True
                nightGameSignup.error = f"Nie znaleziono użytkownika o podanej opasce."
                userError = (
                    f"Nie znaleziono użytkownika o podanej opasce: {person['band']}"
                )

            nightGameSignup.save()
            if nightGameSignup.failed:
                group.delete()
                return Response({"success": False, "error": userError, "error_code": 9})

        # send notifications
        try:
            tokens = list(
                UserFCMToken.objects.filter(
                    user__notifications=True,
                    user__in=GroupMember.objects.filter(group=group).values_list(
                        "user", flat=True
                    ),
                ).values_list("token", flat=True)
            )

            title = f"Zostałeś/aś zapisany/a na grę nocną."
            content = f'Grupę "{group.name}" i jej członków możesz zobaczyć w zakładce "Profil"'
            # absolute_url = request.build_absolute_uri("/app/profil")

            send_notification.delay(title, content, tokens)
        except:
            pass

        return Response({"success": True})
