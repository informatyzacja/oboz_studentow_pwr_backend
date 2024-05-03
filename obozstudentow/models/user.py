
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_resized import ResizedImageField
from .models import Bus

from django.contrib.auth.models import BaseUserManager
from django.contrib import admin

class UserManager(BaseUserManager):
    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        return user

class User(AbstractUser):
    username=None
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(max_length=12, blank=True, null=True)
    bandId = models.CharField(max_length=6, blank=True, null=True, unique=True)
    photo = ResizedImageField(upload_to='users', blank=True, null=True, force_format=None) 
    title = models.CharField(max_length=100, blank=True, null=True) # e.g. "Koordynator"
    diet = models.CharField(max_length=100, blank=True, null=True) # e.g. "wegetariańska"
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True)

    house = models.ForeignKey('House', on_delete=models.SET_NULL, null=True, blank=True)

    # poufne
    birthDate = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    ice_number = models.CharField(max_length=12, blank=True, null=True)
    additional_health_info = models.TextField(blank=True, null=True)
    pesel = models.CharField(max_length=11, blank=True, null=True)

    verification_code = models.IntegerField(null=True, blank=True)
    verification_code_valid_until_datetime = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.first_name + " " + self.last_name + (" " + self.title if self.title else "")
    
    @admin.display(
        boolean=True,
        description='Ma zdjęcie?',
    )
    def has_image(self):
        return bool(self.photo)
    
    @admin.display(
        boolean=True,
        description='Ma opaskę?',
    )
    def has_band(self):
        return bool(self.bandId)
    
    @admin.display(
        boolean=True,
        description='Ma domek?',
    )
    def has_house(self):
        return bool(self.house)

    class Meta:
        app_label = 'obozstudentow'

    def generate_bandId(self):
        from random import randint
        from django.db.models import Q
        while True:
            bandId = str(randint(0, 999999)).zfill(6)
            if not User.objects.filter(Q(bandId=bandId)).exists():
                return bandId

    def save(self, *args, **kwargs):
        if not self.bandId:
            self.bandId = self.generate_bandId()
        super(User, self).save(*args, **kwargs)
        
    
class UserFCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)


class TinderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    photo = ResizedImageField(upload_to='tinder', blank=True, null=True, force_format=None)

class TinderAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tinderaction_target')
    action = models.SmallIntegerField(choices=[(0, 'dislike'), (1, 'like'), (2, 'superlike')])
    date = models.DateTimeField(auto_now_add=True)