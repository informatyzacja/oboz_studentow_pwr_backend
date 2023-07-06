from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required


from ...models import Group
from .. import GroupSerializer, GroupWithMembersSerializer

from django.db.models import Q


@api_view(['GET'])
@permission_required('obozstudentow.can_view_fractions')
def get_fraction(request):
    group_id = request.GET.get('group_id')
    if group_id is None:
        return Response({'error': 'Nie podano ID frakcji'})
    try:
        group = Group.objects.get(id=group_id)
        return Response(GroupSerializer(group, context={'request': request}).data)
    except Group.DoesNotExist:
        return Response({'error': 'Frakcja nie istnieje'})
    
@api_view(['GET'])
@permission_required('obozstudentow.can_view_groups')
def get_group(request):
    group_id = request.GET.get('group_id')
    if group_id is None:
        return Response({'error': 'Nie podano ID grupy'})
    try:
        group = Group.objects.get(id=group_id)
        return Response(GroupWithMembersSerializer(group, context={'request': request}).data)
    except Group.DoesNotExist:
        return Response({'error': 'Grupa nie istnieje'})
    
@api_view(['GET'])
@permission_required('obozstudentow.can_view_groups')
def get_groups(request):
    return Response(GroupSerializer(Group.objects.filter(~Q(type__name="Frakcja")), context={'request': request}, many=True).data)

@api_view(['GET'])
@permission_required('obozstudentow.can_view_fractions')
def get_fractions(request):
    return Response(GroupSerializer(Group.objects.filter(type__name="Frakcja"), context={'request': request}, many=True).data)


