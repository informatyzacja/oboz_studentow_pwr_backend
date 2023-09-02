from rest_framework import serializers, viewsets, mixins
from django.db.models import Q
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status

from .people import PersonSerializer

from ..models import Workshop, WorkshopSignup, WorkshopLeader, User

class WorkshopSerializer(serializers.ModelSerializer):
    userCount = serializers.SerializerMethodField('workshop_user_count')
    workshopleaders = serializers.SerializerMethodField()
    userSignUpId = serializers.SerializerMethodField()
    workshopusers = serializers.SerializerMethodField()

    def get_userSignUpId(self, obj):
        signup = WorkshopSignup.objects.filter(workshop=obj, user=self.context['request'].user)
        return signup.first().id if signup.exists() else None

    def workshop_user_count(self, obj):
        return obj.workshopsignup_set.count()
    
    def get_workshopleaders(self, obj):
        return PersonSerializer( User.objects.filter(id__in=obj.workshopleader_set.values('user')), context=self.context, many=True).data

    def get_workshopusers(self, obj):
        return PersonSerializer(
            User.objects.filter(id__in = obj.workshopsignup_set.values('user') ) if (self.context['request'].user.id in obj.workshopleader_set.values_list('user', flat=True)) else User.objects.none()
        ,context=self.context, many=True ).data

    class Meta:
        model = Workshop
        fields = ('id', 'name', 'description', 'start', 'end', 'location', 'photo', 'userLimit', 'userCount', 'signupsOpen', 'signupsOpenTime', 'userSignUpId', 'workshopleaders', 'itemsToTake', 'workshopusers')

class WorkshopViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Workshop.objects.filter(visible=True)
    serializer_class = WorkshopSerializer

    def get_queryset(self):
        return self.queryset.filter(visible=True, end__gt=timezone.now())
    


#home
class WorkshopUserSignedUpViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Workshop.objects.all()
    serializer_class = WorkshopSerializer

    def get_queryset(self):
        return self.queryset.filter(
            Q(id__in=WorkshopSignup.objects.filter(user=self.request.user).values('workshop')) | Q(id__in=WorkshopLeader.objects.filter(user=self.request.user).values('workshop')
        ), visible=True, end__gt=timezone.now()).order_by('start')


class WorkshopSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkshopSignup
        fields = ('id', 'workshop', 'user')




class WorkshopSignupViewSet(viewsets.GenericViewSet):
    queryset = WorkshopSignup.objects.all()
    serializer_class = WorkshopSignupSerializer
    
    def create(self, request):
        if request.data.get('workshop'):
            workshop = Workshop.objects.get(id=request.data.get('workshop'))

            if WorkshopSignup.objects.filter(user = request.user, workshop__start = workshop.start).exists():
                return Response({'error': 'Jesteś już zapisany/a na inne warsztaty w tym samym czasie', 'success':False})

            if WorkshopSignup.objects.filter(workshop=workshop).count() < workshop.userLimit and not WorkshopSignup.objects.filter(workshop=workshop, user=request.user).exists() and workshop.visible and workshop.signupsOpen and (workshop.signupsOpenTime == None or workshop.signupsOpenTime <= timezone.now()) and workshop.end > timezone.now():
                WorkshopSignup.objects.create(workshop=workshop, user=request.user)
                return Response({}, status=status.HTTP_201_CREATED) 
            
            return Response({'error': 'Błąd zapisu'}, status=status.HTTP_409_CONFLICT)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        if WorkshopSignup.objects.filter(id=pk, user=request.user).exists():
            WorkshopSignup.objects.get(id=pk).delete()
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    
    