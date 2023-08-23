from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required


from ...models import User, GroupType, GroupMember
from .. import ProfileSerializer



@api_view(['GET'])
@permission_required('obozstudentow.can_view_user_info')
def get_user_info(request):
    user_id = request.GET.get('user_id')
    if user_id is None:
        return Response({'success':False, 'error': 'Nie podano ID użytkownika'})
    try:
        user = User.objects.get(bandId=user_id.zfill(6))
        return Response(ProfileSerializer(user, context={'request': request}).data)
    except User.DoesNotExist:
        return Response({'success':False, 'error': 'Użytkownik nie istnieje'})

@api_view(['GET'])
@permission_required('obozstudentow.can_add_points')
def get_user_group(request):
    user_id = request.GET.get('user_id')
    group_type= request.GET.get('group_type')
    if user_id is None:
        return Response({'success':False, 'error': 'Nie podano ID użytkownika'})
    if group_type is None:
        return Response({'success':False, 'error': 'Nie podano typu grupy'})
    try:
        group_member = GroupMember.objects.get(user=User.objects.get(bandId=user_id.zfill(6)), group__type__name=group_type)
        return Response({'success':True, 'group': group_member.group.pk})
    except GroupMember.DoesNotExist:
        return Response({'success':False, 'error': 'Użytkownik nie należy do żadnej grupy o podanym typie'})
    except User.DoesNotExist:
        return Response({'success':False, 'error': 'Nie znaleziono użytkownika'})