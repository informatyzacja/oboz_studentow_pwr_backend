from django.contrib import admin


from ..models import Workshop, WorkshopSignup, WorkshopLeader

class WorkshopSignupInline(admin.TabularInline):
    model = WorkshopSignup
    extra = 1
    classes = ['collapse']

class WorkshopLeaderInline(admin.TabularInline):
    model = WorkshopLeader
    extra = 1

@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('name', 'visible')
    search_fields = ('name', 'visible')
    inlines = [WorkshopLeaderInline, WorkshopSignupInline]