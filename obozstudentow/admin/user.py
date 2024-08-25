
from django.http import HttpRequest

from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.db.models import F
from ..models import User, UserFCMToken, GroupMember, GroupType, TinderProfile
from ..models import Group as ObozGroup

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

    def validate_passwords(self):
        pass

    def clean_email(self):
        """Reject emails that differ only in case."""
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
    queryset.update(bandId=200000 + F('id'))

@admin.action(description='Usuń opaski tymczasowe')
def remove_temporary_bands(modeladmin, request, queryset):
    queryset.filter(bandId = 200000 + F('id')).update(bandId=None)

class UserFCMTokenInline(admin.TabularInline):
    model = UserFCMToken
    extra = 0
    classes = ['collapse']

class TinderProfileInline(admin.TabularInline):
    model = TinderProfile
    extra = 0
    classes = ['collapse']

    # def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
    #     return False
    
    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

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

from ..models import Bus
class ParticipantResource(resources.ModelResource):
    bus = fields.Field(
        column_name='bus', 
        attribute='bus', 
        widget=ForeignKeyWidget(Bus, 'description')
    )



    def after_import_row(self, row, row_result, **kwargs):
        frakcja_name = row.get('frakcja', None)
        if frakcja_name and row_result.instance:
            group_type, created = GroupType.objects.get_or_create(name='Frakcja')
            frakcja, created = ObozGroup.objects.get_or_create(name=frakcja_name, type=group_type)
            GroupMember.objects.create(user=row_result.instance, group=frakcja)




    # frakcja = fields.Field(
    #     column_name='frakcja',
    #     attribute='groupmember_set',
    #     widget=ManyToManyWidget(ObozGroup, field='name'),
    #     m2m_add=True
    # )
    
    # def before_save_instance(self, instance, row, **kwargs):
    #     print(kwargs)

    
    class Meta:
        model = Participant
        fields = ('id', 'first_name', 'last_name', 'email', 'pesel', 'ice_number', 'diet', 'phoneNumber', 'bus', 'additional_health_info', 'frakcja')

class ParticipantAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = ParticipantResource
    form = CustomUserChangeForm

    def frakcja(self, user):
        groups = []
        for group in GroupMember.objects.filter(user=user, group__type=GroupType.objects.get(name='Frakcja')):
            groups.append(group.group.name)
        return ' '.join(groups)
    frakcja.short_description = 'Frakcja'

    def registered(self, user):
        return user.last_login is not None
    registered.short_description = 'Zarejestrowany'
    registered.boolean = True

    def push_notifications_registered(self, user):
        return user.notifications
    push_notifications_registered.short_description = 'Powiadomienia'
    push_notifications_registered.boolean = True

    def has_tinder_profile(self, user):
        return bool(user.tinderprofile)
    has_tinder_profile.short_description = 'Tinder'
    has_tinder_profile.boolean = True
    

    list_display = ('id', "email", 'first_name', 'last_name', 'bandId', 'frakcja', 'is_active', 'has_house', 'registered', 'push_notifications_registered', 'has_tinder_profile')
    search_fields = ('id', 'first_name', "email", 'last_name', 'title', 'phoneNumber', 'bandId', 'title', 'house__name')

    list_filter = ('bus', "is_active", 'groups')
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
        (_("Podstawowe informacje"), {"fields": ("first_name", "last_name", "email")}),
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "photo", "title", "bus", "bus_info", 'house')}),
        (
            _("Aktywny"),
            {
                "fields": (
                    "is_active",
                ),
                'classes': ('collapse',),
            },
        ),
        ("Poufne informacje", {
            "fields": (
                 "diet", 'birthDate', 'ice_number', 'additional_health_info', 'pesel'
            ),
            'classes': ('collapse',),
        }),
        (_("Ważne daty"), {"fields": ("last_login", "date_joined")}),
        ("Hasło", {
            "fields": ("password",),
            'classes': ('collapse',),
        }),
    )
    inlines = [GroupMemberInlineAdmin, TinderProfileInline, UserFCMTokenInline]
    actions = [activate, deactivate, create_temporary_bands, remove_temporary_bands]
    readonly_fields = ('last_login', 'date_joined')



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
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "photo", "title", "diet", "bus", "bus_info", 'birthDate', 'house')}),
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
        ("Dodatkowe informacje", {"fields": ("phoneNumber", "bandId", "photo", "title", "diet", "bus", "bus_info", 'house')}),
        ("Poufne informacje", {"fields": ('birthDate', 'ice_number', 'additional_health_info', 'gender', 'pesel'), 'classes': ('collapse',)}),
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


class ZdjeciaKadra(User):
    class Meta:
        proxy = True
        verbose_name = 'Zdjęcia Kadra'
        verbose_name_plural = 'Zdjęcia Kadra'

@admin.register(ZdjeciaKadra)
class ZdjeciaKadraAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'has_image', 'title')

    list_filter = ("groups",)

    fields = ('first_name', 'last_name', 'title', 'photo')
    fieldsets = None
    readonly_fields = ('first_name', 'last_name', 'title')

    def get_queryset(self, request):
        return self.model.objects.filter(groups__name__in=['Sztab','Kadra','Bajer'])
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
    
    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
    


class Opaski(User):
    class Meta:
        proxy = True
        verbose_name = 'Opaski'
        verbose_name_plural = 'Opaski'

@admin.register(Opaski)
class OpaskiAdmin(CustomUserAdmin):
    actions = [create_temporary_bands, remove_temporary_bands]

    list_display = ('first_name', 'last_name', 'bandId', 'bus')

    list_filter = ('bus',)

    search_fields = ('first_name', 'last_name', 'bandId', 'bus__name')

    fieldsets = (
        (None, {"fields": ("bandId",)}),
        ("Informacje", {"fields": ("bus",)}),
    )

    readonly_fields = ('bus', )

    inlines = []

    def has_delete_permission(self, *args, **kwargs) -> bool:
        return False
    


from django.contrib.auth.models import Group

class DjangoGroup(Group):
    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name = 'Grupa'
        verbose_name_plural = 'Grupy'


admin.site.unregister(Group)

@admin.register(DjangoGroup)
class CustomGroupAdmin(GroupAdmin):
    list_display = ('id','name')