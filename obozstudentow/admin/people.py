from ..models import LifeGuard, SoberDuty, Staff, User, MealDuty

from django.contrib import admin
from orderable.admin import OrderableAdmin

@admin.register(LifeGuard)
class LifeGuardAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(LifeGuardAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].queryset = User.objects.filter(groups__name__in=('Ratownicy',))
        return form

@admin.register(SoberDuty)
class SoberDutyAdmin(admin.ModelAdmin):
    list_display = ('user', 'start', 'end')
    search_fields = ('user', 'start', 'end')

    def get_form(self, request, obj=None, **kwargs):
        form = super(SoberDutyAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].queryset = User.objects.filter(groups__name__in=('Kadra','Sztab'))
        return form
    

@admin.register(MealDuty)
class MealDutyAdmin(admin.ModelAdmin):
    list_display = ('user', 'start', 'end')
    search_fields = ('user', 'start', 'end')

    def get_form(self, request, obj=None, **kwargs):
        form = super(MealDutyAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].queryset = User.objects.filter(groups__name__in=('Kadra','Sztab'))
        return form

@admin.register(Staff)
class ContactAdmin(OrderableAdmin):
    list_display = ('user', 'sort_order_display')
    search_fields = ('user',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(ContactAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['user'].queryset = User.objects.filter(groups__name__in=('Sztab',))
        return form
    
        
