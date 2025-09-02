from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BingoUserInstanceViewSet,
    BingoUserTaskViewSet,
    BingoReviewViewSet,
    bingo_status,
)

router = DefaultRouter()
router.register(r"bingo", BingoUserInstanceViewSet, basename="bingo")
router.register(r"bingo-task", BingoUserTaskViewSet, basename="bingo-task")
router.register(r"bingo-review", BingoReviewViewSet, basename="bingo-review")

urlpatterns = [
    # Ważne: endpoint statusu nie może kolidować z wzorcem detail viewsetu 'bingo/<pk>/'
    path("bingo-status/", bingo_status),
    path("", include(router.urls)),
]
