
from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from ..models import User, UserFCMToken, GroupMember, GroupType

from .group import GroupWardenInline

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
        

@admin.action(description='Aktywuj')
def activate(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Dezaktywuj')
def deactivate(modeladmin, request, queryset):
    queryset.update(is_active=False)

class UserFCMTokenInline(admin.TabularInline):
    model = UserFCMToken
    extra = 0
    classes = ['collapse']

class Participant(User):
    class Meta:
        proxy = True
        verbose_name = 'Uczestnik'
        verbose_name_plural = 'Uczestnicy'

    

class ParticipantAdmin(ImportExportModelAdmin, UserAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(groups=None)

    def frakcja(self, user):
        groups = []
        for group in GroupMember.objects.filter(user=user, group__type=GroupType.objects.get(name='Frakcja')):
            groups.append(group.group.name)
        return ' '.join(groups)
    frakcja.short_description = 'Frakcja'

    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'is_active')
    search_fields = ('first_name', "email", 'last_name', 'title', 'phoneNumber', 'bandId', 'houseNumber', 'title')

    list_filter = ('bus', "is_active")
    ordering = ("last_name",'first_name')

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
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "houseNumber", "photo", "title", "diet", "bus", 'birthDate', 'freenow_code')}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    inlines = [GroupMemberInlineAdmin, GroupWardenInline, UserFCMTokenInline]
    actions = [activate, deactivate]

admin.site.register(Participant, ParticipantAdmin)


class Kadra(User):
    class Meta:
        proxy = True
        verbose_name = 'Kadrowicz'
        verbose_name_plural = 'Kadra'

class KadraAdmin(ParticipantAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(groups__name__in=['Kadra','Bajer'])
    
    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'title', 'is_active', 'has_image')
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "houseNumber", "photo", "title", "diet", "bus", 'birthDate', 'freenow_code')}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "groups",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    list_filter = ('groups', 'bus', "is_active")
    
admin.site.register(Kadra, KadraAdmin)
   
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    def frakcja(self, user):
        groups = []
        for group in GroupMember.objects.filter(user=user, group__type=GroupType.objects.get(name='Frakcja')):
            groups.append(group.group.name)
        return ' '.join(groups)
    frakcja.short_description = 'Frakcja'

    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'title', 'is_active', "is_staff", 'has_image')
    search_fields = ('first_name', "email", 'last_name', 'title', 'phoneNumber', 'bandId', 'houseNumber', 'title')

    list_filter = ("groups", 'bus', "is_staff", "is_active")
    ordering = ("last_name",'first_name')

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
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "houseNumber", "photo", "title", "diet", "bus", 'birthDate', 'freenow_code')}),
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
    inlines = [GroupMemberInlineAdmin, GroupWardenInline, UserFCMTokenInline]
    actions = [activate, deactivate]

admin.site.register(User, CustomUserAdmin)


class Sztab(User):
    class Meta:
        proxy = True
        verbose_name = 'Sztab'
        verbose_name_plural = 'Sztab'

class SztabAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(groups__name__in=['Sztab'])
    
admin.site.register(Sztab, SztabAdmin)

