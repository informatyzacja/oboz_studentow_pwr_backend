from django.db import models
from obozstudentow_async.models import Chat

class House(models.Model):
    name = models.CharField(max_length=10, verbose_name="Numer domku/pokoju", unique=True)
    key_collected = models.BooleanField(default=False, verbose_name="Klucz odebrany")
    user_key_collected = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kto odebrał klucz", related_name='user_key_collected')
    places = models.SmallIntegerField(default=0, verbose_name="Liczba miejsc")
    floor = models.CharField(max_length=50, default=None, verbose_name="Piętro", blank=True, null=True)
    description = models.TextField(default=None, verbose_name="Opis", blank=True, null=True)
    signup_open = models.BooleanField(default=True, verbose_name="Czy można się zapisać?")
    signout_open = models.BooleanField(default=True, verbose_name="Czy można się wypisać?")

    chat = models.ForeignKey(Chat, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Czat")

    def __str__(self):
        return 'Pokój/domek nr ' + self.name
    
    def locators(self):
        return self.user_set.count()
    locators.short_description = 'Lokatorzy'

    def full(self):
        return self.locators() >= self.places
    full.short_description = 'Pełny'
    full.boolean = True

    class Meta:
        verbose_name = "Pokój/domek"
        verbose_name_plural = "Pokoje/domki"

    def save(self, *args, **kwargs):
        if self.places < 0:
            self.places = 0
        if self.user_key_collected:
            self.key_collected = True
        super().save(*args, **kwargs)
        if not self.chat:
            self.chat = Chat.objects.create(name='Czat domku nr ' + self.name)
            self.chat.users.set(self.user_set.all())
            self.save()


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

