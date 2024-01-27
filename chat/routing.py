from django.urls import path , include
from .consumers import ChatConsumer
from .houseSignups import HouseSignupsConsumer

# Here, "" is routing to the URL ChatConsumer which
# will handle the chat functionality.
websocket_urlpatterns = [
	path("chat/" , ChatConsumer.as_asgi()) ,
    path("house-signups/" , HouseSignupsConsumer.as_asgi()),
]

# from channels.security.websocket import AllowedHostsOriginValidator
# from channels.routing import ProtocolTypeRouter, URLRouter
# from ..obozstudentowProject.middleware import TokenAuthMiddleware
# # from django.conf.urls import url

# application = ProtocolTypeRouter({
#         'websocket': AllowedHostsOriginValidator(
#             TokenAuthMiddleware(
#                 URLRouter(
#                     [
#                         path("chat/" , ChatConsumer.as_asgi()) ,
#                         path("house-signups/" , HouseSignupsConsumer.as_asgi()),
#                     ]
#                 )
#             )
#         )
#     })