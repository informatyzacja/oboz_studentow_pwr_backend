from django.db import models
from django_resized import ResizedImageField
from django.contrib import admin


class Workshop(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=100, blank=True, null=True)
    visible = models.BooleanField(default=True)
    signupsOpen = models.BooleanField(default=False)
    signupsOpenTime = models.DateTimeField(blank=True, null=True)
    photo = ResizedImageField(upload_to="workshop", blank=True)
    userLimit = models.IntegerField()
    itemsToTake = models.TextField(blank=True, null=True)
    notifications_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Warsztat"
        verbose_name_plural = "Warsztaty"

    def __str__(self):
        return self.name

    @admin.display(
        boolean=True,
        description="Ma zdjęcie?",
    )
    def has_image(self):
        return bool(self.photo)


class WorkshopSignup(models.Model):
    user = models.ForeignKey("obozstudentow.User", on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Zapis na warsztaty"
        verbose_name_plural = "Zapisy na warsztaty"

    def __str__(self):
        return (
            self.user.first_name
            + " "
            + self.user.last_name
            + " ("
            + self.workshop.name
            + ")"
        )


class WorkshopLeader(models.Model):
    user = models.ForeignKey("obozstudentow.User", on_delete=models.PROTECT)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Prowadzący warsztaty"
        verbose_name_plural = "Prowadzący warsztaty"

    def __str__(self):
        return (
            self.user.first_name
            + " "
            + self.user.last_name
            + " ("
            + self.workshop.name
            + ")"
        )
