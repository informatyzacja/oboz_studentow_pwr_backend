from django.test import TestCase, override_settings
from django.utils import timezone
from unittest.mock import patch
from .models import BerealNotification
from . import tasks
import datetime


class BerealTasksTests(TestCase):
    def test_schedule_today_prompt_creates_and_schedules(self):
        self.assertEqual(BerealNotification.objects.count(), 0)
        with patch("bereal.tasks.send_daily_prompt.apply_async") as mock_async:
            tasks.schedule_today_prompt()
            self.assertEqual(BerealNotification.objects.count(), 1)
            obj = BerealNotification.objects.first()
            mock_async.assert_called_once()
            kwargs = mock_async.call_args.kwargs
            self.assertEqual(kwargs["kwargs"]["prompt_id"], obj.id)
            eta = kwargs["eta"]
            self.assertIsNotNone(eta)
            self.assertEqual(eta.date(), timezone.now().date())
            # Just validate eta time matches chosen start or (if already past) within same minute as now
            chosen_time = obj.start
            eta_time = eta.time()
            now = timezone.now()
            if chosen_time < (now - datetime.timedelta(minutes=1)).time():
                # If chosen time clearly earlier than a minute ago, expect eta near now
                self.assertTrue(abs(now.minute - eta_time.minute) <= 1)
            else:
                self.assertEqual(eta_time, chosen_time)

    def test_schedule_today_prompt_idempotent(self):
        with patch("bereal.tasks.send_daily_prompt.apply_async") as mock_async:
            tasks.schedule_today_prompt()
            tasks.schedule_today_prompt()  # second call should not schedule again
            self.assertEqual(mock_async.call_count, 1)
            self.assertEqual(BerealNotification.objects.count(), 1)

    def test_send_daily_prompt_marks_sent(self):
        # Create object manually so we control times
        now = timezone.now()
        obj = BerealNotification.objects.create(
            date=now.date(),
            start=(now - datetime.timedelta(minutes=1)).time(),
        )
        self.assertFalse(obj.is_sent)
        tasks.send_daily_prompt(obj.id)
        obj.refresh_from_db()
        self.assertTrue(obj.is_sent)
        self.assertIsNotNone(obj.sent_at)

    def test_send_daily_prompt_no_duplicate(self):
        now = timezone.now()
        obj = BerealNotification.objects.create(
            date=now.date(),
            start=(now - datetime.timedelta(minutes=1)).time(),
            is_sent=True,
            sent_at=now,
        )
        # Should simply exit without changing sent_at
        prev_sent_at = obj.sent_at
        tasks.send_daily_prompt(obj.id)
        obj.refresh_from_db()
        self.assertEqual(obj.sent_at, prev_sent_at)
