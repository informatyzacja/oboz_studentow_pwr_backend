from django.db import models
from django.contrib.auth.models import AbstractUser

# Separate models

class Link(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    icon = models.URLField(blank=True)

    def __unicode__(self):
        return self.name
    
class FAQ(models.Model):
    question = models.CharField(max_length=100)
    answer = models.TextField()

    def __unicode__(self):
        return self.question
    
class ScheduleItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=100)
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name
    

class Bus(models.Model):
    description = models.CharField(max_length=100)
    location = models.URLField()

class User(AbstractUser):
    phoneNumber = models.CharField(max_length=9, blank=True)
    bandId = models.CharField(max_length=10, blank=True)
    houseNumber = models.CharField(max_length=10, blank=True)
    photo = models.ImageField(upload_to='users', blank=True) 
    title = models.CharField(max_length=100, blank=True) # e.g. "Koordynator"
    diet = models.CharField(max_length=100, blank=True) # e.g. "wegetariańska"
    


    def __unicode__(self):
        return self.first_name
    

    
