from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required

from ..models import UserFCMToken


@api_view(["POST"])
def register_fcm_token(request):
    token = request.data.get("token")
    if token is None:
        return Response({"success": False, "error": "Nie podano tokenu"})

    UserFCMToken.objects.filter(token=token).delete()
    UserFCMToken.objects.create(user=request.user, token=token)

    request.user.notifications = True
    request.user.save()

    return Response({"success": True})


@api_view(["PUT"])
def enable_disable_notifications(request):
    enabled = request.data.get("enabled")
    if enabled is None:
        return Response({"success": False, "error": "Nie podano enabled"})

    request.user.notifications = enabled
    request.user.save()

    return Response({"success": True})


import firebase_admin
from firebase_admin import credentials, messaging
from obozstudentowProject.settings import BASE_DIR

if (BASE_DIR / "oboz-studentow-pwr-firebase-adminsdk.json").exists():
    cred = credentials.Certificate(
        BASE_DIR / "oboz-studentow-pwr-firebase-adminsdk.json"
    )
    firebase_admin.initialize_app(cred)
else:
    import logging

    logging.error(
        "Firebase certificate file is missing. Firebase cannot be initialized."
    )


def send_notification(title, body, tokens, link=None):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens,
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(sound="default"),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default"),
            ),
        ),
    )
    response = messaging.send_each_for_multicast(message)
    return response
