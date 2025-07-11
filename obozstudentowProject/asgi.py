# """
# ASGI config for obozstudentowProject project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
# """

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "obozstudentowProject.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from obozstudentow_async import routing


from channels.routing import ProtocolTypeRouter, URLRouter
from .channelsmiddleware import JwtAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": JwtAuthMiddleware(URLRouter(routing.websocket_urlpatterns)),
    }
)
