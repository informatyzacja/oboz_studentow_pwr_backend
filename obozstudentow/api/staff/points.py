from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required
from rest_framework import serializers

from ...models import Point, PointType, GroupType, Group
from .. import StaffSerializer, GroupSerializer, GroupTypeSerializer

from django.utils import timezone


class PointsSerializer(serializers.ModelSerializer):
    addedBy = serializers.SerializerMethodField()
    validatedBy = serializers.SerializerMethodField()

    def get_addedBy(self, obj):
        return StaffSerializer(obj.addedBy).data
    
    def get_validatedBy(self, obj):
        return StaffSerializer(obj.validatedBy).data

    class Meta:
        model = Point
        fields = ('id','description','date','numberOfPoints','group','type','addedBy', 'validated', 'rejected', 'validatedBy', 'validationDate')
        depth = 2

@api_view(['GET'])
@permission_required('obozstudentow.can_view_points')
def get_points(request):
    return Response(PointsSerializer(Point.objects.order_by('date'), many=True).data)

@api_view(['PUT'])
@permission_required('obozstudentow.can_validate_points')
def validate_points(request, id):
    if not Point.objects.filter(id=id).exists():
        return Response({'success': False, 'error': 'Nie znaleziono punktów o podanym id'})
    point = Point.objects.get(id=id)
    point.validated = True
    point.validatedBy = request.user
    point.validationDate = timezone.now()
    point.rejected = False
    point.save()
    return Response({'success': True})

@api_view(['PUT'])
@permission_required('obozstudentow.can_validate_points')
def reject_points(request, id):
    if not Point.objects.filter(id=id).exists():
        return Response({'success': False, 'error': 'Nie znaleziono punktów o podanym id'})
    point = Point.objects.get(id=id)
    point.validated = False
    point.validatedBy = request.user
    point.validationDate = timezone.now()
    point.rejected = True
    point.save()
    return Response({'success': True})

class PointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointType
        fields = '__all__'
        depth = 1

@api_view(['GET'])
@permission_required('obozstudentow.can_add_points')
def get_point_types(request):
    groupTypes = GroupType.objects.all()
    pointTypes = PointType.objects.all()
    groups = Group.objects.all()
    return Response({
        'groupTypes': GroupTypeSerializer(groupTypes, many=True).data,
        'pointTypes': PointTypeSerializer(pointTypes, many=True).data,
        'groups': GroupSerializer(groups, many=True, context={'request':request}).data
    })

@api_view(['POST'])
@permission_required('obozstudentow.can_add_points')
def add_points(request):
    if not request.data['group'] or not request.data['type'] or not request.data['numberOfPoints']:
        return Response({'success': False, 'error': 'Nie podano wszystkich wymaganych danych'})
    if not Group.objects.filter(id=request.data['group']).exists():
        return Response({'success': False, 'error': 'Nie znaleziono grupy o podanym id'})
    if not PointType.objects.filter(id=request.data['type']).exists():
        return Response({'success': False, 'error': 'Nie znaleziono typu punktów o podanym id'})
    point = Point()
    point.group = Group.objects.get(id=request.data['group'])
    point.type = PointType.objects.get(id=request.data['type'])
    point.numberOfPoints = request.data['numberOfPoints']
    point.description = request.data['description']
    point.addedBy = request.user
    point.save()
    return Response({'success': True})