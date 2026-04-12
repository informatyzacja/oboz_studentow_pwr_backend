from rest_framework import serializers, viewsets, mixins
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response

from ..models import SoberDuty, LifeGuard, Staff, User, Group


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "phoneNumber", "photo", "title")


class ParticipantForAnotherParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name")


class ParticipantForStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "phoneNumber", "title")


class ContactViewSet(viewsets.GenericViewSet):
    def list(self, request):
        from .camps import get_camp_from_request

        camp = get_camp_from_request(request)
        frakcja = Group.objects.filter(
            Q(groupmember__user=request.user) | Q(groupwarden__user=request.user),
            type__name="Frakcja",
        )
        if camp is not None:
            frakcja = frakcja.filter(camp=camp)
        frakcja = frakcja.first()

        staff_qs = Staff.objects.all().order_by("sort_order")
        lifeguard_qs = LifeGuard.objects.all()
        soberduty_qs = SoberDuty.objects.filter(
            start__lte=timezone.now(), end__gte=timezone.now()
        )
        if camp is not None:
            staff_qs = staff_qs.filter(camp=camp)
            lifeguard_qs = lifeguard_qs.filter(camp=camp)
            soberduty_qs = soberduty_qs.filter(camp=camp)

        return Response(
            {
                "staff": StaffSerializer(
                    [x.user for x in staff_qs],
                    many=True,
                    context=self.get_serializer_context(),
                ).data,
                "lifeGuard": StaffSerializer(
                    User.objects.filter(id__in=lifeguard_qs.values("user")),
                    many=True,
                    context=self.get_serializer_context(),
                ).data,
                "currentSoberDuty": StaffSerializer(
                    User.objects.filter(id__in=soberduty_qs.values("user")),
                    many=True,
                    context=self.get_serializer_context(),
                ).data,
                "fractionWardens": StaffSerializer(
                    User.objects.filter(
                        id__in=frakcja.groupwarden_set.all().values("user")
                    ),
                    many=True,
                    context=self.get_serializer_context(),
                ).data
                if frakcja
                else [],
            }
        )


class MyHouseMembers(viewsets.GenericViewSet):
    def list(self, request):
        return Response(
            ParticipantForAnotherParticipantSerializer(
                User.objects.filter(house=request.user.house),
                many=True,
                context=self.get_serializer_context(),
            ).data
        )
