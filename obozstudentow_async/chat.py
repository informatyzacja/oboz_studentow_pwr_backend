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

from .models import Message

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
def save_message(message, user, group_name):
	message = Message.objects.create(
		message=message,
		user=user,
		group_name=group_name
	)
	message.save()
	while Message.objects.filter(group_name=group_name).count() > 100:
		Message.objects.filter(group_name=group_name).order_by('date')[0].delete()
	return message

@database_sync_to_async
def send_message_notification(title, content, house, excludeUser=None):
	try:
		# print("send message notification", title, content, house)
		tokens = list(UserFCMToken.objects.filter(user__in=User.objects.filter(house__pk=house).exclude(id=excludeUser)).values_list('token', flat=True))
		
		response = send_notification(title, content, tokens)
	except:
		pass

class ChatConsumer(AsyncWebsocketConsumer):

	async def connect(self):
		try:
			# print("connected")
			self.user = self.scope["user"]

			if self.user.is_anonymous:
				await self.close()
				return
			
			user = await get_user(self.user.id)
			self.house = await get_user_house(user)
			if not self.house:
				await self.close()
				return
			
			self.roomGroupName = "house_" + str(self.house)
			
			await self.channel_layer.group_add(
				self.roomGroupName ,
				self.channel_name
			)
			await self.accept()
		except Exception as e:
			print(e)
			await self.close()
			return

	async def disconnect(self , close_code):
		# print("disconnected")
		await self.channel_layer.group_discard(
			self.roomGroupName ,
			self.channel_layer
		)

	async def receive(self, text_data):
		try:
			# print("received", text_data, self)
			if self.user.is_anonymous:
				await self.close()
				return
			
			text_data_json = json.loads(text_data)
			message = text_data_json["message"]
			savedMessage = await save_message(message, self.user, self.roomGroupName)
			
			username = self.user.first_name + " " + self.user.last_name
			await self.channel_layer.group_send(
				self.roomGroupName,{
					"type" : "sendMessage" ,
					"message" : message ,
					"username" : username ,
					"user_id" : self.user.id ,
					"date": str(timezone.now())
				})
			
			#send notifications
			await send_message_notification(f"{username} napisał/a:", message, self.house, self.user.id)
		except Exception as e:
			print(e)
		
	async def sendMessage(self , event):
		# print("send message", event)
		message = event["message"]
		username = event["username"]
		user_id = event["user_id"]
		date = event["date"]
		await self.send(text_data = json.dumps({ "message":message ,"username":username, "user_id":user_id, "date":date }))
