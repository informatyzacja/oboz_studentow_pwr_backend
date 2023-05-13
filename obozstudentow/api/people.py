
from rest_framework import serializers, viewsets
from django.db.models import Q
from django.utils import timezone

from ..models import SoberDuty, LifeGuard, Contact, User

class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'phoneNumber', 'photo', 'title')

class PersonViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = PersonSerializer

class CurrentSoberDutyViewSet(viewsets.ModelViewSet):
    queryset = SoberDuty.objects.all()
    serializer_class = PersonSerializer

    def get_queryset(self):
        return User.objects.filter(id__in=self.queryset.filter(start__lte=timezone.now(), end__gte=timezone.now()).values('user'))

class LifeGuardViewSet(viewsets.ModelViewSet):
    queryset = LifeGuard.objects.all()
    serializer_class = PersonSerializer

    def get_queryset(self):
        return User.objects.filter(id__in=self.queryset.values('user'))


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = PersonSerializer

    def get_queryset(self):
        return User.objects.filter(id__in=self.queryset.values('user'))