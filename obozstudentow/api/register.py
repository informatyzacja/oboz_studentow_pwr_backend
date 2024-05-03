
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status

from ..models import *

from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import AllowAny

import random

from django.core.mail import send_mail

from rest_framework_simplejwt.tokens import RefreshToken

def send_verification_email(user: User):

    # send email to user with verification code
    return send_mail(
        'Kod weryfikacyjny',
        f'Cześć, twój kod weryfikacyjny to: {user.verification_code}',
        from_email = None,
        recipient_list = [user.email],
    )
    

@api_view(['POST'])
@permission_classes([AllowAny])
def send_email_verification(request):

    email = request.data.get('email', None)

    if not email:
        return Response( 
            {'error': 'No email or first name'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.filter(email=email).first()

    if not user:
        return Response({'exists': False})
    
    if not user.verification_code or user.verification_code_valid_until_datetime < timezone.now():
        user.verification_code = random.randint(10000000, 99999999)
        user.verification_code_valid_until_datetime = timezone.now() + timezone.timedelta(minutes=30)

        user.save()

    # send email to user with verification code
    response = send_verification_email(user)

    return Response({'exists': True, 'email_sent': response})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_code(request):
    '''
    Verify email code
    '''
    code = request.data.get('code', None)

    if not code:
        return Response( 
            {'error': 'No code'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    email = request.data.get('email', None)

    if not email:
        return Response( 
            {'error': 'No email'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = User.objects.filter(email=email, verification_code=code, verification_code_valid_until_datetime__gte=timezone.now()).first()

    if user:
        user.verification_code = None
        user.verification_code_valid_until_datetime = None

        user.save()

        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        return Response({'refresh': refresh_token, 'access': str(refresh.access_token)}) 
    
    return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)

