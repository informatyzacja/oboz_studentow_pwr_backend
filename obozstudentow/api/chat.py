from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q


from obozstudentow_async.models import Message
from ..models import User

class MessageSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    username = serializers.SerializerMethodField()
    fromMe = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.first_name + " " + obj.user.last_name
    
    def get_fromMe(self, obj):
        return obj.user == self.context['request'].user

    class Meta:
        model = Message
        fields = ('id', 'message', 'username', 'user_id', 'date', 'fromMe')

class MessageViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        group_name = ('house_' + str(self.request.user.house.pk)) if self.request.user.house else None
        if group_name is not None:
            queryset = queryset.filter(group_name=group_name).order_by('date')
            if queryset.count() > 100:
                queryset = queryset[:100]
        else:
            queryset = queryset.none()
        return queryset