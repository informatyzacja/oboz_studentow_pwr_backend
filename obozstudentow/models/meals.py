from django.db import models

class MealType(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name
    
class Meal(models.Model):
    type = models.ForeignKey(MealType, on_delete=models.PROTECT)
    date = models.DateField()

    def __unicode__(self):
        return self.type.name + " (" + str(self.date) + ")"
    
class MealValidation(models.Model):
    user = models.ForeignKey('obozstudentow.User', on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.PROTECT)
    timeOfValidation = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.user.first_name + " " + self.user.last_name + " (" + self.meal.type.name + ")"