from rest_framework import serializers, routers, viewsets
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

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupType
        fields = ('id', 'name')

class GroupTypeViewSet(viewsets.ModelViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer



class GroupWardeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupWarden
        fields = ('id', 'group', 'user')

class GroupWardenViewSet(viewsets.ModelViewSet):
    queryset = GroupWarden.objects.all()
    serializer_class = GroupWardeSerializer



class GroupMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupMember
        fields = ('id', 'group', 'user')

class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.all()
    serializer_class = GroupMemberSerializer


