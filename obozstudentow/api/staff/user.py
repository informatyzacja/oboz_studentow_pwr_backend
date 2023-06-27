from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required


from ...models import User, Group
from .. import ProfileSerializer, GroupSerializer, GroupWithMembersSerializer

from django.urls import path


@api_view(['GET'])
@permission_required('obozstudentow.can_view_user_info')
def get_user_info(request):
    user_id = request.GET.get('user_id')
    if user_id is None:
        return Response({'error': 'Nie podano ID użytkownika'})
    try:
        user = User.objects.get(id=user_id)
        return Response(ProfileSerializer(user, context={'request': request}).data)
    except User.DoesNotExist:
        return Response({'error': 'Użytkownik nie istnieje'})

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