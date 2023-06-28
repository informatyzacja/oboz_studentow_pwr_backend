from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required
from rest_framework import serializers

from ...models import Point, PointType
from .. import PersonSerializer


class PointsSerializer(serializers.ModelSerializer):
    addedBy = serializers.SerializerMethodField()
    validatedBy = serializers.SerializerMethodField()

    def get_addedBy(self, obj):
        return PersonSerializer(obj.addedBy).data
    
    def get_validatedBy(self, obj):
        return PersonSerializer(obj.validatedBy).data

    class Meta:
        model = Point
        fields = ('id','description','date','numberOfPoints','group','type','addedBy', 'validated', 'validatedBy', 'validationDate')
        depth = 2

@api_view(['GET'])
@permission_required('obozstudentow.can_view_points')
def get_points(request):
    return Response(PointsSerializer(Point.objects.all(), many=True).data)