from django.db import models

class LifeGuard(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
    
class SoberDuty(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.start.strftime("HH:MM dd.mm") + " - " + self.end.strftime("HH:MM dd.mm") + ")"
    

class Staff(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
    
