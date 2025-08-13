from django.contrib.auth import get_user_model
from django.contrib import admin, messages
from .models import BingoUserInstance, BingoTaskTemplate, BingoUserTask
from .utils import create_bingo_for_user

User = get_user_model()


@admin.action(
    description="Wygeneruj bingo dla użytkownika, jeśli nie ma jeszcze planszy"
)
def generate_bingo_for_selected_users(modeladmin, request, queryset):
    created_count = 0
    skipped_count = 0

    for user in queryset:
        if BingoUserInstance.objects.filter(user=user).exists():
            skipped_count += 1
            continue
        try:
            create_bingo_for_user(user)
            created_count += 1
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Nie udało się wygenerować bingo dla {user}: {e}",
                level=messages.ERROR,
            )

    modeladmin.message_user(
        request,
        f"Wygenerowano bingo dla {created_count} użytkowników, pominięto {skipped_count} użytkowników z istniejącymi planszami.",
        level=messages.SUCCESS,
    )


class BingoUserTaskAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "instance",
        "task_state",
        "row",
        "col",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    )
    list_filter = ("task_state", "instance__user")
    search_fields = (
        "task__task_name",
        "instance__user__username",
        "user_comment",
        "reviewer_comment",
    )
    readonly_fields = ("submitted_at", "reviewed_at", "reviewed_by")
    list_select_related = ("task", "instance", "reviewed_by")

    # Umożliwienie edycji zadań w adminie
    fields = (
        "instance",
        "task",
        "row",
        "col",
        "task_state",
        "user_comment",
        "reviewer_comment",
        "photo_proof",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    )


class BingoUserTaskInlineForActiveGames(admin.TabularInline):
    model = BingoUserTask
    extra = 0
    readonly_fields = (
        "task",
        "row",
        "col",
        "task_state",
        "user_comment",
        "reviewer_comment",
        "photo_proof",
    )
    can_delete = False
    show_change_link = True


@admin.register(BingoUserInstance)
class BingoUserInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "review_status",
        "has_won",
        "swap_used",
        "created_at",
        "completed_at",
    )
    list_filter = ("review_status", "has_won")
    search_fields = ("user__username",)
    inlines = [BingoUserTaskInlineForActiveGames]
    readonly_fields = ("created_at", "completed_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


@admin.register(BingoTaskTemplate)
class BingoTaskTemplateAdmin(admin.ModelAdmin):
    list_display = ("task_name", "is_active")


admin.site.register(BingoUserTask, BingoUserTaskAdmin)
