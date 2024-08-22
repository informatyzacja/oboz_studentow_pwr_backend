from rest_framework import serializers, routers, viewsets, mixins
from django.db.models import Q


from obozstudentow_async.models import Message
from ..models import User, TinderAction
from obozstudentow_async.models import Chat
from django.db.models import Max
from .tinder import TinderProfileSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response

class MessageSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    username = serializers.SerializerMethodField()
    fromMe = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.first_name + " " + obj.user.last_name[0] + '.' + (' ('+obj.user.title+')' if obj.user.title else '')
    
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
        queryset = queryset.filter(chat__enabled = True, chat__users = self.request.user).exclude(chat__blocked_by = self.request.user).order_by('date')
        return queryset
    
class ChatSerializer(serializers.ModelSerializer):
    house_chat = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    tinder_profile = serializers.SerializerMethodField()
    notifications_blocked = serializers.SerializerMethodField()

    def get_house_chat(self, obj):
        return obj.house_set.exists()
    
    def get_last_message(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            return MessageSerializer(last_message, context={'request': self.context['request']}).data
        elif not obj.house_set.exists() and obj.users.count() == 2:
            user = obj.users.filter(~Q(id=self.context['request'].user.id)).first()
            last_action = TinderAction.objects.filter(
                Q(user=user, target=self.context['request'].user) | Q(user=self.context['request'].user, target=user)
            ).filter(action__in=[1,2]).order_by('-date').first()
            return {
                'message': user.tinderprofile.description if hasattr(user,'tinderprofile') else None,
                'date': last_action.date if last_action else None
            }
        
        else:
            return None
        
    def get_avatar(self, obj):
        if obj.house_set.exists():
            return None
        
        if obj.group_set.exists():
            return self.context['request'].build_absolute_uri(obj.group_set.first().logo.url) if obj.group_set.first().logo else None
        
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
    
    def get_tinder_profile(self, obj):
        if not obj.group_set.exists() and obj.name[:6] == 'tinder':
            user = obj.users.filter(~Q(id=self.context['request'].user.id)).first()
            return TinderProfileSerializer(user.tinderprofile, context={'request': self.context['request']}).data if hasattr(user,'tinderprofile') else None
        return None
    
    def get_notifications_blocked(self, obj):
        return obj.notifications_blocked_by.filter(id=self.context['request'].user.id).exists()
    class Meta:
        model = Chat
        fields = '__all__'

class ChatViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatSerializer

    def get_queryset(self):
        return self.request.user.chat_set.filter(enabled=True).exclude(blocked_by = self.request.user).annotate(last_message_date=Max('message__date')).order_by('-last_message_date')
    

@api_view(['PUT'])
def block_chat(request, chat_id):
    chat = Chat.objects.get(id=chat_id)
    if request.user not in chat.users.all():
        return Response({'status': 'error', 'message': 'You are not a member of this chat'}, status=400)
    
    block = request.data.get('block', True)
    if block:
        chat.blocked_by.add(request.user)
    else:
        chat.blocked_by.remove(request.user)

    return Response({'status': 'success'})


@api_view(['PUT'])
def block_chat_notifications(request, chat_id):
    chat = Chat.objects.get(id=chat_id)
    if request.user not in chat.users.all():
        return Response({'status': 'error', 'message': 'You are not a member of this chat'}, status=400)
    
    block = request.data.get('block', True)
    if block:
        chat.notifications_blocked_by.add(request.user)
    else:
        chat.notifications_blocked_by.remove(request.user)

    return Response({'status': 'success'})