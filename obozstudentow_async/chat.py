import json
from channels.generic.websocket import AsyncWebsocketConsumer

from asgiref.sync import sync_to_async

import django
django.setup()

from obozstudentow.models import User, UserFCMToken
from obozstudentow.api.notifications import send_notification

from channels.db import database_sync_to_async

from django.contrib.auth.models import AnonymousUser

from django.utils import timezone

from .models import Message, Chat

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()
    
@database_sync_to_async
def get_user_house(user):
	if not user.house:
		return None
	return user.house.pk

@database_sync_to_async
def save_message(message, user, chat_id):
	if user.chat_set.filter(id=chat_id, enabled=True).exists():
		message = Message.objects.create(
			message=message,
			user=user,
			chat = Chat.objects.get(id=chat_id)
		)
		message.save()
		if Message.objects.filter(chat__id=chat_id).count() > 1000:
			Message.objects.filter(chat__id=chat_id).order_by('date')[:-1000].delete()
		return message
	return None

@database_sync_to_async
def send_message_notification(message):
	try:
		# print("send message notification", title, content, house)
		tokens = list(UserFCMToken.objects.filter(user__notifications=True, user__in=message.chat.users.exclude(id=message.user.id).exclude(id__in=message.chat.notifications_blocked_by.values('id')).exclude(id__in=message.chat.blocked_by.values('id')).values('id')).values_list('token', flat=True))

		group_name = ""
		if message.chat.users.count() > 2:
			group_name = "\nDo grupy " + message.chat.name
		
		response = send_notification(f"{message.user.first_name} {message.user.last_name[0]}. " + group_name, message.message, tokens)
	except Exception as e:
		print(e)
		pass

class ChatConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		try:
			# print("connected")
			self.user = self.scope["user"]

			if self.user.is_anonymous:
				await self.close()
				return
			
			async for chat in self.user.chat_set.filter(enabled=True):
				await self.channel_layer.group_add(
					str(chat.id),
					self.channel_name
				)
			await self.accept()

		except Exception as e:
			print(e)
			await self.close()
			return

	async def disconnect(self , close_code):
		# print("disconnected")
		if self.user.is_anonymous:
			return
		
		for chat in self.user.chat_set.all():
			await self.channel_layer.group_discard(
				str(chat.id),
				self.channel_name
			)


	async def receive(self, text_data):
		try:
			# print("received", text_data, self)
			if self.user.is_anonymous:
				await self.close()
				return
			
			text_data_json = json.loads(text_data)
			message = text_data_json["message"]
			chat_id = text_data_json["chat"]
			savedMessage = await save_message(message, self.user, chat_id)

			if not savedMessage:
				return
			
			username = self.user.first_name + " " + self.user.last_name[0] + '.'
			await self.channel_layer.group_send(
				str(chat_id), {
					"type" : "sendMessage" ,
					"message" : message ,
					"username" : username ,
					"user_id" : self.user.id ,
					"chat" : chat_id ,
					"date": str(timezone.now())
				})
			
			#send notifications
			await send_message_notification(savedMessage)

		except Exception as e:
			print(e)
		
	async def sendMessage(self , event):
		try:
			# print("send message", event)
			await self.send(text_data = json.dumps(event))
		except Exception as e:
			print(e)
