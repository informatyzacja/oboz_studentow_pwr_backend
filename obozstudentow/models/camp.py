from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_resized import ResizedImageField


class Camp(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa obozu")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")

    class Meta:
        verbose_name = "Obóz"
        verbose_name_plural = "Obozy"
        app_label = "obozstudentow"

    def __str__(self):
        return self.name


class CampSettings(models.Model):
    """Per-camp configuration: branding and feature flags."""

    camp = models.OneToOneField(
        Camp,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name="Obóz",
    )

    # Branding
    logo = ResizedImageField(
        upload_to="camps/logos",
        blank=True,
        null=True,
        force_format=None,
        size=[400, 400],
        verbose_name="Logo obozu",
    )
    primary_color = models.CharField(
        max_length=7, default="#3b5bdb", verbose_name="Kolor główny (hex)"
    )
    secondary_color = models.CharField(
        max_length=7, default="#ffffff", verbose_name="Kolor dodatkowy (hex)"
    )

    # Feature flags
    feature_workshops = models.BooleanField(default=True, verbose_name="Warsztaty")
    feature_schedule = models.BooleanField(default=True, verbose_name="Harmonogram")
    feature_tinder = models.BooleanField(default=True, verbose_name="Tinder")
    feature_bereal = models.BooleanField(default=True, verbose_name="BeReal")
    feature_bingo = models.BooleanField(default=True, verbose_name="Bingo")
    feature_points = models.BooleanField(default=True, verbose_name="Punkty")

    # Extra extensible config
    extra_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dodatkowa konfiguracja (JSON)",
    )

    class Meta:
        verbose_name = "Ustawienia obozu"
        verbose_name_plural = "Ustawienia obozów"
        app_label = "obozstudentow"

    def __str__(self):
        return f"Ustawienia: {self.camp.name}"


@receiver(post_save, sender=Camp)
def create_camp_settings(sender, instance, created, **kwargs):
    """Automatically create CampSettings for every new Camp."""
    if created:
        CampSettings.objects.get_or_create(camp=instance)


class UserCamp(models.Model):
    """Many-to-many through-table between User and Camp, carrying the user's role."""

    class Role(models.TextChoices):
        OWNER = "owner", "Właściciel"
        MEMBER = "member", "Uczestnik"

    user = models.ForeignKey(
        "obozstudentow.User",
        on_delete=models.CASCADE,
        related_name="user_camps",
        verbose_name="Użytkownik",
    )
    camp = models.ForeignKey(
        Camp,
        on_delete=models.CASCADE,
        related_name="user_camps",
        verbose_name="Obóz",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name="Rola",
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dołączenia")

    class Meta:
        verbose_name = "Członkostwo w obozie"
        verbose_name_plural = "Członkostwa w obozie"
        unique_together = [["user", "camp"]]
        app_label = "obozstudentow"
        indexes = [
            models.Index(fields=["user", "camp"]),
            models.Index(fields=["camp"]),
        ]

    def __str__(self):
        return f"{self.user} – {self.camp} ({self.get_role_display()})"
