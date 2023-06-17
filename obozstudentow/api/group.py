from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q

from ..models import Group, GroupMember, GroupWarden, GroupType


from .people import PersonSerializer
from ..models import User
class GroupSerializer(serializers.HyperlinkedModelSerializer):
    wardens = serializers.SerializerMethodField()

    def get_wardens(self, obj):
        return PersonSerializer( User.objects.filter(id__in=GroupWarden.objects.filter(group=obj).values('user')), many=True, context=self.context ).data

    class Meta:
        model = Group
        fields = ('id', 'name', 'type', 'logo', 'map', 'wardens', 'description', 'messenger')
        depth = 1

class GroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupType
        fields = ('id', 'name')

class GroupTypeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer



class GroupWardeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupWarden
        fields = ('id', 'group', 'user')

class GroupWardenViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = GroupWarden.objects.all()
    serializer_class = GroupWardeSerializer



class GroupMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'user')

class GroupMemberViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer


