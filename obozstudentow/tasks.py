from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from obozstudentow.api.notifications import send_notification, UserFCMToken
from django.db.models import Q
from obozstudentow.models.workshop import Workshop


@shared_task
def send_workshop_notifications():
    NOTIFICATION_MINUTES = 15
    workshops = Workshop.objects.filter(
        notifications_sent=False,
        start__lte=timezone.now() + timedelta(minutes=NOTIFICATION_MINUTES),
        end__gt=timezone.now(),
    )
    for workshop in workshops:
        title = workshop.name
        minutes_until_start = int(
            (workshop.start - timezone.now()).total_seconds() / 60
        )
        if minutes_until_start < 0:
            continue
        message = f"Warsztaty rozpoczynają się za {minutes_until_start} minut."

        if workshop.location:
            message += f"\nLokalizacja: {workshop.location}"

        tokens = list(
            UserFCMToken.objects.filter(
                Q(user__in=workshop.workshopsignup_set.values_list("user", flat=True))
                | Q(user__in=workshop.workshopleader_set.values_list("user", flat=True))
            ).values_list("token", flat=True)
        )

        send_notification.delay(
            title=title,
            body=message,
            tokens=tokens,
            link=f"/warsztaty/info/{workshop.id}",
        )

        workshop.notifications_sent = True
        workshop.save()

    return f"Sent notifications for {workshops.count()} workshops."
