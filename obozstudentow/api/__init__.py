from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q

from .group import get_group_signup_info

api_router = routers.SimpleRouter()

from .faq import *

api_router.register(r"faq", FAQViewSet)

from .group import *

api_router.register(r"group", GroupViewSet)
api_router.register(r"groupType", GroupTypeViewSet)

from .people import *

api_router.register(r"contact", ContactViewSet, "contact")
api_router.register(r"myHouseMembers", MyHouseMembers, "myHouseMembers")

from .workshop import *

api_router.register(r"workshop", WorkshopViewSet, "workshop")
api_router.register(
    r"workshopUserSignedUp", WorkshopUserSignedUpViewSet, "workshopUserSignedUp"
)
api_router.register(r"workshopSignUps", WorkshopSignupViewSet, "workshopSignupViewSet")

from .staff.permissions import *

api_router.register(r"permissions", PermissionsViewSet)

from .chat import *

api_router.register(r"chat", MessageViewSet, "chat")
api_router.register(r"chats", ChatViewSet, "chats")

from .houses import *

api_router.register(r"houses", HouseViewSet, "houses")


# home
from ..views import *

from ..models import ScheduleItem


class ScheduleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleItem
        fields = (
            "id",
            "name",
            "description",
            "start",
            "end",
            "location",
            "photo",
            "hide_map",
        )


class ScheduleItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = ScheduleItem.objects.filter(visible=True)
    serializer_class = ScheduleItemSerializer


api_router.register(r"schedule", ScheduleItemViewSet)


from .people import StaffSerializer

from ..models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    addedBy = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()

    def get_addedBy(self, obj):
        return StaffSerializer(
            obj.addedBy, context={"request": self.context["request"]}
        ).data

    def get_group(self, obj):
        return GroupSerializer(
            obj.group, context={"request": self.context["request"]}
        ).data

    class Meta:
        model = Announcement
        fields = ("id", "title", "content", "date", "addedBy", "group", "hide_date")


class AnnouncementViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        return self.queryset.filter(
            Q(group__in=self.request.user.groupmember_set.values("group"))
            | Q(group__in=self.request.user.groupwarden_set.values("group"))
            | Q(group=None),
            Q(hide_date=None) | Q(hide_date__gt=timezone.now()),
            visible=True,
        ).order_by("-date")


api_router.register(r"announcement", AnnouncementViewSet)

from ..models import DailyQuest


class DailyQuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyQuest
        fields = ("id", "title", "description", "points", "finish")


class DailyQuestViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = DailyQuest.objects.all()
    serializer_class = DailyQuestSerializer

    def get_queryset(self):
        return self.queryset.filter(
            Q(group__in=self.request.user.groupmember_set.values("group"))
            | Q(group__in=self.request.user.groupwarden_set.values("group"))
            | Q(group=None),
            Q(start__lte=timezone.now()) | Q(start=None),
            visible=True,
            finish__gte=timezone.now(),
        )


api_router.register(r"dailyQuest", DailyQuestViewSet)

from ..models import Bus


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = "__all__"


class BusViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer


api_router.register(r"bus", BusViewSet)


class GroupWithMembersSerializer(serializers.ModelSerializer):
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
        return ParticipantForAnotherParticipantSerializer(
            User.objects.filter(
                id__in=GroupMember.objects.filter(group=obj).values("user")
            ),
            many=True,
            context=self.context,
        ).data

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "type",
            "logo",
            "map",
            "wardens",
            "members",
            "description",
            "messenger",
        )
        depth = 1


from ..models import Group, SoberDuty, MealDuty


class SoberDutySerializer(serializers.ModelSerializer):
    class Meta:
        model = SoberDuty
        fields = ("start", "end")


from .tinder import TinderProfileSerializer, tinder_register_active
from ..models import TinderProfile


class ProfileSerializer(serializers.ModelSerializer):
    fraction = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    sober_duty = serializers.SerializerMethodField()
    meal_duty = serializers.SerializerMethodField()

    tinder_profile = serializers.SerializerMethodField()

    tinder_register_active = serializers.SerializerMethodField()

    def get_tinder_profile(self, obj):
        return TinderProfileSerializer(
            TinderProfile.objects.filter(user=obj).first(), context=self.context
        ).data

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

    def get_sober_duty(self, obj):
        return SoberDutySerializer(SoberDuty.objects.filter(user=obj), many=True).data

    def get_meal_duty(self, obj):
        return SoberDutySerializer(MealDuty.objects.filter(user=obj), many=True).data

    def get_tinder_register_active(self, obj):
        return tinder_register_active()

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "groups",
            "fraction",
            "bandId",
            "photo",
            "title",
            "bus",
            "diet",
            "house",
            "sober_duty",
            "meal_duty",
            "notifications",
            "tinder_profile",
            "tinder_register_active",
        )
        depth = 1


class ProfileViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)


api_router.register(r"profile", ProfileViewSet)


from ..models import Link


class LinkSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(source="icon.icon")

    class Meta:
        model = Link
        fields = ("id", "name", "url", "icon")


class LinkViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Link.objects.order_by("sort_order")
    serializer_class = LinkSerializer


api_router.register(r"link", LinkViewSet)


from ..models import HomeLink


class HomeLinkSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(source="icon.icon", required=False)

    class Meta:
        model = HomeLink
        fields = ("id", "name", "url", "icon", "image", "font_size")


class HomeLinkViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = HomeLink.objects.filter(visible=True).order_by("sort_order")
    serializer_class = HomeLinkSerializer


api_router.register(r"home-link", HomeLinkViewSet)


from ..models import Image


class ImageSerializer(serializers.ModelSerializer):
    downloadLink = serializers.SerializerMethodField()

    def get_downloadLink(self, obj):
        return "/download-image/" + str(obj.id) + "/"

    class Meta:
        model = Image
        fields = ("id", "name", "image", "downloadLink")


class ImageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Image.objects.filter(visible=True)
    serializer_class = ImageSerializer


api_router.register(r"image", ImageViewSet)


from ..models import Partners


class PartnersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partners
        fields = "__all__"


class PartnersViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Partners.objects.order_by("sort_order")
    serializer_class = PartnersSerializer


api_router.register(r"partners", PartnersViewSet)
