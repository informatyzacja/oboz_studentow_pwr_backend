from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q

from ..models import Group, GroupMember, GroupWarden, GroupType, UserFCMToken

from .notifications import send_notification

from .people import PersonSerializer
from ..models import User

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    wardens = serializers.SerializerMethodField()

    def get_wardens(self, obj):
        return PersonSerializer( User.objects.filter(id__in=GroupWarden.objects.filter(group=obj).values('user')), many=True, context=self.context ).data

    class Meta:
        model = Group
        fields = ('id', 'name', 'type', 'logo', 'map', 'wardens', 'description', 'messenger')
        depth = 1

class GroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GroupType
        fields = ('id', 'name')

class GroupTypeViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = GroupType.objects.all()
    serializer_class = GroupTypeSerializer


from ..models import Setting
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def get_group_signup_info(request):
    free_places = Group.objects.filter(~Q(type__name="Frakcja")).count() < int(Setting.objects.get(name="group_limit").value)
    group_user_min = int(Setting.objects.get(name="group_user_min").value)
    group_user_max = int(Setting.objects.get(name="group_user_max").value)
    user_in_group = GroupMember.objects.filter(user=request.user).filter(~Q(group__type__name="Frakcja")).exists()

    return Response({'free_places': free_places, 'group_user_min': group_user_min, 'group_user_max': group_user_max, 'user_in_group': user_in_group})

from ..models import NightGameSignup

