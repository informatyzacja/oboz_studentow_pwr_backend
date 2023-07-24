from django.db import models
from django_resized import ResizedImageField

class Workshop(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=100)
    visible = models.BooleanField(default=True)
    signupsOpen = models.BooleanField(default=False)
    signupsOpenTime = models.DateTimeField(blank=True, null=True)
    photo = ResizedImageField(upload_to='workshop', blank=True)
    userLimit = models.IntegerField()
    itemsToTake = models.TextField(blank=True)

    class Meta:
        verbose_name = "Warsztat"
        verbose_name_plural = "Warsztaty"

    def __str__(self):
        return self.name
    

class WorkshopSignup(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Zapis na warsztaty"
        verbose_name_plural = "Zapisy na warsztaty"

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.workshop.name + ")"
    
class WorkshopLeader(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.PROTECT)
    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = "Prowadzący warsztaty"
        verbose_name_plural = "Prowadzący warsztaty"

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.workshop.name + ")"