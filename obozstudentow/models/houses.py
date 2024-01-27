from django.db import models

class House(models.Model):
    name = models.CharField(max_length=10, verbose_name="Numer pokoju", unique=True)
    key_collected = models.BooleanField(default=False, verbose_name="Klucz odebrany")
    places = models.SmallIntegerField(default=0, verbose_name="Liczba miejsc")
    floor = models.CharField(max_length=50, default=None, verbose_name="Piętro", blank=True, null=True)

    def __str__(self):
        return 'Pokój nr ' + self.name
    
    def locators(self):
        return self.user_set.count()
    locators.short_description = 'Lokatorzy'

    def full(self):
        return self.locators() >= self.places
    full.short_description = 'Pełny'
    full.boolean = True

    class Meta:
        verbose_name = "Pokój"
        verbose_name_plural = "Pokoje"

class HouseCollocationForImport(models.Model):
    house = models.CharField(max_length=10)
    bandId = models.CharField(max_length=6, blank=True, null=True, unique=True)


class HouseSignupProgress(models.Model):
    house = models.OneToOneField(House, on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Ostatnia aktualizacja")

    def seconds_until_free(self):
        from django.utils import timezone
        return max(0, ((timezone.timedelta(seconds=60) + self.last_updated) - timezone.now()).total_seconds())
    
    def free(self):
        return self.user is None or self.seconds_until_free() == 0

