"""
Admin mixins for multi-camp isolation.

Usage:
    @admin.register(MyModel)
    class MyModelAdmin(CampScopedAdmin, admin.ModelAdmin):
        ...

Rules:
- superuser → sees all data
- OWNER     → sees only data belonging to their owned camps; also filters by the
              "active camp" stored in the session when present
- MEMBER    → no admin access (has_module_perms returns False)
"""
from __future__ import annotations

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models.camp import Camp, UserCamp

SESSION_ACTIVE_CAMP_KEY = "admin_active_camp_id"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_user_owner_camps(user):
    """Return a queryset of Camps where *user* is OWNER."""
    return Camp.objects.filter(
        user_camps__user=user, user_camps__role=UserCamp.Role.OWNER
    )


def _get_active_camp(request):
    """
    Return the currently selected Camp from session, or None.

    If the stored camp_id is no longer valid for the user, clears the session
    key and returns None.
    """
    camp_id = request.session.get(SESSION_ACTIVE_CAMP_KEY)
    if not camp_id:
        return None
    # Superusers may have any camp active
    if request.user.is_superuser:
        return Camp.objects.filter(pk=camp_id).first()
    # For OWNERs verify the camp is still theirs
    camp = _get_user_owner_camps(request.user).filter(pk=camp_id).first()
    if not camp:
        del request.session[SESSION_ACTIVE_CAMP_KEY]
        return None
    return camp


def _is_owner_of_any_camp(user):
    return UserCamp.objects.filter(user=user, role=UserCamp.Role.OWNER).exists()


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------


class CampScopedAdmin:
    """
    Mixin for ModelAdmin classes whose model has a ``camp`` ForeignKey.

    - Superusers see everything.
    - OWNERs see only records belonging to their own camps (filtered further by
      the active camp when one is selected in the session).
    - MEMBERs have no admin access.
    """

    # Name of the FK field on the model pointing to Camp
    camp_field: str = "camp"

    # ------------------------------------------------------------------
    # Access control
    # ------------------------------------------------------------------

    def has_module_perms(self, request):
        if request.user.is_superuser:
            return True
        return _is_owner_of_any_camp(request.user)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not _is_owner_of_any_camp(request.user):
            return False
        if obj is not None:
            obj_camp = getattr(obj, self.camp_field, None)
            if obj_camp is None:
                return True
            return _get_user_owner_camps(request.user).filter(pk=obj_camp.pk).exists()
        return True

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return _is_owner_of_any_camp(request.user)

    # ------------------------------------------------------------------
    # Queryset isolation
    # ------------------------------------------------------------------

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter to the user's owned camps
        owned_camps = _get_user_owner_camps(request.user)
        # Optionally narrow to active camp
        active_camp = _get_active_camp(request)
        if active_camp and owned_camps.filter(pk=active_camp.pk).exists():
            return qs.filter(**{self.camp_field: active_camp})
        return qs.filter(**{f"{self.camp_field}__in": owned_camps})

    # ------------------------------------------------------------------
    # Auto-assign camp on save
    # ------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            # Auto-assign the active camp (or the first owned camp) on create
            camp = _get_active_camp(request)
            if camp is None:
                camp = _get_user_owner_camps(request.user).first()
            if camp is not None and getattr(obj, self.camp_field, None) is None:
                setattr(obj, self.camp_field, camp)
        super().save_model(request, obj, form, change)
