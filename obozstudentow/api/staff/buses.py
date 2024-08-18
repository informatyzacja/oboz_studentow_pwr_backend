from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required
from django.urls import path
from django.db.models import Count, Q

from ...models import User, Bus

@api_view(['GET'])
@permission_required('obozstudentow.can_check_bus_presence')
def get_buses(request):
    return Response(Bus.objects.all().annotate(
        users_count=Count('user'),
        present_users_count=Count('user', filter=Q(user__bus_presence=True)),
        opaski_count=Count('user', filter=Q(user__bandId__isnull=False))
    ).order_by('description').values('id', 'description', 'users_count', 'present_users_count', 'opaski_count'))

@api_view(['GET'])
@permission_required('obozstudentow.can_check_bus_presence')
def get_bus_users(request):
    if 'bus_id' not in request.GET:
        return Response({'success': False, 'error': 'Nie podano ID autobusu'})

    if not Bus.objects.filter(id=request.GET['bus_id']).exists():
        return Response({'success': False, 'error': 'Autobus nie istnieje'})

    bus = Bus.objects.get(id=request.GET['bus_id'])

    return Response(User.objects.filter(bus=bus).annotate(
        bandId_isnull=Count('bandId')
    ).order_by('bus_presence', 'bandId_isnull', 'last_name', 'first_name').values('id', 'first_name', 'last_name', 'phoneNumber', 'bus_presence', 'bandId'))

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

    user.bus_presence = request.data['bus_presence']
    user.save()

    return Response({'success': True, 'error': None, 'user': user.first_name + ' ' + user.last_name, 'bus_presence': user.bus_presence})

@api_view(['PUT'])
@permission_required('obozstudentow.can_check_bus_presence')
def set_user_band_id(request):
    if 'user_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID użytkownika'})
    if 'band_id' not in request.data:
        return Response({'success': False, 'error': 'Nie podano ID opaski'})

    if not User.objects.filter(id=request.data['user_id']).exists():
        return Response({'success': False, 'error': 'Użytkownik nie istnieje'})

    user = User.objects.get(id=request.data['user_id'])

    if user.bandId is not None:
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