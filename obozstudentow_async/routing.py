from django.urls import path
from .chat import ChatConsumer
from .houseSignups import HouseSignupsConsumer

# Here, "" is routing to the URL ChatConsumer which
# will handle the chat functionality.
websocket_urlpatterns = [
    path("chat/", ChatConsumer.as_asgi()),
    path("house-signups/", HouseSignupsConsumer.as_asgi()),
]
