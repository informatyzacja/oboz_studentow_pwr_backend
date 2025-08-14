from django.contrib import admin

from .models import BeRealPhoto, BeRealPhotoInteraction, BeRealNotification


class BeRealPhotoInteractionInline(admin.TabularInline):
    model = BeRealPhotoInteraction
    extra = 0
    fields = ("user", "interaction_type", "created_at")
    readonly_fields = ("created_at", "interaction_type", "user")


@admin.register(BeRealPhoto)
class BeRealPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "taken_at", "is_late", "like_count")
    list_filter = ("is_late",)
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__id",
        "id",
    )
    ordering = ("-taken_at",)
    inlines = [BeRealPhotoInteractionInline]


@admin.register(BeRealNotification)
class BeRealNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "predicted_send_time", "is_sent", "sent_at")
    list_filter = ("is_sent",)
    search_fields = ("id",)
    ordering = ("-predicted_send_time",)
