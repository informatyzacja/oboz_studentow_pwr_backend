from django.contrib import admin

from ..models import Meal, MealValidation


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start", "end", "mealvalidation__count")

    ordering = ("start", "end")

    def mealvalidation__count(self, obj):
        return obj.mealvalidation_set.count()

    mealvalidation__count.short_description = "Ilość zatwierdzonych"


@admin.register(MealValidation)
class MealValidationAdmin(admin.ModelAdmin):
    pass
