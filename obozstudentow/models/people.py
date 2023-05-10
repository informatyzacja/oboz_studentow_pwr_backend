from django.db import models

class LifeGuard(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)

    def __unicode__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.group.name + ")"
    
class SoberDuty(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    
    def __unicode__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.start + " - " + self.end + ")"
    

class Contact(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    
    def __unicode__(self):
        return self.user.first_name + " " + self.user.last_name
    
