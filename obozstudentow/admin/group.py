from django.contrib import admin

from import_export.admin import ImportExportModelAdmin
from django.db.models.fields.related import ForeignKey
from django.forms.models import ModelChoiceField
from django.http.request import HttpRequest
from typing import Any

from ..models import GroupType, Group, GroupMember, GroupWarden, User

from orderable.admin import OrderableAdmin

@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('name',)

class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1
    classes = ['collapse']

class GroupWardenInline(admin.TabularInline):
    model = GroupWarden
    extra = 1

    def formfield_for_foreignkey(self, db_field: ForeignKey[Any], request: HttpRequest | None, **kwargs: Any) -> ModelChoiceField | None:
        field = super(GroupWardenInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'user':
            field.queryset = User.objects.filter(groups__name__in=('Sztab','Kadra','Bajer'))
        return field
    
@admin.register(GroupMember)
class GroupMemberAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'group', 'user')
    search_fields = ('group', 'user')
    list_filter = ('group','group__type')

@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin, OrderableAdmin):
    list_display = ('id', 'name', 'type', 'logo', 'map', 'messenger', 'sort_order_display')
    search_fields = ('name', 'type')
    list_filter = ('type',)
    inlines = [GroupWardenInline, GroupMemberInline]


from ..models import PointType, Point

@admin.register(PointType)
class PointTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','group_type')
    search_fields = ('name','group_type')
    list_filter = ('group_type',)

@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ('group', 'type', 'description', 'date', 'addedBy', 'numberOfPoints', 'validated')
    search_fields = ('group', 'type', 'description', 'date', 'addedBy', 'numberOfPoints')
    list_filter = ('validated', 'rejected', 'group', 'type', 'addedBy')

from ..models import NightGameSignup
@admin.register(NightGameSignup)
class NightGameSignupAdmin(admin.ModelAdmin):
    list_display = ('group', 'user_first_name', 'user_last_name', 'user_band', 'date', 'addedBy', 'failed')
    search_fields = ('group', 'user_first_name', 'user_last_name', 'user_band', 'date', 'addedBy')
    list_filter = ('group', 'failed')