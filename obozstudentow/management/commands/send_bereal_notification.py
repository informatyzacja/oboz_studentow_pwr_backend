from django.core.management.base import BaseCommand
from django.utils import timezone
from obozstudentow.models import BeerealNotification, UserFCMToken, Setting
from obozstudentow.api.notifications import send_notification
import random
from datetime import timedelta


class Command(BaseCommand):
    help = "Send BeReal notification at random time"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force send notification even if one was already sent today",
        )

    def handle(self, *args, **options):
        try:
            # Check if BeReal is enabled
            bereal_active = (
                Setting.objects.get(name="bereal_active").value.lower() == "true"
            )
            if not bereal_active:
                self.stdout.write(self.style.WARNING("BeReal is disabled"))
                return
        except Setting.DoesNotExist:
            self.stdout.write(self.style.ERROR("BeReal settings not found"))
            return

        today = timezone.now().date()

        # Check if notification was already sent today
        if (
            BeerealNotification.objects.filter(date=today).exists()
            and not options["force"]
        ):
            self.stdout.write(
                self.style.WARNING("BeReal notification already sent today")
            )
            return

        # Create notification with random deadline (2-3 hours from now)
        deadline_hours = random.uniform(2, 3)
        deadline = timezone.now() + timedelta(hours=deadline_hours)

        notification = BeerealNotification.objects.create(date=today, deadline=deadline)

        # Get all user FCM tokens
        tokens = list(
            UserFCMToken.objects.filter(user__notifications=True).values_list(
                "token", flat=True
            )
        )

        if not tokens:
            self.stdout.write(self.style.WARNING("No FCM tokens found"))
            return

        # Send notification
        title = "⚡ BeReal! ⚡"
        body = "Czas na dzisiejsze BeReal! Masz ograniczony czas na przesłanie zdjęcia."

        try:
            response = send_notification(title, body, tokens)
            success_count = response.success_count
            failure_count = response.failure_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"BeReal notification sent successfully! "
                    f"Success: {success_count}, Failures: {failure_count}"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to send notifications: {str(e)}")
            )
