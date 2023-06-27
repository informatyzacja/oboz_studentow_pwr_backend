from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required


from ...models import User
from .. import ProfileSerializer



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
