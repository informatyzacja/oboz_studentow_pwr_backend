from django.db import models

class MealType(models.Model):
    name = models.CharField(max_length=100)
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        verbose_name = "Rodzaj posiłku"
        verbose_name_plural = "Rodzaje posiłków"

    def __str__(self):
        return self.name
    
class Meal(models.Model):
    type = models.ForeignKey(MealType, on_delete=models.PROTECT)
    date = models.DateField()

    class Meta:
        verbose_name = "Posiłek"
        verbose_name_plural = "Posiłki"

    def __str__(self):
        return self.type.name + " (" + str(self.date) + ")"
    
class MealValidation(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.PROTECT)
    timeOfValidation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Walidacja posiłku"
        verbose_name_plural = "Walidacje posiłków"
    
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.meal.type.name + ")"