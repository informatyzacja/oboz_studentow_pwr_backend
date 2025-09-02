# bingo/views.py

from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import BingoUserInstance, BingoUserTask
from .serializers import BingoUserInstanceSerializer, BingoUserTaskSerializer
from .utils import swap_user_task, check_bingo_win


class BingoUserInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet dla użytkownika do przeglądania swojej planszy bingo.
    Jest ReadOnly, ponieważ akcje są wykonywane przez dedykowane metody.
    """

    serializer_class = BingoUserInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Użytkownik widzi tylko swoje aktywne (niezakończone) plansze
        return BingoUserInstance.objects.filter(user=self.request.user).exclude(
            review_status=BingoUserInstance.ReviewStatus.COMPLETED
        )

    @action(detail=True, methods=["post"], url_path="submit-for-review")
    def submit_for_review(self, request, pk=None):
        """
        Akcja dla użytkownika, aby wysłać planszę do sprawdzenia przez admina.
        """
        instance = self.get_object()

        if not check_bingo_win(instance):
            return Response(
                {"error": "Nie masz jeszcze bingo! Wykonaj zadania w jednej linii."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if instance.review_status != BingoUserInstance.ReviewStatus.IN_PROGRESS:
            return Response(
                {
                    "error": "Ta plansza została już wysłana lub jest w trakcie weryfikacji."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.review_status = BingoUserInstance.ReviewStatus.PENDING_REVIEW
        instance.save(update_fields=["review_status"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BingoUserTaskViewSet(viewsets.ModelViewSet):

    # ViewSet do zarządzania pojedynczymi zadaniami przez użytkownika.

    serializer_class = BingoUserTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return BingoUserTask.objects.filter(instance__user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.instance.user != self.request.user:
            raise PermissionDenied("Nie masz dostępu do tego zadania.")
        return obj

    @action(detail=True, methods=["post"], url_path="upload-photo")
    def upload_photo(self, request, pk=None):
        task = self.get_object()
        photo = request.data.get("photo_proof")

        if not photo:
            return Response(
                {"error": "Nie załączono pliku ze zdjęciem."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if task.instance.review_status not in [
            BingoUserInstance.ReviewStatus.IN_PROGRESS,
            BingoUserInstance.ReviewStatus.NEEDS_CORRECTION,
        ]:
            return Response(
                {
                    "error": "Nie można modyfikować zadań, gdy plansza jest w trakcie weryfikacji."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        task.photo_proof = photo
        task.save()

        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="swap")
    def swap(self, request, pk=None):
        task = self.get_object()

        if task.instance.swap_used:
            return Response(
                {"error": "Wykorzystałeś już swoją jednorazową wymianę zadania."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if task.task_state != BingoUserTask.TaskState.NOT_STARTED:
            return Response(
                {
                    "error": "Możesz wymienić tylko zadanie, którego jeszcze nie zacząłeś realizować."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_task_template = swap_user_task(task)

        if not new_task_template:
            return Response(
                {"error": "Brak dostępnych zadań do wymiany."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(task)
        return Response(serializer.data)


class BingoReviewViewSet(viewsets.ViewSet):

    # ViewSet dla Administratora do zarządzania i weryfikacji plansz bingo.

    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        queryset = BingoUserInstance.objects.filter(
            review_status=BingoUserInstance.ReviewStatus.PENDING_REVIEW
        ).prefetch_related("tasks__task")
        serializer = BingoUserInstanceSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        instance = BingoUserInstance.objects.get(pk=pk)
        serializer = BingoUserInstanceSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="review-task/(?P<task_pk>\d+)")
    def review_task(self, request, pk=None, task_pk=None):
        try:
            task = BingoUserTask.objects.get(pk=task_pk, instance__pk=pk)
        except BingoUserTask.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        new_state = request.data.get("task_state")
        reviewer_comment = request.data.get("reviewer_comment")

        if new_state not in [
            BingoUserTask.TaskState.APPROVED,
            BingoUserTask.TaskState.REJECTED,
        ]:
            return Response(
                {"error": "Nieprawidłowy status zadania."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_state == BingoUserTask.TaskState.REJECTED and not reviewer_comment:
            return Response(
                {"error": "Komentarz jest wymagany przy odrzuceniu zadania."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.task_state = new_state
        task.reviewer_comment = reviewer_comment if reviewer_comment else ""
        task.reviewed_by = request.user
        task.reviewed_at = timezone.now()
        task.save()

        if new_state == BingoUserTask.TaskState.REJECTED:
            instance = task.instance
            instance.review_status = BingoUserInstance.ReviewStatus.NEEDS_CORRECTION
            instance.save(update_fields=["review_status"])

        serializer = BingoUserTaskSerializer(task, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="approve-win")
    def approve_win(self, request, pk=None):
        instance = BingoUserInstance.objects.get(pk=pk)

        if not check_bingo_win(instance):
            return Response(
                {
                    "error": "Warunek wygranej nie jest spełniony. Sprawdź, czy wszystkie zadania w linii są zatwierdzone."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.has_won = True
        instance.completed_at = timezone.now()
        instance.review_status = BingoUserInstance.ReviewStatus.COMPLETED
        instance.save()

        # Wysłanie powiadomienia do użytkownika

        serializer = BingoUserInstanceSerializer(instance, context={"request": request})
        return Response(serializer.data)
