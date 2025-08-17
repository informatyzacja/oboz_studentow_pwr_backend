from .models import BerealNotification
from celery import shared_task

from django.db import transaction

from django.utils import timezone
import datetime


@shared_task
def schedule_today_prompt():
    """Ensure there's a notification object for today and schedule the send task.

    If a notification for today does not yet exist we create one with a random start
    window and then schedule the Celery task to fire exactly at the chosen "start"
    time. Previously this referenced a non-existent attribute (window_open_at), so
    we now combine today's date with the stored start TimeField to build an aware
    datetime for the ETA.
    """
    with transaction.atomic():
        now = timezone.now()
        today = now.date()
        obj, created = BerealNotification.objects.select_for_update().get_or_create(
            date=today, defaults=_random_window_for_today()
        )
        if created:
            eta = datetime.datetime.combine(today, obj.start)
            if timezone.is_naive(eta):
                eta = timezone.make_aware(eta, timezone.get_current_timezone())
            # Guard: if start time already passed (race right after midnight change), send immediately
            if timezone.is_naive(now):
                now = timezone.make_aware(now, timezone.get_current_timezone())
            if eta < now:
                eta = now
            send_daily_prompt.apply_async(eta=eta, kwargs={"prompt_id": obj.id})
        return str(obj), created


def _random_window_for_today():
    import random, datetime

    # Random start time between TIME_START and TIME_END
    TIME_START = 10  # 10:00
    TIME_END = 22  # 22:00
    minutes = random.randint(0, (TIME_END - TIME_START) * 60)
    base_dt = datetime.datetime.combine(
        timezone.now().date(), datetime.time(TIME_START, 0)
    )
    start_dt = base_dt + datetime.timedelta(minutes=minutes)

    # DEBUG - plan in 1 minute
    start_dt = timezone.now() + datetime.timedelta(minutes=1)
    # END DEBUG
    # deadline zostanie policzony dopiero przy wysyłaniu (send_daily_prompt)
    return {
        "start": start_dt.time(),
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_daily_prompt(self, prompt_id):
    with transaction.atomic():
        p = BerealNotification.objects.select_for_update().get(id=prompt_id)
        if p.is_sent:
            return
        try:
            # Ustal deadline dopiero teraz (np. 3 minuty od start), jeśli brak.
            if not p.deadline:
                start_dt = datetime.datetime.combine(p.date, p.start)
                if timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(
                        start_dt, timezone.get_current_timezone()
                    )
                deadline_dt = start_dt + datetime.timedelta(minutes=3)
                p.deadline = deadline_dt.time()
            # tu: pobierz aktywne urządzenia i wyślij batch push (FCM/APNs/WebPush)
            # send_push_to_all(...)
            p.is_sent = True
            p.sent_at = timezone.now()
            p.save(update_fields=["is_sent", "sent_at", "deadline"])
            print(f"Wysłano powiadomienie BeReal - {str(p)}")
        except Exception as e:
            self.retry(exc=e)
            print(f"Nie udało się wysłać powiadomienia BeReal - {str(p)}")
            return f"Nie udało się wysłać powiadomienia BeReal - {str(p)}"
        return f"Wysłano powiadomienie BeReal - {str(p)}"


@shared_task
def catch_up_prompts():
    """Find any unsent BeReal notifications whose window is currently active and send them.

    We look for today's BerealNotification
    rows where start <= now <= deadline and is_sent is False and enqueue the send task.
    Limited batch size to 50 just like previous implementation to avoid stampede.
    """
    now = timezone.now()
    current_time = now.time()
    qs = BerealNotification.objects.filter(
        date=now.date(),
        is_sent=False,
        start__lte=current_time,
    )[:50]
    dispatched = 0
    for n in qs:
        send_daily_prompt.delay(n.id)
        dispatched += 1
    return f"Dispatched {dispatched} pending BeReal notifications"
