from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q


from django.contrib.auth.models import Permission
from rest_framework.response import Response

# from ...models import CustomPermissions
class PermissionsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Permission
        fields = ('name','codename')

class PermissionsViewSet( viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    def list(self, request):
        queryset = request.user.groups.first().permissions.all()
        serializer = PermissionsSerializer(queryset, many=True)
        return Response(serializer.data)


