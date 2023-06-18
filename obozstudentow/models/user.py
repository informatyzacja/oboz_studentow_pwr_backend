
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_resized import ResizedImageField
from .models import Bus

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
    
