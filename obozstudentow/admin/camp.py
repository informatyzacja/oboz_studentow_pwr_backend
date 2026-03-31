from django.contrib import admin
from ..models.camp import Camp, UserCamp


class UserCampInline(admin.TabularInline):
    model = UserCamp
    extra = 1
    autocomplete_fields = ["user"]


@admin.register(Camp)
class CampAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at", "member_count")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    inlines = [UserCampInline]

    def member_count(self, obj):
        return obj.user_camps.count()

    member_count.short_description = "Liczba członków"


@admin.register(UserCamp)
class UserCampAdmin(admin.ModelAdmin):
    list_display = ("user", "camp", "role", "joined_at")
    list_filter = ("role", "camp")
    search_fields = ("user__email", "user__first_name", "user__last_name", "camp__name")
    autocomplete_fields = ["user", "camp"]
