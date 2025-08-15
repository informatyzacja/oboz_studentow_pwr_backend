from django.db import models
from django_resized import ResizedImageField
from django.conf import settings


class TinderProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    photo = ResizedImageField(
        upload_to="tinder", blank=True, null=True, force_format=None
    )
    super_like_used = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tinder profile"
        verbose_name_plural = "Tinder profiles"


class TinderAction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tinderaction_target",
    )
    action = models.SmallIntegerField(
        choices=[(0, "dislike"), (1, "like"), (2, "superlike")]
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tinder action"
        verbose_name_plural = "Tinder actions"
