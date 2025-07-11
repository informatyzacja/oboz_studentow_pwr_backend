from typing import Any
from django.contrib import admin
from django.db.models.fields.related import ForeignKey
from django.forms.models import ModelChoiceField
from django.http.request import HttpRequest

from import_export.admin import ImportExportModelAdmin

from ..models import Workshop, WorkshopSignup, WorkshopLeader, User


class WorkshopSignupInline(admin.TabularInline):
    model = WorkshopSignup
    extra = 1
    classes = ["collapse"]


class WorkshopLeaderInline(admin.TabularInline):
    model = WorkshopLeader
    extra = 1

    def formfield_for_foreignkey(
        self, db_field: ForeignKey[Any], request: HttpRequest | None, **kwargs: Any
    ) -> ModelChoiceField | None:
        field = super(WorkshopLeaderInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )
        if db_field.name == "user":
            field.queryset = User.objects.filter(
                groups__name__in=("Sztab", "Kadra", "Bajer")
            )
        return field


@admin.register(WorkshopLeader)
class WorkshopLeaderAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("user", "workshop")
    search_fields = ("user__first_name", "user__last_name", "workshop__name")
    list_filter = ("workshop",)


@admin.register(Workshop)
class WorkshopAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    def signups(self, obj):
        return str(obj.workshopsignup_set.count()) + "/" + str(obj.userLimit)

    list_display = (
        "name",
        "visible",
        "has_image",
        "start",
        "end",
        "location",
        "signups",
        "signupsOpen",
        "signupsOpenTime",
    )
    readonly_fields = ("signups",)
    search_fields = ("name", "visible", "location")
    list_filter = (
        "visible",
        "signupsOpen",
        "start",
        "end",
        "location",
        "signupsOpenTime",
    )
    inlines = [WorkshopLeaderInline, WorkshopSignupInline]
