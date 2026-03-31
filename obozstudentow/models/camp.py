from django.db import models


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


class UserCamp(models.Model):
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
