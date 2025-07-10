from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required
from django.urls import path
from django.db.models import Count, Q, F

from ...models import User, Bus, Setting

@api_view(['GET'])
@permission_required('obozstudentow.can_check_bus_presence')
def get_buses(request):

    bus_presence_type = Setting.objects.get(name="bus_presence").value.lower()
    if bus_presence_type not in ('to','return'):
        return Response({'success': False, 'error': 'Sprawdzanie obecności w busach nie jest aktywowane'})
    bus_presence_to = bus_presence_type == 'to'

    users_own_transport = User.objects.filter(Q(bus__isnull=True) | (Q(bus_info=User.BusInfoChoices.RETURN) if bus_presence_to else Q(bus_info=User.BusInfoChoices.RETURN)))
    users_count = users_own_transport.count()
    present_users_count = users_own_transport.filter(Q(bus_presence=True) if bus_presence_to else Q(bus_presence_return=True)).count()
    opaski_count = users_own_transport.filter(bandId__isnull=False, bandId__gte=300000).count()

    return Response(
        list(
            Bus.objects.all().annotate(

                users_count=Count('user', filter=Q(user__bus_info__in=(User.BusInfoChoices.BOTH, User.BusInfoChoices.TO))) if bus_presence_to else Count('user', filter=Q(user__bus_info__in=(User.BusInfoChoices.BOTH, User.BusInfoChoices.RETURN))),

                present_users_count=Count('user', filter=Q(user__bus_presence=True, user__bus_info__in=[User.BusInfoChoices.BOTH, User.BusInfoChoices.TO])) if bus_presence_to else Count('user', filter=Q(user__bus_presence_return=True, user__bus_info__in=[User.BusInfoChoices.BOTH,  User.BusInfoChoices.RETURN])),

                opaski_count=Count('user', filter=Q(user__bandId__isnull=False, user__bus_info__in=[User.BusInfoChoices.BOTH, User.BusInfoChoices.TO if bus_presence_to else User.BusInfoChoices.RETURN]))

            ).order_by('description').values('id', 'description', 'users_count', 'present_users_count', 'opaski_count')
         ) + [{
        'id': 0,
        'description': 'dojazd własny',
        'users_count': users_count,
        'present_users_count': present_users_count,
        'opaski_count': opaski_count
    }])

@api_view(['GET'])
@permission_required('obozstudentow.can_check_bus_presence')
def get_bus_users(request):
    if 'bus_id' not in request.GET:
        return Response({'success': False, 'error': 'Nie podano ID autobusu'})

    if request.GET['bus_id'] != '0' and not Bus.objects.filter(id=request.GET['bus_id']).exists():
        return Response({'success': False, 'error': 'Autobus nie istnieje'})

    bus_presence_type = Setting.objects.get(name="bus_presence").value.lower()
    bus_presence_to = bus_presence_type == 'to'
    presence_type  = 'bus_presence' if bus_presence_to else 'bus_presence_return'

    if Bus.objects.filter(id=request.GET['bus_id']).exists():
        bus = Bus.objects.get(id=request.GET['bus_id'])

        return Response(User.objects.filter(bus=bus, bus_info__in=[User.BusInfoChoices.BOTH, User.BusInfoChoices.TO if bus_presence_to else User.BusInfoChoices.RETURN]).annotate(
            bandId_isnull=Count('bandId'),
        ).order_by(presence_type, 'bandId_isnull', 'last_name', 'first_name').values('id', 'first_name', 'last_name', 'phoneNumber', 'bandId', 'bus_info',  presence = F(presence_type)))
    
    else:
        return Response(User.objects.filter(Q(bus__isnull=True) | (Q(bus_info=User.BusInfoChoices.RETURN) if bus_presence_to else Q(bus_info=User.BusInfoChoices.RETURN))).annotate(
            bandId_isnull=Count('bandId', filter=Q(bandId__gte=300000)),
        ).order_by(presence_type, 'bandId_isnull', 'last_name', 'first_name').values('id', 'first_name', 'last_name', 'phoneNumber', 'bandId', 'bus_info',  presence = F(presence_type)))


@api_view(['PUT'])
@permission_required('obozstudentow.can_check_bus_presence')
def set_bus_presence(request):
    if 'user_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID użytkownika'})

    if 'bus_presence' not in request.data:
        return Response({'success': False, 'error': 'Nie podano obecności'})
    
    if not User.objects.filter(id=request.data['user_id']).exists():
        return Response({'success': False, 'error': 'Użytkownik nie istnieje'})
    
    user = User.objects.get(id=request.data['user_id'])

    bus_presence_type = Setting.objects.get(name="bus_presence").value.lower()
    
    if bus_presence_type == 'to':
        user.bus_presence = request.data['bus_presence']
    elif bus_presence_type == 'return':
        user.bus_presence_return = request.data['bus_presence']
    else:
        return Response({'success': False, 'error': 'Sprawdzanie obecności w busach nie jest aktywowane'})
    
    user.save()

    return Response({'success': True, 'error': None, 'user': user.first_name + ' ' + user.last_name, 'presence': user.bus_presence if bus_presence_type == 'to' else user.bus_presence_return})

@api_view(['PUT'])
@permission_required('obozstudentow.can_check_bus_presence')
def set_user_band_id(request):
    if 'user_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID użytkownika'})
    if 'band_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID opaski'})
    
    try:
        # Walidacja numerów opasek
        if int(request.data['band_id']) < 300000:
            return Response({'success': False, 'error': 'Nieprawidłowy numer opaski'})
    except ValueError:
        return Response({'success': False, 'error': 'Nieprawidłowy numer opaski'})

    if not User.objects.filter(id=request.data['user_id']).exists():
        return Response({'success': False, 'error': 'Użytkownik nie istnieje'})

    user = User.objects.get(id=request.data['user_id'])

    if request.user.has_perm('obozstudentow.can_change_bands') == False:
        if user.bandId is not None and int(user.bandId) >= 300000:
            return Response({'success': False, 'error': 'Użytkownik ma już przypisaną opaskę'})
    
    if User.objects.filter(bandId=request.data['band_id']).exists():
        return Response({'success': False, 'error': 'Opaska jest już przypisana do innego użytkownika: ' + User.objects.get(bandId=request.data['band_id']).first_name + ' ' + User.objects.get(bandId=request.data['band_id']).last_name})

    user.bandId = request.data['band_id']
    user.save()

    return Response({'success': True, 'error': None, 'user': user.first_name + ' ' + user.last_name, 'band_id': user.bandId})

urlpatterns = [
    path('get-buses/', get_buses),
    path('get-bus-users/', get_bus_users),
    path('set-bus-presence/', set_bus_presence),
    path('set-user-band-id/', set_user_band_id)
]