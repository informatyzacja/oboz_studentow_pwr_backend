from rest_framework import serializers, routers, viewsets
from django.db.models import Q

from ..models import Group, GroupMember, GroupWarden, GroupType
class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'type', 'logo', 'groupwarden_set')
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


