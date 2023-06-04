from rest_framework import serializers, viewsets
from django.db.models import Q
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status

from .people import PersonSerializer

from ..models import Workshop, WorkshopSignup, WorkshopLeader, User

class WorkshopSerializer(serializers.HyperlinkedModelSerializer):
    userCount = serializers.SerializerMethodField('workshop_user_count')
    workshopleaders = serializers.SerializerMethodField()

    def workshop_user_count(self, obj):
        return obj.workshopsignup_set.count()
    
    def get_workshopleaders(self, obj):
        return PersonSerializer( User.objects.filter(id__in=obj.workshopleader_set.values('user')), context=self.context, many=True).data

    class Meta:
        model = Workshop
        fields = ('id', 'name', 'description', 'start', 'end', 'location', 'photo', 'userLimit', 'userCount', 'workshopleaders')

class WorkshopViewSet(viewsets.ModelViewSet):
    queryset = Workshop.objects.filter(visible=True)
    serializer_class = WorkshopSerializer

    def get_queryset(self):
        return self.queryset.filter(visible=True)
    
class WorkshopLeaderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WorkshopLeader
        fields = ('id', 'workshop', 'user')

class WorkshopLeaderViewSet(viewsets.ModelViewSet):
    queryset = WorkshopLeader.objects.all()
    serializer_class = WorkshopLeaderSerializer




#home
class WorkshopUserSignedUpViewSet(viewsets.ModelViewSet):
    queryset = Workshop.objects.all()
    serializer_class = WorkshopSerializer

    def get_queryset(self):
        return self.queryset.filter(Q(id__in=WorkshopSignup.objects.filter(user=self.request.user).values('workshop')) | Q(id__in=WorkshopLeader.objects.filter(user=self.request.user).values('workshop')), visible=True)


class WorkshopSignupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WorkshopSignup
        fields = ('id', 'workshop', 'user')

class WorkshopSignupViewSet(viewsets.ModelViewSet):
    queryset = WorkshopSignup.objects.all()
    serializer_class = WorkshopSignupSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    def create(self, request):
        if request.data.get('workshop') and request.data.get('user'):
            workshop = Workshop.objects.get(id=request.data.get('workshop'))
            if WorkshopSignup.objects.filter(workshop=workshop).count() < workshop.userLimit and not WorkshopSignup.objects.filter(workshop=workshop, user=request.user).exists() and workshop.visible and workshop.signupsOpen and workshop.start > timezone.now():
                WorkshopSignup.objects.create(workshop=workshop, user=request.user)
                return Response(status=status.HTTP_201_CREATED) 
            
        return Response(status=status.HTTP_409_CONFLICT)
    
    def destroy(self, request, pk=None):
        if WorkshopSignup.objects.filter(id=pk, user=request.user).exists():
            WorkshopSignup.objects.get(id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    