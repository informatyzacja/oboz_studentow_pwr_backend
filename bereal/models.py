from django.db import models
from django_resized import ResizedImageField
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class BerealPost(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bereal_posts"
    )
    photo1 = ResizedImageField(
        upload_to="bereal", force_format="JPEG", size=[1920, 1920]
    )
    photo2 = ResizedImageField(
        upload_to="bereal", force_format="JPEG", size=[1920, 1920]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    bereal_date = models.DateField()

    class Meta:
        verbose_name = "Post BeReal"
        verbose_name_plural = "Posty BeReal"
        unique_together = ["user", "bereal_date"]
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"BeReal {self.user.first_name} {self.user.last_name} - {self.bereal_date}"
        )


class BerealLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(BerealPost, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Like BeReal"
        verbose_name_plural = "Lajki BeReal"
        unique_together = ["user", "post"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.first_name} ❤️ {self.post.user.first_name}"


class BerealReport(models.Model):
    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bereal_reports_made"
    )
    post = models.ForeignKey(
        BerealPost, on_delete=models.CASCADE, related_name="reports"
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bereal_reports_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Zgłoszenie BeReal"
        verbose_name_plural = "Zgłoszenia BeReal"
        unique_together = ["reporter", "post"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Zgłoszenie: {self.post} przez {self.reporter.first_name}"


class BerealNotification(models.Model):
    date = models.DateField(db_index=True, unique=True)
    start = models.TimeField()
    deadline = models.TimeField(null=True, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Powiadomienie BeReal"
        verbose_name_plural = "Powiadomienia BeReal"
        ordering = ["-date"]

    def __str__(self):
        return f"BeReal {self.date} - {self.start.strftime('%H:%M')}"

    @property
    def start_at(self):
        """Pełna data+czas startu powiadomienia"""
        return datetime.combine(self.date, self.start).astimezone(
            timezone.get_current_timezone()
        )

    @property
    def deadline_at(self):
        """Pełna data+czas deadline (uwzględnia przejście po północy)"""
        if not self.deadline:
            return None
        dt = datetime.combine(self.date, self.deadline)
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
        # Jeśli deadline < start → znaczy, że okno przechodzi po północy
        if self.deadline <= self.start:
            dt += timedelta(days=1)
        return dt

    def is_active(self):
        """Czy okno BeReal jest aktywne między start a deadline"""
        now = timezone.now()
        if not self.is_sent or not self.deadline_at:
            return False
        return self.start_at <= now <= self.deadline_at
