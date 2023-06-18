
from django.contrib import admin

from ..models import Meal, MealValidation, MealType

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'type')

@admin.register(MealValidation)
class MealValidationAdmin(admin.ModelAdmin):
    pass

@admin.register(MealType)
class MealTypeAdmin(admin.ModelAdmin):
    pass