from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import BerealPost, BerealLike, BerealReport, BerealNotification


@admin.register(BerealPost)
class BeerealPostAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "bereal_date",
        "created_at",
        "is_late",
        "likes_count",
        "photo1_preview",
        "photo2_preview",
    )
    list_filter = ("bereal_date", "is_late", "created_at")
    search_fields = ("user__first_name", "user__last_name", "user__email")
    readonly_fields = ("created_at", "photo1_preview", "photo2_preview")
    ordering = ("-created_at",)

    def likes_count(self, obj):
        return obj.likes.count()

    likes_count.short_description = "Liczba lajków"

    def photo1_preview(self, obj):
        if obj.photo1:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.photo1.url,
            )
        return "Brak zdjęcia"

    def photo2_preview(self, obj):
        if obj.photo2:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.photo2.url,
            )
        return "Brak zdjęcia"

    photo1_preview.short_description = "Podgląd zdjęcia 1"
    photo2_preview.short_description = "Podgląd zdjęcia 2"


@admin.register(BerealLike)
class BeerealLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post_user", "post_date", "created_at")
    list_filter = ("created_at", "post__bereal_date")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "post__user__first_name",
        "post__user__last_name",
    )
    ordering = ("-created_at",)

    def post_user(self, obj):
        return f"{obj.post.user.first_name} {obj.post.user.last_name}"

    post_user.short_description = "Autor posta"

    def post_date(self, obj):
        return obj.post.bereal_date

    post_date.short_description = "Data BeReal"


@admin.register(BerealReport)
class BeerealReportAdmin(admin.ModelAdmin):
    list_display = (
        "reporter",
        "post_user",
        "post_date",
        "created_at",
        "resolved",
        "resolved_by",
    )
    list_filter = ("resolved", "created_at", "post__bereal_date")
    search_fields = (
        "reporter__first_name",
        "reporter__last_name",
        "post__user__first_name",
        "post__user__last_name",
        "reason",
    )
    readonly_fields = (
        "created_at",
        "post_link",
    )
    ordering = ("-created_at",)
    actions = ["mark_resolved"]

    def post_user(self, obj):
        return f"{obj.post.user.first_name} {obj.post.user.last_name}"

    post_user.short_description = "Autor posta"

    def post_date(self, obj):
        return obj.post.bereal_date

    post_date.short_description = "Data BeReal"

    def post_link(self, obj):
        url = reverse("admin:bereal_berealpost_change", args=[obj.post.id])
        return format_html('<a href="{}">Zobacz post</a>', url)

    post_link.short_description = "Link do posta"

    def mark_resolved(self, request, queryset):
        queryset.update(
            resolved=True, resolved_by=request.user, resolved_at=timezone.now()
        )
        self.message_user(
            request, f"Oznaczono {queryset.count()} zgłoszeń jako rozwiązane."
        )

    mark_resolved.short_description = "Oznacz jako rozwiązane"


@admin.register(BerealNotification)
class BeerealNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "sent_at",
        "start",
        "deadline",
        "is_active_display",
        "posts_count",
    )
    list_filter = ("date", "sent_at")
    ordering = ("-date",)
    readonly_fields = ("sent_at",)

    def is_active_display(self, obj):
        return obj.is_active()

    is_active_display.boolean = True
    is_active_display.short_description = "Aktywny"

    def posts_count(self, obj):
        return BerealPost.objects.filter(bereal_date=obj.date).count()

    posts_count.short_description = "Liczba postów"
