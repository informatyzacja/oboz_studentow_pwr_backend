from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required

from ..models import UserFCMToken

@api_view(['POST'])
def register_fcm_token(request):
    token = request.data.get('token')
    if token is None:
        return Response({'success':False, 'error': 'Nie podano tokenu'})
    
    UserFCMToken.objects.filter(token=token).delete()
    UserFCMToken.objects.create(user=request.user, token=token)

    return Response({'success': True})