from channels.generic.websocket import AsyncJsonWebsocketConsumer

import django

django.setup()


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
