from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required


from ...models import User, GroupType, GroupMember, House

from rest_framework import serializers

from ...api.group import GroupSerializer, Group
from ...api import GroupWithMembersSerializer

from django.db.models import Q


class ParticipantInfoSerializer(serializers.ModelSerializer):
    fraction = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    def get_fraction(self, obj):
        return GroupSerializer(
            Group.objects.filter(
                Q(groupmember__user=obj) | Q(groupwarden__user=obj),
                type__name="Frakcja",
            ).first(),
            context=self.context,
        ).data

    def get_groups(self, obj):
        return GroupWithMembersSerializer(
            Group.objects.filter(
                Q(groupmember__user=obj) | Q(groupwarden__user=obj),
                ~Q(type__name="Frakcja"),
            ),
            context=self.context,
            many=True,
        ).data

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "groups",
            "fraction",
            "bandId",
            "photo",
            "title",
            "bus",
            "house",
            "phoneNumber",
            "diet",
        )
        depth = 1


@api_view(["GET"])
@permission_required("obozstudentow.can_view_user_info")
def get_user_info(request):
    user_id = request.GET.get("user_id")
    if user_id is None:
        return Response({"success": False, "error": "Nie podano ID użytkownika"})
    try:
        user = User.objects.get(bandId=user_id.zfill(6))
        return Response(
            ParticipantInfoSerializer(user, context={"request": request}).data
        )
    except User.DoesNotExist:
        return Response({"success": False, "error": "Użytkownik nie istnieje"})


class ParticipantConfidentialInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "birthDate",
            "gender",
            "ice_number",
            "additional_health_info",
            "pesel",
        )
        depth = 1


@api_view(["GET"])
@permission_required("obozstudentow.can_view_confidential_user_info")
def get_user_confidential_info(request):
    user_id = request.GET.get("user_id")
    if user_id is None:
        return Response({"success": False, "error": "Nie podano ID użytkownika"})
    try:
        user = User.objects.get(bandId=user_id.zfill(6))
        return Response(
            ParticipantConfidentialInfoSerializer(
                user, context={"request": request}
            ).data
        )
    except User.DoesNotExist:
        return Response({"success": False, "error": "Użytkownik nie istnieje"})


class HouseInfoSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    def get_members(self, obj):
        return ParticipantInfoSerializer(
            User.objects.filter(house=obj), many=True, context=self.context
        ).data

    class Meta:
        model = House
        fields = ("id", "name", "key_collected", "user_key_collected", "members")
        depth = 1


@api_view(["GET"])
@permission_required("obozstudentow.can_view_user_info")
def get_house_info(request):
    house_id = request.GET.get("house_id")
    if house_id is None:
        return Response({"success": False, "error": "Nie podano ID domku"})
    try:
        house = House.objects.get(pk=house_id)
        return Response(HouseInfoSerializer(house, context={"request": request}).data)
    except House.DoesNotExist:
        return Response({"success": False, "error": "Dom nie istnieje"})


@api_view(["GET"])
@permission_required("obozstudentow.can_add_points")
def get_user_group(request):
    user_id = request.GET.get("user_id")
    group_type = request.GET.get("group_type")
    if user_id is None:
        return Response({"success": False, "error": "Nie podano ID użytkownika"})
    if group_type is None:
        return Response({"success": False, "error": "Nie podano typu grupy"})
    try:
        group_member = GroupMember.objects.get(
            user=User.objects.get(bandId=user_id.zfill(6)), group__type__name=group_type
        )
        return Response({"success": True, "group": group_member.group.pk})
    except GroupMember.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Użytkownik nie należy do żadnej grupy o podanym typie",
            }
        )
    except User.DoesNotExist:
        return Response({"success": False, "error": "Nie znaleziono użytkownika"})


class StaffContactSerializer(serializers.ModelSerializer):
    note = serializers.SerializerMethodField()

    def get_note(self, obj):
        note = ""

        if obj.groupwarden_set.exists():
            note += (
                "Frakcja: "
                + ", ".join(
                    [
                        group_warden.group.name
                        for group_warden in obj.groupwarden_set.all()
                    ]
                )
                + "\n"
            )

        if obj.workshopleader_set.exists():
            note += (
                "Warsztaty: "
                + ", ".join(
                    [
                        workshop_leader.workshop.name
                        for workshop_leader in obj.workshopleader_set.all()
                    ]
                )
                + "\n"
            )

        return note or None

    phone = serializers.CharField(source="phoneNumber")

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "phone", "photo", "title", "note")


@api_view(["GET"])
@permission_required("obozstudentow.can_get_contacts")
def get_contacts(request):
    return Response(
        StaffContactSerializer(
            User.objects.filter(groups__isnull=False, phoneNumber__isnull=False)
            .exclude(id=request.user.id)
            .exclude(first_name__icontains="test")
            .exclude(last_name__icontains="test")
            .distinct(),
            many=True,
            context={"request": request},
        ).data
    )


from django.db.models import Count, F


@api_view(["GET"])
@permission_required("obozstudentow.can_change_bands")
def get_user_list(request):
    return Response(
        User.objects.annotate(
            bandId_isnull=Count("bandId"),
        )
        .order_by("bandId_isnull", "last_name", "first_name")
        .values(
            "id", "first_name", "last_name", "phoneNumber", "bandId", "bus_info", "bus"
        )
    )
