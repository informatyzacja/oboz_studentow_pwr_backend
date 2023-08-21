from django.db import models
from orderable.models import Orderable

class LifeGuard(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Ratownik"
        verbose_name_plural = "Ratownicy"

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
    
class SoberDuty(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        verbose_name = "Dyżur trzeźwości"
        verbose_name_plural = "Dyżury trzeźwości"
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.start.strftime("%H:%M %d.%m") + " - " + self.end.strftime("%H:%M %d.%m") + ")"
    

class Staff(Orderable):
    user = models.OneToOneField('obozstudentow.User', on_delete=models.CASCADE)

    class Meta(Orderable.Meta):
        verbose_name = "Kontakt do sztabu"
        verbose_name_plural = "Kontakty do sztabu"
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name
    
