
from django.contrib import admin

from ..models import Meal, MealValidation

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'start', 'end')

    ordering = ('-start',)

@admin.register(MealValidation)
class MealValidationAdmin(admin.ModelAdmin):
    pass
