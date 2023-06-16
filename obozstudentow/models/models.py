from django.db import models
from django.contrib.auth.models import AbstractUser
from django_resized import ResizedImageField

# Separate models

class Link(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    icon = ResizedImageField(upload_to='links', blank=True, force_format=None)

    def __str__(self):
        return self.name
    
class FAQ(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField()

    def __str__(self):
        return self.question
    
class ScheduleItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=100)
    photo = ResizedImageField(upload_to='schedule', blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

class Bus(models.Model):
    description = models.CharField(max_length=100)
    location = models.URLField()

    class Meta:
        verbose_name_plural = "Buses"

    def __str__(self):
        return "Bus " + self.description

class User(AbstractUser):
    username=None
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(max_length=9, blank=True)
    bandId = models.CharField(max_length=10, blank=True)
    houseNumber = models.CharField(max_length=10, blank=True)
    photo = ResizedImageField(upload_to='users', blank=True) 
    title = models.CharField(max_length=100, blank=True) # e.g. "Koordynator"
    diet = models.CharField(max_length=100, blank=True) # e.g. "wegetariańska"
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    def __str__(self):
        return self.first_name + " " + self.last_name + " " + self.title
    

    
