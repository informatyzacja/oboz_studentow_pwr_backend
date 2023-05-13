
from rest_framework import serializers, routers, viewsets
from django.db.models import Q



from ..models import FAQ
class FAQSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer')

class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

    