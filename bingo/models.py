from django.db import models
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    # sprawdzanie wygranej
    def __str__(self):
        return f"{self.task.task_name} for {self.instance.user.username}"

    def save(self, *args, **kwargs):
        # Jeśli dodano zdjęcie, a zadanie nie było wcześniej zgłoszone
        if self.photo_proof_url and self.task_state == self.TaskState.NOT_STARTED:
            self.task_state = self.TaskState.SUBMITTED
            self.submitted_at = timezone.now()

        super().save(*args, **kwargs)
        tasks = self.instance.tasks.all()
        if all(
            t.task_state
            in [
                self.TaskState.SUBMITTED,
                self.TaskState.APPROVED,
                self.TaskState.REJECTED,
            ]
            and t.photo_proof_url
            for t in tasks
        ):
            if self.instance.completed_at is None:
                self.instance.completed_at = timezone.now()
                self.instance.save(update_fields=["completed_at"])


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
