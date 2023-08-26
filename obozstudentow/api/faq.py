
from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q



from ..models import FAQ
class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer')

class FAQViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FAQ.objects.order_by('sort_order')
    serializer_class = FAQSerializer

    