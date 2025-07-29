from django.shortcuts import render
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BingoUserInstance, BingoUserTask
from .serializers import BingoUserInstanceSerializer, BingoUserTaskSerializer
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from .utils import swap_user_task
from .utils import swap_user_task, check_bingo_win


class BingoUserInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = BingoUserInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BingoUserInstance.objects.filter(user=self.request.user)

    @action(detail=True, methods=["put"])
    def submit_bingo(self, request, pk=None):
        instance = self.get_object()
        instance.completed_at = timezone.now()
        instance.save()
        return Response({"status": "bingo submitted"})


class BingoUserTaskViewSet(viewsets.ModelViewSet):
    serializer_class = BingoUserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BingoUserTask.objects.filter(instance__user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.instance.user != self.request.user:
            raise PermissionDenied("Nie masz dostępu do tego zadania.")
        return obj

    @action(detail=True, methods=["put"], url_path="upload-photo")
    def upload_photo(self, request, pk=None):
        task = self.get_object()
        photo = request.FILES.get("photo_proof")

        if not photo:
            return Response(
                {"error": "No photo file uploaded"}, status=status.HTTP_400_BAD_REQUEST
            )

        if task.photo_proof:
            task.photo_proof.delete(save=False)

        task.photo_proof = photo
        # Status zmieni się automatycznie przy zapisie dzięki poprawce w models.py
        task.save()

        # Używamy get_serializer, aby kontekst (np. request) był dostępny
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["put"])
    def add_comment(self, request, pk=None):
        task = self.get_object()
        task.user_comment = request.data.get("user_comment")
        task.save()
        return Response({"status": "comment added", "submitted_at": task.submitted_at})

    @action(detail=True, methods=["put"])
    def swap_task(self, request, pk=None):
        task = self.get_object()
        new_task = swap_user_task(task)
        if not new_task:
            return Response(
                {"error": "No available tasks to swap"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"status": "task swapped", "new_task": new_task.task_name})


class BingoReviewViewSet(viewsets.ModelViewSet):
    serializer_class = BingoUserInstanceSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return BingoUserInstance.objects.filter(
            has_won=False,
            tasks__task_state=BingoUserTask.TaskState.SUBMITTED,
            needs_bingo_admin_review=True,
        ).distinct()

    @action(detail=True, methods=["put"])
    def approve_bingo_win(self, request, pk=None):
        instance = self.get_object()

        if not check_bingo_win(
            instance
        ):  # Sprawdzamy ponownie, czy warunek Bingo nadal jest spełniony
            return Response(
                {"error": "Bingo condition not met or tasks not fully approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.has_won = True
        instance.completed_at = (
            timezone.now()
        )  # Opcjonalnie: Ustaw completed_at przy wygranej
        instance.needs_bingo_admin_review = (
            False  # Resetujemy flagę, bo Bingo zostało rozpatrzone
        )
        instance.save(
            update_fields=["has_won", "completed_at", "needs_bingo_admin_review"]
        )

        # Tutaj powinno nastąpić wysłanie powiadomienia do użytkownika
        # (patrz punkt 4)
        print(f"Powiadomienie: Użytkownik {instance.user.username} wygrał Bingo!")

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["put"])
    def reject_bingo_win(self, request, pk=None):
        instance = self.get_object()
        instance.has_won = False  # Upewniamy się, że has_won jest False
        instance.needs_bingo_admin_review = False  # Resetujemy flagę
        # Możesz dodać pole, np. `admin_bingo_rejection_reason`
        instance.save(update_fields=["has_won", "needs_bingo_admin_review"])

        # Opcjonalnie: Powiadomienie użytkownika o odrzuceniu
        print(
            f"Powiadomienie: Zgłoszenie Bingo dla użytkownika {instance.user.username} zostało odrzucone."
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["put"])
    def review(self, request, pk=None):
        instance = self.get_object()
        approve = request.data.get("approve")
        instance.has_won = bool(approve)
        instance.save()
        return Response({"status": "reviewed"})

    @action(detail=True, methods=["get"])
    def check_win(self, request, pk=None):
        instance = self.get_object()
        from .utils import check_bingo_win

        result = check_bingo_win(instance)
        return Response({"has_won": result})

    @action(detail=True, methods=["put"], url_path="review-task/(?P<task_pk>\d+)")
    def review_task(self, request, pk=None, task_pk=None):
        try:
            task = BingoUserTask.objects.get(pk=task_pk, instance__pk=pk)
        except BingoUserTask.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Pobierz nowy status i komentarz z requesta
        new_state = request.data.get("task_state")
        reviewer_comment = request.data.get("reviewer_comment")

        if new_state not in [
            BingoUserTask.TaskState.APPROVED,
            BingoUserTask.TaskState.REJECTED,
        ]:
            return Response(
                {"error": "Invalid state"}, status=status.HTTP_400_BAD_REQUEST
            )

        task.task_state = new_state
        if reviewer_comment:
            task.reviewer_comment = reviewer_comment

        task.reviewed_by = request.user
        task.reviewed_at = timezone.now()
        task.save()  # To wywoła sprawdzenie wygranej w models.py

        serializer = BingoUserTaskSerializer(task)
        return Response(serializer.data)
