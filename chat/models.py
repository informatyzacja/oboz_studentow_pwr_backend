from django.db import models

# Create your models here.

from obozstudentow.models import User
class Message(models.Model):
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    group_name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name + ': ' + self.message