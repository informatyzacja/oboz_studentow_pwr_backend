
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

@admin.action(description='Usuń opaski')
def remove_bands(modeladmin, request, queryset):
    queryset.update(bandId=None)

@admin.action(description='Stwórz opaski tymczasowe')
def create_temporary_bands(modeladmin, request, queryset):
    for user in queryset:
        if not user.bus and not user.bandId:
            user.bandId = str(200000+user.id)
            user.save()

class UserFCMTokenInline(admin.TabularInline):
    model = UserFCMToken
    extra = 0
    classes = ['collapse']

class Participant(User):
    class Meta:
        proxy = True
        verbose_name = 'Uczestnik'
        verbose_name_plural = 'Uczestnicy'

from django.contrib.auth.forms import UserChangeForm

class CustomUserChangeForm(UserChangeForm):
    
    def clean_bandId(self):
        bandId = self.cleaned_data['bandId']
        if bandId:
            bandId = bandId.zfill(6)
        return bandId

class ParticipantAdmin(ImportExportModelAdmin, UserAdmin):
    form = CustomUserChangeForm
    def get_queryset(self, request):
        return self.model.objects.filter(groups=None)

    def frakcja(self, user):
        groups = []
        for group in GroupMember.objects.filter(user=user, group__type=GroupType.objects.get(name='Frakcja')):
            groups.append(group.group.name)
        return ' '.join(groups)
    frakcja.short_description = 'Frakcja'

    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'is_active', 'has_house')
    search_fields = ('id', 'first_name', "email", 'last_name', 'title', 'phoneNumber', 'bandId', 'title', 'house__name')

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
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "photo", "title", "diet", "bus", 'birthDate', 'freenow_code', 'house')}),
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
    inlines = [GroupMemberInlineAdmin, UserFCMTokenInline]
    actions = [activate, deactivate, create_temporary_bands]



admin.site.register(Participant, ParticipantAdmin)


class Kadra(User):
    class Meta:
        proxy = True
        verbose_name = 'Kadrowicz'
        verbose_name_plural = 'Kadra'

class KadraAdmin(ParticipantAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(groups__name__in=['Kadra','Bajer','Fotograf'])
    
    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'title', 'is_active', 'has_image', 'has_house')
    
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "photo", "title", "diet", "bus", 'birthDate', 'freenow_code', 'house')}),
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

    actions = [activate, deactivate, remove_bands]
    inlines = [GroupMemberInlineAdmin, GroupWardenInline, UserFCMTokenInline]
    
admin.site.register(Kadra, KadraAdmin)
   
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    form = CustomUserChangeForm
    def frakcja(self, user):
        groups = []
        for group in GroupMember.objects.filter(user=user, group__type=GroupType.objects.get(name='Frakcja')):
            groups.append(group.group.name)
        return ' '.join(groups)
    frakcja.short_description = 'Frakcja'

    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'title', 'is_active', "is_staff", 'has_image')
    search_fields = ('id', 'first_name', "email", 'last_name', 'title', 'phoneNumber', 'bandId', 'title')

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
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "photo", "title", "diet", "bus", 'birthDate', 'freenow_code', 'house')}),
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
    
    actions = [activate, deactivate, remove_bands]
    
admin.site.register(Sztab, SztabAdmin)



from ..models import HouseCollocationForImport, House
from django.contrib import messages

@admin.action(description='Przypisz domki do uczestników')
def assign_houses(modeladmin, request, queryset):
    added = 0
    for house in queryset:
        try:
            user = User.objects.get(bandId=house.bandId.zfill(6))
            user.house = House.objects.get(name=house.house)
            user.save()
            house.delete()
            added += 1
        except User.DoesNotExist:
            messages.error(request, f'Nie znaleziono uczestnika z opaską {house.bandId}')
        except House.DoesNotExist:
            messages.error(request, f'Nie znaleziono domku {house.house}')

    messages.success(request, f'Przypisano {added} z {queryset.count()} domków')


@admin.register(HouseCollocationForImport)
class HouseCollocationForImportAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('house', 'bandId')
    list_per_page = 400

    actions = [assign_houses]