@api_view(['POST'])
def signup_group(request):
    free_places = Group.objects.filter(~Q(type__name="Frakcja")).count() < int(Setting.objects.get(name="group_limit").value)

    if not free_places:
        return Response({'success':False, 'error': 'Brak wolnych miejsc','error_code': 1})
    
    if not 'group_name' in request.data:
        return Response({'success':False, 'error': 'Brak nazwy grupy','error_code': 2})
    
    if not 'people' in request.data:
        return Response({'success':False, 'error': 'Brak listy osób','error_code': 3})
    
    if len(request.data['people'])+1 < int(Setting.objects.get(name="group_user_min").value):
        return Response({'success':False, 'error': 'Za mało osób w grupie','error_code': 4})
    
    if len(request.data['people'])+1 > int(Setting.objects.get(name="group_user_max").value):
        return Response({'success':False, 'error': 'Za dużo osób w grupie','error_code': 5})
    
    if NightGameSignup.objects.filter(addedBy=request.user).exists():
        return Response({'success':False, 'error': 'Już zapisałeś grupę na grę nocną','error_code': 6})
    
    group_name = request.data['group_name']
    group_type = GroupType.objects.get(name="Gra nocna")

    if Group.objects.filter(name=group_name, type=group_type).exists():
        return Response({'success':False, 'error': 'Grupa o tej nazwie już istnieje','error_code': 7})

    group = Group.objects.create(name=group_name, type=group_type)
    group.save()


    # user making request
    nightGameSignup = NightGameSignup.objects.create(
        user_band = request.user.bandId,
        user_first_name = request.user.first_name,
        user_last_name = request.user.last_name,

        group = group,
        addedBy = request.user
    )
    if not GroupMember.objects.filter(user=request.user, group__type=group_type).exists():
        GroupMember.objects.create(user=request.user, group=group).save()
    else:
        group.delete()
        nightGameSignup.failed = True
        nightGameSignup.error = "Użytkownik jest już w jakiejś grupie"
        nightGameSignup.save()
        return Response({'success':False, 'error': f"Użytkownik {request.user.first_name} {request.user.last_name} jest już w jakiejś grupie",'error_code': 8})

    nightGameSignup.save()

    # other people
    for person in request.data['people']:
        nightGameSignup = NightGameSignup.objects.create(
            user_band = person['band'],
            user_first_name = person['first_name'],
            user_last_name = person['last_name'],

            group = group,
            addedBy = request.user
        )
        userError = ""
        if User.objects.filter(bandId=person['band'],first_name=person['first_name'].strip(),last_name=person['last_name'].strip()).exists():
            user = User.objects.get(bandId=person['band'],first_name=person['first_name'].strip(),last_name=person['last_name'].strip())

            if not GroupMember.objects.filter(user=user, group__type=group_type).exists():
                GroupMember.objects.create(user=user, group=group).save()
            else:
                nightGameSignup.failed = True
                nightGameSignup.error = "Użytkownik jest już w jakiejś grupie"
                userError = f"Użytkownik {person['first_name'].strip()} {person['last_name'].strip()} jest już w jakiejś grupie"

        elif User.objects.filter(bandId=person['band'], last_name=person['last_name'].strip()).exists():
            user = User.objects.get(bandId=person['band'], last_name=person['last_name'].strip())
            nightGameSignup.failed = True
            nightGameSignup.error = f"Nie znaleziono użytkownika o podanym imieniu. Znaleziony użytkownik to: {user.first_name} {user.last_name}, ID: {user.pk}, opaska: {user.bandId if user.bandId else 'brak numeru opaski'}"
            userError = f"Nie znaleziono użytkownika o podanych danych: {person['first_name'].strip()} {person['last_name'].strip()}, opaska: {person['band']}"

        elif User.objects.filter(bandId=person['band'], first_name=person['first_name'].strip()).exists():
            user = User.objects.get(bandId=person['band'], first_name=person['first_name'].strip())
            nightGameSignup.failed = True
            nightGameSignup.error = f"Nie znaleziono użytkownika o podanym nazwisku. Znaleziony użytkownik to: {user.first_name} {user.last_name}, ID: {user.pk}, opaska: {user.bandId if user.bandId else 'brak numeru opaski'}"
            userError = f"Nie znaleziono użytkownika o podanych danych: {person['first_name'].strip()} {person['last_name'].strip()}, opaska: {person['band']}"

        elif User.objects.filter(bandId=person['band']).exists():
            user = User.objects.get(bandId=person['band'])
            nightGameSignup.failed = True
            nightGameSignup.error = f"Nie znaleziono użytkownika o podanym imieniu i nazwisku. Znaleziony użytkownik to: {user.first_name} {user.last_name}, ID: {user.pk}, opaska: {user.bandId if user.bandId else 'brak numeru opaski'}"
            userError = f"Nie znaleziono użytkownika o podanych danych: {person['first_name'].strip()} {person['last_name'].strip()}, opaska: {person['band']}"
        
        elif User.objects.filter(first_name=person['first_name'].strip(), last_name=person['last_name'].strip()).exists():
            user = User.objects.get(first_name=person['first_name'].strip(), last_name=person['last_name'].strip())
            nightGameSignup.failed = True
            nightGameSignup.error = f"Nie znaleziono użytkownika o podanej opasce. Znaleziony użytkownik to: {user.first_name} {user.last_name}, ID: {user.pk}, opaska: {user.bandId if user.bandId else 'brak numeru opaski'}"
            userError = f"Nie znaleziono użytkownika o podanych danych: {person['first_name'].strip()} {person['last_name'].strip()}, opaska: {person['band']}"

        else:
            nightGameSignup.failed = True
            nightGameSignup.error = f"Nie znaleziono użytkownika o podanym imieniu, nazwisku, ani opasce."
            userError = f"Nie znaleziono użytkownika o podanych danych: {person['first_name'].strip()} {person['last_name'].strip()}, opaska: {person['band']}"
            
        nightGameSignup.save()
        if nightGameSignup.failed:
            group.delete()
            return Response({'success':False, 'error': userError, 'error_code': 9})

    #send notifications
    try:
        tokens = list(UserFCMToken.objects.filter(user__in=GroupMember.objects.filter(group=group).values_list('user', flat=True)).values_list('token', flat=True))

        title = f"Zostałeś/aś właśnie zapisany/a do grupy {group.name} na grę nocną."
        content = f"Grupę i jej członków możesz zobaczyć w zakładce \"profil\""
        absolute_url = request.build_absolute_uri("/app/profil")
        
        response = send_notification(title, content, tokens, link=absolute_url if request.is_secure() else None)
    except:
        pass
    
    
    return Response({'success': True})
    


