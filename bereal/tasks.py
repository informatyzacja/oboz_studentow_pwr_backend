from .models import BerealNotification
from celery import shared_task

from django.db import transaction

from django.utils import timezone
import datetime
from obozstudentow.models import UserFCMToken
from obozstudentow.api.notifications import send_notification


def _get_setting_int(name: str, default: int) -> int:
    """Fetch integer setting value or return default on any error.

    We import Setting lazily to avoid any potential circular imports at worker startup.
    """
    try:
        from obozstudentow.models import Setting  # local import

        value = (
            Setting.objects.filter(name=name).values_list("value", flat=True).first()
        )
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


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
    import random
    import datetime

    # Pull configuration from settings (fallback to defaults if missing / invalid)
    time_start = _get_setting_int("bereal_time_start", 10)  # hour 0-23
    time_end = _get_setting_int("bereal_time_end", 22)  # hour 1-23

    # Basic validation / normalization
    if not (0 <= time_start <= 23):
        time_start = 10
    if not (0 <= time_end <= 23):
        time_end = 22
    if time_end <= time_start:  # fallback to defaults if misconfigured
        time_start, time_end = 10, 22

    minutes = random.randint(0, (time_end - time_start) * 60)
    base_dt = datetime.datetime.combine(
        timezone.now().date(), datetime.time(time_start, 0)
    )
    start_dt = base_dt + datetime.timedelta(minutes=minutes)

    # deadline zostanie policzony dopiero przy wysyłaniu (send_daily_prompt)
    return {"start": start_dt.time()}


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
                deadline_minutes = _get_setting_int("bereal_deadline_minutes", 3)
                if deadline_minutes < 1:
                    deadline_minutes = 3
                deadline_dt = start_dt + datetime.timedelta(minutes=deadline_minutes)
                p.deadline = deadline_dt.time()

            tokens = UserFCMToken.objects.filter(user__notifications=True).values_list(
                "token", flat=True
            )
            send_notification.delay(
                title="It's time to BeerReal!",
                body="Pora na Twoje codzienne BeerReal!",
                tokens=tokens,
                link="/bereal/home/",
            )

            p.is_sent = True
            p.sent_at = timezone.now()
            p.save(update_fields=["is_sent", "sent_at", "deadline"])
            print(f"Wysłano powiadomienie BeReal - {str(p)}")
        except Exception as e:
            self.retry(exc=e)
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
