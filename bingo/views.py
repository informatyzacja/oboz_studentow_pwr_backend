from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BingoUserInstance, BingoUserTask
from .serializers import BingoUserInstanceSerializer, BingoUserTaskSerializer
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from .utils import swap_user_task


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

    @action(detail=True, methods=["put"])
    def upload_photo(self, request, pk=None):
        task = self.get_object()
        task.photo_proof_url = request.data.get("photo_proof_url")
        task.save()
        task.submitted_at = timezone.now()
        task.task_state = BingoUserTask.TaskState.SUBMITTED
        task.save()

        return Response({"status": "photo uploaded", "submitted_at": task.submitted_at})

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
            completed_at__isnull=False, has_won=False
        )

    @action(detail=True, methods=["put"])
    def review(self, request, pk=None):
        instance = self.get_object()
        approve = request.data.get("approve")
        instance.has_won = bool(approve)
        instance.save()
        return Response({"status": "reviewed"})
