from django.contrib import admin


from ..models import GroupType, Group, GroupMember, GroupWarden

@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 1
    classes = ['collapse']

class GroupWardenInline(admin.TabularInline):
    model = GroupWarden
    extra = 1

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'logo', 'map', 'messenger')
    search_fields = ('name', 'type')
    list_filter = ('type',)
    inlines = [GroupWardenInline, GroupMemberInline]


from ..models import PointType, Point

@admin.register(PointType)
class PointTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ('group', 'type', 'description', 'date', 'addedBy', 'numberOfPoints')
    search_fields = ('group', 'type', 'description', 'date', 'addedBy', 'numberOfPoints')