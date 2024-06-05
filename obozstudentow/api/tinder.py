

from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..models import *
from rest_framework import serializers

import base64

from django.core.files.base import ContentFile

from django.utils import timezone

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


def tinder_active():
    active = Setting.objects.get(name='tinder_swiping_active').value.lower() == 'true'
    if active and Setting.objects.get(name="tinder_swiping_activate_datetime").value:
        active = timezone.datetime.strptime(Setting.objects.get(name="tinder_swiping_activate_datetime").value, '%Y-%m-%d %H:%M') <= timezone.now()

    return active

@api_view(['GET'])
def loadTinderProfiles(request):

    if not tinder_active():
        return Response({'info': 'Przeglądanie profili jest obecnie wyłączone'}, status=200)
    
    user = request.user

    if not TinderProfile.objects.filter(user=user).exists():
        return Response({'error': 'Brak profilu'}, status=400)

    # profiles = TinderProfile.objects.exclude(user=user).exclude(user__tinderaction_target__user=user).order_by('?')[:10]

    # demo profiles
    profiles = TinderProfile.objects.exclude(user=user)[0]
    profiles = [profiles] * 10

    serializer = TinderProfileSerializer(profiles, context={'request': request}, many=True)
    data = serializer.data

    # demo id
    import random
    for profile in data:
        profile['id'] = random.randint(1, 100000)

    return Response(data)


@api_view(['POST'])
def tinderAction(request):

    if not tinder_active():
        return Response({'error': 'Funkcja swipingu jest wyłączona'}, status=400)
    
    user = request.user

    if not TinderProfile.objects.filter(user=user).exists():
        return Response({'error': 'Brak profilu'}, status=400)
    
    target = User.objects.get(id=request.data.get('target'))

    if target == user:
        return Response({'error': 'Nie możesz oceniać siebie'}, status=400)

    action = request.data.get('action')

    tinderaction = TinderAction.objects.get_or_create(user=user, target=target, defaults={'action':0})[0]

    if action == 'like':
        tinderaction.action = 1
    elif action == 'dislike':
        tinderaction.action = 0
    elif action == 'superlike':
        if not user.tinderprofile.super_like_used:
            user.tinderprofile.super_like_used = True
            user.tinderprofile.save()
        else:
            return Response({'error': 'Już użyłeś superlajka'}, status=400)
        tinderaction.action = 2
    else:
        return Response({'error': 'Niepoprawna akcja'}, status=400)
    
    tinderaction.save()

    match = (tinderaction.action == 1 and TinderAction.objects.filter(user=target, target=user, action__in=[1,2]).exists()) or tinderaction.action == 2

    if match:
        chat = Chat.objects.filter(name='tinder').filter(users=user).filter(users=target).first()
        if not chat:
            chat = Chat.objects.create(name='tinder')
            chat.users.add(user, target)
    return Response({'success': True, 'match': match, 'chat_id': chat.id if match else None})