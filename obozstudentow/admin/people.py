from ..models import LifeGuard, SoberDuty, Staff

from django.contrib import admin

@admin.register(LifeGuard)
class LifeGuardAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user',)

@admin.register(SoberDuty)
class SoberDutyAdmin(admin.ModelAdmin):
    list_display = ('user', 'start', 'end')
    search_fields = ('user', 'start', 'end')

@admin.register(Staff)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user',)
