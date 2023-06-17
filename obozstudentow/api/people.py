
from rest_framework import serializers, viewsets, mixins
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response

from ..models import SoberDuty, LifeGuard, Staff, User

class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'phoneNumber', 'photo', 'title')

class ContactViewSet(viewsets.GenericViewSet):
    
    def list(self, request):

        return Response({
            'staff': PersonSerializer(User.objects.filter(id__in=Staff.objects.all().values('user')), many=True, context=self.get_serializer_context()).data,
            'lifeGuard': PersonSerializer(User.objects.filter(id__in=LifeGuard.objects.all().values('user')), many=True, context=self.get_serializer_context()).data, 
            'currentSoberDuty': PersonSerializer(User.objects.filter(id__in=SoberDuty.objects.filter(start__lte=timezone.now(), end__gte=timezone.now()).values('user')), many=True, context=self.get_serializer_context()).data
        })