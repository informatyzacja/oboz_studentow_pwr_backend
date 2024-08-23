from rest_framework import serializers, viewsets, mixins
from django.db.models import Q, F, Count
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status

from ..models import House, HouseSignupProgress, User

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class HouseLocatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('bandId', 'first_name', 'last_name')

class HouseSignupProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseSignupProgress
        fields = '__all__'

class HouseSerializer(serializers.ModelSerializer):
    locators_data = serializers.SerializerMethodField()

    def get_locators_data(self, obj):
        return HouseLocatorSerializer( User.objects.filter(house=obj), many=True, context=self.context ).data

    class Meta:
        model = House
        fields = ('id', 'name', 'places', 'floor', 'locators', 'locators_data', 'housesignupprogress', 'description', 'signup_open', 'signout_open')
        depth = 1

def house_signups_active():
    active = Setting.objects.get(name='house_signups_active').value.lower() == 'true'
    if active and Setting.objects.get(name='house_signup_start_datetime').value:
        active = timezone.datetime.strptime(Setting.objects.get(name='house_signup_start_datetime').value, '%Y-%m-%d %H:%M') <= timezone.now()

    return active

class HouseViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = House.objects.order_by('floor','name')
    serializer_class = HouseSerializer
    

    def get_queryset(self):
        if not house_signups_active():
            return self.queryset.none()

        return self.queryset.annotate(Count("user")).filter(Q(places__gt=F("user__count")) | Q(id = self.request.user.house.id if self.request.user.house else None)).order_by('floor','name')
    

from ..models import Setting
from rest_framework.decorators import api_view
from django.db import transaction


@api_view(['PUT'])
def signup_user_for_house(request, id):
    room_instead_of_house = Setting.objects.get_or_create(name='room_instead_of_house', defaults={'value': 'false', 'description': 'Czy zamienić nazwę "domek" na "pokój" w opisach?'})[0].value.lower() == 'true'

    if not house_signups_active():
        return Response({'success': False, 'error': f'Zapisy na {"pokoje" if room_instead_of_house else "domki"} są obecnie wyłączone'})

    if not House.objects.filter(id=id).exists():
        return Response({'success': False, 'error': f'Nie znaleziono {"pokoju" if room_instead_of_house else "domku"} o podanym id'})
    
    house = House.objects.get(id=id)

    if not house.signup_open:
        return Response({'success': False, 'error': f'Zapisy do tego {"pokoju" if room_instead_of_house else "domku"} są obecnie zamknięte'})

    if house.full():
        return Response({'success': False, 'error': f'{"Pokój" if room_instead_of_house else "Domek"} jest już pełny'})
    
    if request.data.get('bandId'):
        if not User.objects.filter(bandId=request.data.get('bandId')).exists():
            return Response({'success': False, 'error': 'Nie znaleziono użytkownika o podanym ID'})
    
        user = User.objects.get(bandId=request.data.get('bandId'))
    else:
        user = request.user

    
    if user != request.user and user.house is not None:
        if user.house == house:
            return Response({'success': False, 'error': f'Ten użytkownik jest już zapisany do tego {"pokoju" if room_instead_of_house else "domku"}'})
        
        return Response({'success': False, 'error': f'Ten użytkownik jest już zapisany do jakiegoś {"pokoju" if room_instead_of_house else "domku"}. Jeżeli chcesz go/ją zapisać do tego {"pokoju" if room_instead_of_house else "domku"}, najpierw poproś go/ją, aby opuścił/a obecny {"pokój" if room_instead_of_house else "domek"}. Może to zrobić w zapisach na {"pokoje" if room_instead_of_house else "domki"} w swojej aplikacji.'})
    
    if user.house == house:
        return Response({'success': False, 'error': f'Jesteś już zapisany/a do tego {"pokoju" if room_instead_of_house else "domku"}'})
    
    with transaction.atomic():

        channel_layer = get_channel_layer()

        if HouseSignupProgress.objects.filter(user=request.user).exists():
            progress = HouseSignupProgress.objects.get(user=request.user)

            if progress.house != house:
                async_to_sync(channel_layer.group_send)(
                    'house-signups',
                    {
                        'type': 'send',
                        'event': 'update',
                        'house': progress.house.id,
                        'progress': None,
                        'locators': progress.house.locators(),
                        'locators_data': HouseLocatorSerializer( User.objects.filter(house=progress.house), many=True ).data,
                    }
                )
                progress.delete()

        if HouseSignupProgress.objects.filter(house=house).exists():
            progress = HouseSignupProgress.objects.get(house=house)

            if progress.user != request.user and not progress.free():
                return Response({'success': False, 'error': f'Ktoś inny aktualnie zapisuje się do tego {"pokoju" if room_instead_of_house else "domku"}'})
            
            progress.user = request.user
            progress.save()
        else:
            progress = HouseSignupProgress(house=house, user=request.user)
            progress.save()

        user.house = house
        user.save()

        async_to_sync(channel_layer.group_send)(
            'house-signups',
            {
                'type': 'send',
                'event': 'update',
                'house': house.id,
                'progress': HouseSignupProgressSerializer(progress).data,
                'locators': house.locators(),
                'locators_data': HouseLocatorSerializer( User.objects.filter(house=house), many=True ).data,
            }
        )
        
        return Response({'success': True, 'progress_last_updated': progress.last_updated})
    

@api_view(['PUT'])
def leave_house(request):

    room_instead_of_house = Setting.objects.get_or_create(name='room_instead_of_house', defaults={'value': 'false', 'description': 'Czy zamienić nazwę "domek" na "pokój" w opisach?'})[0].value.lower() == 'true'

    if request.user.house is None:
        return Response({'success': False, 'error': f'Nie jesteś zapisany do żadnego {"pokoju" if room_instead_of_house else "domku"}'})

    if not house_signups_active():
        return Response({'success': False, 'error': f'Zapisy na {"pokoje" if room_instead_of_house else "domki"} są obecnie wyłączone'})
    
    house = request.user.house

    if not house.signout_open:
        return Response({'success': False, 'error': f'Wypisywanie się z tego {"pokoju" if room_instead_of_house else "domku"} jest zablokowane'})
    
    request.user.house = None
    request.user.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'house-signups',
        {
            'type': 'send',
            'event': 'update',
            'house': house.id,
            'locators': house.locators(),
            'locators_data': HouseLocatorSerializer( User.objects.filter(house=house), many=True ).data,
        }
    )

    return Response({'success': True})



@api_view(['GET'])
def get_house_signups_info(request):
    room_instead_of_house = Setting.objects.get_or_create(name='room_instead_of_house', defaults={'value': 'false', 'description': 'Czy zamienić nazwę "domek" na "pokój" w opisach?'})[0].value.lower() == 'true'

    return Response({'room_instead_of_house': room_instead_of_house, 'house_signups_active': house_signups_active(), 'house_signup_start_datetime': Setting.objects.get(name='house_signup_start_datetime').value })