from django.db import models
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User  # Zastępuje user_table


class BingoTaskTemplate(models.Model):
    task_name = models.TextField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.task_name


class BingoUserInstance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    has_won = models.BooleanField(default=False)

    def __str__(self):
        return f"Bingo for {self.user.username} - {self.created_at.date()}"


# ustawianie automatyczne wygranej dodać


class BingoUserTask(models.Model):
    class TaskState(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    instance = models.ForeignKey(
        BingoUserInstance, on_delete=models.CASCADE, related_name="tasks"
    )
    task = models.ForeignKey(BingoTaskTemplate, on_delete=models.CASCADE)
    task_state = models.CharField(
        max_length=20, choices=TaskState.choices, default=TaskState.NOT_STARTED
    )
    user_comment = models.TextField(blank=True, null=True)
    reviewer_comment = models.TextField(blank=True, null=True)
    photo_proof_url = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_tasks",
    )

    def __str__(self):
        return f"{self.task.task_name} for {self.instance.user.username}"


class BingoUserTaskInline(admin.TabularInline):
    model = BingoUserTask
    extra = 0


@admin.register(BingoUserInstance)
class BingoUserInstanceAdmin(admin.ModelAdmin):
    inlines = [BingoUserTaskInline]
    list_display = ("user", "created_at", "completed_at", "has_won")


@admin.register(BingoTaskTemplate)
class BingoTaskTemplateAdmin(admin.ModelAdmin):
    list_display = ("task_name", "is_active")
