from django.db import models

# Create your models here.

from obozstudentow.models import User
class Message(models.Model):
    message = models.TextField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name + ': ' + self.message
    
class Chat(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User)
    
    def __str__(self):
        return self.name