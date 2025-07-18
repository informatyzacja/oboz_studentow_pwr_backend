from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BingoUserInstance, BingoUserTask
from .serializers import BingoUserInstanceSerializer, BingoUserTaskSerializer
from rest_framework.permissions import IsAdminUser
from django.utils import timezone


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


# dodać opcje podmiany 1 zadania


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
        return Response({"status": "photo uploaded"})

    @action(detail=True, methods=["put"])
    def add_comment(self, request, pk=None):
        task = self.get_object()
        task.user_comment = request.data.get("user_comment")
        task.save()
        return Response({"status": "comment added"})


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
