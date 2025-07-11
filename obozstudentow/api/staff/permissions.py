from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q


from django.contrib.auth.models import Permission
from rest_framework.response import Response


# from ...models import CustomPermissions
class PermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("name", "codename")


class PermissionsViewSet(viewsets.GenericViewSet):
    queryset = Permission.objects.all()

    def list(self, request):
        queryset = request.user.user_permissions.all() | Permission.objects.filter(
            group__user=request.user
        )
        serializer_data = PermissionsSerializer(queryset, many=True).data
        if request.user.is_staff:
            serializer_data.append({"name": "Is staff", "codename": "is_staff"})
        return Response(serializer_data)
