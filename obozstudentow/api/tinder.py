

from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import *
from rest_framework import serializers

import base64

from django.core.files.base import ContentFile

@api_view(['POST'])
def uploadProfilePhoto(request):
    profile = TinderProfile.objects.get_or_create(user=request.user)[0]

    photoBase64String = request.data.get('photo')

    if not photoBase64String:
        return Response({'error': 'Brak zdjęcia'}, status=400)
    
    format, imgstr = photoBase64String.split(';base64,')
    ext = format.split('/')[-1]

    profile.photo.save(f'{request.user.id}.{ext}', ContentFile(base64.b64decode(imgstr)), save=True)

    return Response({'success': True, 'tinder_profile': TinderProfileSerializer(profile, context={'request': request}).data})


@api_view(['POST'])
def uploadProfileData(request):
    profile = TinderProfile.objects.get_or_create(user=request.user)[0]
    
    if description := request.data.get('description'):
        profile.description = description

    profile.save()

    return Response({'tinder_profile': TinderProfileSerializer(profile, context={'request': request}).data})


class TinderProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.first_name')

    class Meta:
        model = TinderProfile
        fields = '__all__'

@api_view(['GET'])
def loadTinderProfiles(request):
    user = request.user

    if not TinderProfile.objects.filter(user=user).exists():
        return Response({'error': 'Brak profilu'}, status=400)

    profiles = TinderProfile.objects.exclude(user=user).exclude(user__tinderaction_target__user=user).order_by('?')[:10]

    serializer = TinderProfileSerializer(profiles, many=True)

    return Response(serializer.data)

@api_view(['POST'])
def tinderAction(request):
    user = request.user

    if not TinderProfile.objects.filter(user=user).exists():
        return Response({'error': 'Brak profilu'}, status=400)
    
    target = User.objects.get(id=request.data.get('target'))

    action = request.data.get('action')

    tinderaction = TinderAction.objects.get_or_create(user=user, target=target)[0]

    if action == 'like':
        tinderaction.action = 1
    elif action == 'dislike':
        tinderaction.action = 0
    elif action == 'superlike':
        tinderaction.action = 2
    else:
        return Response({'error': 'Niepoprawna akcja'}, status=400)
    
    tinderaction.save()

    match = TinderAction.objects.filter(user=target, target=user, action__in=[1,2]).exists()

    return Response({'success': True, 'match': match})