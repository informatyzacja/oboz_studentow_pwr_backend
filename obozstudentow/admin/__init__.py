from .group import *
from .meals import *
from .people import *
from .workshop import *

from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from ..models import Link, FAQ, ScheduleItem, User, Icons

class LinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'icon')
    search_fields = ('name', 'url', 'icon')

class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')

class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'start', 'end', 'location', 'visible')
    search_fields = ('name', 'description', 'start', 'end', 'location', 'visible')

@admin.register(Icons)
class IconsAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name', 'icon')

class GroupMemberInlineAdmin(admin.TabularInline):
    model = GroupMember
    extra = 1

from django.contrib.auth.forms import BaseUserCreationForm
from django.core.exceptions import ValidationError

class UserCreationFormEmail(BaseUserCreationForm):
    password1 = None
    password2 = None

    def save(self, commit=True):
        user = super(BaseUserCreationForm, self).save(commit=False)
        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user

    def clean_email(self):
        """Reject usernames that differ only in case."""
        email = self.cleaned_data.get("email")
        if (
            email
            and self._meta.model.objects.filter(email__iexact=email).exists()
        ):
            self._update_errors(
                ValidationError(
                    {
                        "email": self.instance.unique_error_message(
                            self._meta.model, ["email"]
                        )
                    }
                )
            )
        else:
            return email
        
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    list_display = ("email", 'first_name', 'last_name', 'phoneNumber', 'bandId', "is_staff")
    search_fields = ('first_name', "email", 'last_name', 'phoneNumber', 'bandId', 'houseNumber')

    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    ordering = ("email",)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name"),
            },
        ),
    )
    add_form = UserCreationFormEmail


    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "houseNumber", "photo", "title", "diet", "bus")}),
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
    inlines = [GroupMemberInlineAdmin, GroupWardenInline]

admin.site.register(Link, LinkAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(ScheduleItem, ScheduleItemAdmin)
admin.site.register(User, CustomUserAdmin)


from ..models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'date', 'addedBy', 'group', 'visible')
    search_fields = ('title', 'content', 'date', 'addedBy', 'group', 'visible')

from ..models import DailyQuest

@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'finish', 'addedBy', 'group', 'visible')
    search_fields = ('title', 'description', 'finish', 'addedBy', 'group', 'visible')


from ..models import Bus

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('description', 'location')
    search_fields = ('description', 'location')


from ..models import Image
@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'image')
    search_fields = ('name', 'image')


from ..models import Setting
@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')
    search_fields = ('name', 'value')