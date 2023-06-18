from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q


from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import Group as DjangoGroup

# from ...models import CustomPermissions
class PermissionsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Permission
        fields = ('name','codename')

class PermissionsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.filter(content_type__model='custompermissions')
    serializer_class = PermissionsSerializer


