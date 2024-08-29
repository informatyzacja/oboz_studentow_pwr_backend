
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status

from ..models import *

from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import AllowAny

import random

from django.core.mail import send_mail

from rest_framework_simplejwt.tokens import RefreshToken
from django.template.loader import render_to_string

def is_constant_code_user(user):
    return user.email == 'test@oboz.samorzad.pwr.edu.pl'

def send_verification_email(user: User):


    subject = 'Kod weryfikacyjny'
    html_message = render_to_string('confirmation_email.html', {'code': user.verification_code})

    # send email to user with verification code
    return send_mail(subject, f'Cześć, twój kod weryfikacyjny to: {user.verification_code}', None, [user.email], html_message=html_message)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_email_verification(request):

    email = request.data.get('email', None)

    if not email:
        return Response( 
            {'error': 'No email or first name'}
    )

    user = User.objects.filter(email=email).first()

    if not user:
        return Response({'exists': False, 'error': 'Podany adres e-mail nie jest przypisany do żadnego uczestnika obozu.'})
    
    if not user.is_active:
        return Response({'error': 'Użytkownik nie jest aktywny'})
    
    if is_constant_code_user(user):
        user.verification_code_valid_until_datetime = timezone.now() + timezone.timedelta(minutes=30)
        user.save()

        return Response({'exists': True, 'email_sent': True})
    
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
        if not user.is_active:
            return Response({'error': 'Użytkownik nie jest aktywny'}, status=status.HTTP_400_BAD_REQUEST)

        if not is_constant_code_user(user): 
            user.verification_code = None
        user.verification_code_valid_until_datetime = None
        user.last_login = timezone.now()
        user.save()

        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        return Response({'refresh': refresh_token, 'access': str(refresh.access_token)}) 
    
    return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)
