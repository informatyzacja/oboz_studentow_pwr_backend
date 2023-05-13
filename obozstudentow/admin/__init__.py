from .group import *
from .meals import *
from .people import *
from .workshop import *


from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from ..models import Link, FAQ, ScheduleItem, User

class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon')
    search_fields = ('name', 'url', 'icon')

class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')

class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'start', 'end', 'location', 'visible')
    search_fields = ('name', 'description', 'start', 'end', 'location', 'visible')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', "email", 'first_name', 'last_name', 'phoneNumber', 'bandId', "is_staff")
    search_fields = ('username', 'first_name', "email", 'last_name', 'phoneNumber', 'bandId', 'houseNumber')

    list_filter = ("is_staff", "is_superuser", "is_active", "groups")


    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Additional info"), {"fields": ("phoneNumber", "bandId", "houseNumber", "photo", "title", "diet", "bus")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

admin.site.register(Link, LinkAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(ScheduleItem, ScheduleItemAdmin)
admin.site.register(User, CustomUserAdmin)


from ..models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'date', 'addedBy', 'group', 'visible')
    search_fields = ('title', 'content', 'date', 'addedBy', 'group', 'visible')


from ..models import Bus

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('description', 'location')
    search_fields = ('description', 'location')
