import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from asgiref.sync import sync_to_async

import django

django.setup()

from obozstudentow.models import User, UserFCMToken
from obozstudentow.api.notifications import send_notification

from channels.db import database_sync_to_async

from django.contrib.auth.models import AnonymousUser

from django.utils import timezone

from .models import Message


class HouseSignupsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = "house-signups"

        await self.accept()
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, close_code):
        # print("disconnected")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send(self, event):
        await self.send_json(event)
