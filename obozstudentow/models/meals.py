from django.db import models


class Meal(models.Model):
    camp = models.ForeignKey(
        "obozstudentow.Camp",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Obóz",
        db_index=True,
    )
    name = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        verbose_name = "Posiłek"
        verbose_name_plural = "Posiłki"

    def __str__(self):
        return self.name + " (" + str(self.start) + ")"


class MealValidation(models.Model):
    user = models.ForeignKey("obozstudentow.User", on_delete=models.CASCADE)
    meal = models.ForeignKey(Meal, on_delete=models.PROTECT)
    timeOfValidation = models.DateTimeField(auto_now_add=True)
    validatedBy = models.ForeignKey(
        "obozstudentow.User",
        on_delete=models.SET_NULL,
        related_name="meal_validations",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Walidacja posiłku"
        verbose_name_plural = "Walidacje posiłków"

    def __str__(self):
        return (
            self.user.first_name
            + " "
            + self.user.last_name
            + " ("
            + self.meal.name
            + ")"
        )
