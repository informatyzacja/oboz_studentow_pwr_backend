from rest_framework import serializers, routers, viewsets
from django.db.models import Q

api_router = routers.DefaultRouter()

from .faq import *
api_router.register(r'faq', FAQViewSet)

from .group import *
api_router.register(r'group', GroupViewSet)
api_router.register(r'groupType', GroupTypeViewSet)
api_router.register(r'groupWarden', GroupWardenViewSet)
api_router.register(r'groupMember', GroupMemberViewSet)

from .people import *
# api_router.register(r'lifeGuard', LifeGuardViewSet)
# api_router.register(r'currentSoberDuty', CurrentSoberDutyViewSet)
api_router.register(r'contact', ContactViewSet, 'contact')
# api_router.register(r'person', PersonViewSet)

from .workshop import *
api_router.register(r'workshop', WorkshopViewSet, 'workshop')
api_router.register(r'workshopUserSignedUp', WorkshopUserSignedUpViewSet, 'workshopUserSignedUp')
api_router.register(r'workshopSignUps', WorkshopSignupViewSet, 'workshopSignupViewSet')
# api_router.register(r'workshopLeader', WorkshopLeaderViewSet, 'workshopLeader')


#home

from ..models import ScheduleItem
class ScheduleItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ScheduleItem
        fields = ('id', 'name', 'description', 'start', 'end', 'location', 'photo')

class ScheduleItemViewSet(viewsets.ModelViewSet):
    queryset = ScheduleItem.objects.filter(visible=True)
    serializer_class = ScheduleItemSerializer

api_router.register(r'schedule', ScheduleItemViewSet)




from ..models import Announcement
class AnnouncementSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Announcement
        fields = ('id', 'title', 'content', 'date', 'addedBy')

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        return self.queryset.filter(
            Q(group__in=self.request.user.groupmember_set.values('group')) | 
            Q(group__in=self.request.user.groupwarden_set.values('group')) | 
            Q(group=None), 
            visible=True
        )
    
api_router.register(r'announcement', AnnouncementViewSet)

from ..models import DailyQuest
class DailyQuestSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DailyQuest
        fields = ('id', 'content', 'finish', 'addedBy')

class DailyQuestViewSet(viewsets.ModelViewSet):
    queryset = DailyQuest.objects.all()
    serializer_class = DailyQuestSerializer

    def get_queryset(self):
        return self.queryset.filter(
            Q(group__in=self.request.user.groupmember_set.values('group')) | 
            Q(group__in=self.request.user.groupwarden_set.values('group')) | 
            Q(group=None), 
            visible=True
        )
    
api_router.register(r'dailyQuest', DailyQuestViewSet)

from ..models import Bus
class BusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Bus
        fields = "__all__"

class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

api_router.register(r'bus', BusViewSet)



class GroupWithMembersSerializer(serializers.HyperlinkedModelSerializer):
    wardens = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    def get_wardens(self, obj):
        return PersonSerializer( User.objects.filter(id__in=GroupWarden.objects.filter(group=obj).values('user')), many=True, context=self.context ).data
    
    def get_members(self, obj):
        return PersonSerializer( User.objects.filter(id__in=GroupMember.objects.filter(group=obj).values('user')), many=True, context=self.context ).data

    class Meta:
        model = Group
        fields = ('id', 'name', 'type', 'logo', 'map', 'wardens', 'members', 'description', 'messenger')
        depth = 1

from ..models import Group

class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    fraction = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    def get_fraction(self, obj):
        return GroupSerializer( Group.objects.filter(Q(groupmember__user=obj) | Q(groupwarden__user=obj), type__name="Frakcja").first(), context=self.context ).data
    
    def get_groups(self, obj):
        return GroupWithMembersSerializer( Group.objects.filter(Q(groupmember__user=obj) | Q(groupwarden__user=obj), ~Q(type__name="Frakcja")), context=self.context, many=True ).data


    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'groups', 'fraction', 'bandId', 'houseNumber', 'photo', 'title', 'bus')
        depth = 1

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.request.user.id)
    
api_router.register(r'profile', ProfileViewSet)






from ..models import Link
class LinkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Link
        fields = "__all__"

class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer

api_router.register(r'link', LinkViewSet)