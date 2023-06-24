from django.db import models
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
    description = models.TextField(null=True, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=100)
    photo = ResizedImageField(upload_to='schedule', blank=True)
    visible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Harmonogram"
        verbose_name_plural = "Harmonogram"

    def __str__(self):
        return self.name
    

class Bus(models.Model):
    description = models.CharField(max_length=100)
    location = models.URLField()

    class Meta:
        verbose_name_plural = "Busy"

    def __str__(self):
        return "Bus " + self.description



class Image(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Obrazki"
