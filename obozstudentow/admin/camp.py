from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from ..models.camp import Camp, CampSettings, UserCamp
from .mixins import (
    SESSION_ACTIVE_CAMP_KEY,
    _get_active_camp,
    _get_user_owner_camps,
    _is_owner_of_any_camp,
)


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------


class UserCampInline(admin.TabularInline):
    model = UserCamp
    extra = 1
    autocomplete_fields = ["user"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # OWNERs can only manage members of their own camps
        return qs.filter(camp__in=_get_user_owner_camps(request.user))

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return _is_owner_of_any_camp(request.user)
        return _get_user_owner_camps(request.user).filter(pk=obj.pk).exists()

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


class CampSettingsInline(admin.StackedInline):
    model = CampSettings
    can_delete = False
    verbose_name_plural = "Ustawienia obozu"
    fieldsets = (
        (
            "Branding",
            {
                "fields": ("logo", "primary_color", "secondary_color"),
                "description": (
                    "Użyj wartości hex dla kolorów, np. #3b5bdb. "
                    "Logo zostanie przeskalowane do 400×400 px."
                ),
            },
        ),
        (
            "Feature flags",
            {
                "fields": (
                    "feature_workshops",
                    "feature_schedule",
                    "feature_tinder",
                    "feature_bereal",
                    "feature_bingo",
                    "feature_points",
                ),
            },
        ),
        (
            "Dodatkowa konfiguracja",
            {
                "fields": ("extra_config",),
                "classes": ("collapse",),
            },
        ),
    )


# ---------------------------------------------------------------------------
# CampAdmin
# ---------------------------------------------------------------------------


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "created_at",
        "member_count",
        "active_camp_button",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    inlines = [CampSettingsInline, UserCampInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user_camps__user=request.user, user_camps__role=UserCamp.Role.OWNER)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return _is_owner_of_any_camp(request.user)
        return _get_user_owner_camps(request.user).filter(pk=obj.pk).exists()

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False  # OWNERs cannot delete camps

    def has_add_permission(self, request):
        return True  # Any staff can create a camp (they become OWNER)

    def member_count(self, obj):
        return obj.user_camps.count()

    member_count.short_description = "Liczba członków"

    def active_camp_button(self, obj):
        url = reverse("admin:set-active-camp", args=[obj.pk])
        return format_html('<a class="button" href="{}">Ustaw aktywny</a>', url)

    active_camp_button.short_description = "Aktywny obóz"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:camp_id>/set-active/",
                self.admin_site.admin_view(self.set_active_camp_view),
                name="set-active-camp",
            ),
            path(
                "clear-active/",
                self.admin_site.admin_view(self.clear_active_camp_view),
                name="clear-active-camp",
            ),
        ]
        return custom + urls

    def set_active_camp_view(self, request, camp_id):
        """Store the selected camp_id in the session."""
        camp = Camp.objects.filter(pk=camp_id).first()
        if camp is None:
            self.message_user(request, "Nie znaleziono obozu.", level="error")
        elif not request.user.is_superuser and not _get_user_owner_camps(
            request.user
        ).filter(pk=camp_id).exists():
            self.message_user(
                request, "Nie masz dostępu do tego obozu.", level="error"
            )
        else:
            request.session[SESSION_ACTIVE_CAMP_KEY] = camp_id
            self.message_user(
                request,
                f"Aktywny obóz ustawiony na: {camp.name}",
                level="success",
            )
        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER", reverse("admin:obozstudentow_camp_changelist"))
        )

    def clear_active_camp_view(self, request):
        """Clear the active camp from the session."""
        request.session.pop(SESSION_ACTIVE_CAMP_KEY, None)
        self.message_user(request, "Aktywny obóz wyczyszczony.", level="success")
        return HttpResponseRedirect(reverse("admin:obozstudentow_camp_changelist"))


# ---------------------------------------------------------------------------
# UserCampAdmin
# ---------------------------------------------------------------------------


@admin.register(UserCamp)
class UserCampAdmin(admin.ModelAdmin):
    list_display = ("user", "camp", "role", "joined_at")
    list_filter = ("role", "camp")
    search_fields = ("user__email", "user__first_name", "user__last_name", "camp__name")
    autocomplete_fields = ["user", "camp"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(camp__in=_get_user_owner_camps(request.user))

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return _is_owner_of_any_camp(request.user)
        return _get_user_owner_camps(request.user).filter(pk=obj.camp_id).exists()

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return _is_owner_of_any_camp(request.user)
