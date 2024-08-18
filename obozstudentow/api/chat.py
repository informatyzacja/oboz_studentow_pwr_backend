from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q


from obozstudentow_async.models import Message
from ..models import User
from obozstudentow_async.models import Chat

class MessageSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    username = serializers.SerializerMethodField()
    fromMe = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.first_name + " " + obj.user.last_name[0] + '.'
    
    def get_fromMe(self, obj):
        return obj.user == self.context['request'].user

    class Meta:
        model = Message
        fields = ('id', 'message', 'username', 'user_id', 'date', 'fromMe', 'chat')

class MessageViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(chat__users = self.request.user).order_by('date')
        return queryset
    
class ChatSerializer(serializers.ModelSerializer):
    house_chat = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_house_chat(self, obj):
        return obj.house_set.exists()
    
    def get_last_message(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            return MessageSerializer(last_message, context={'request': self.context['request']}).data
        elif not obj.house_set.exists() and obj.users.count() == 2:
            user = obj.users.filter(~Q(id=self.context['request'].user.id)).first()
            return {
                'message': user.tinderprofile.description if hasattr(user,'tinderprofile') else None,
            }
        
        else:
            return None
        
    def get_avatar(self, obj):
        if obj.house_set.exists():
            return None
        
        if obj.users.count() == 2:
            user = obj.users.filter(~Q(id=self.context['request'].user.id)).first()
            return self.context['request'].build_absolute_uri((user.tinderprofile.photo.url if hasattr(user,'tinderprofile') and user.tinderprofile.photo else None) or (user.photo.url if user.photo else None))
        
    def get_name(self, obj):
        if obj.house_set.exists():
            return obj.name
        
        if obj.users.count() == 2:
            user = obj.users.filter(~Q(id=self.context['request'].user.id)).first()
            return user.first_name + " " + (user.last_name[0] + '.' if user.last_name else '')
        
        return obj.name
    class Meta:
        model = Chat
        fields = '__all__'

class ChatViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatSerializer

    def get_queryset(self):
        return self.request.user.chat_set.all()