from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BingoUserInstanceViewSet, BingoUserTaskViewSet, BingoReviewViewSet

router = DefaultRouter()
router.register(r"bingo", BingoUserInstanceViewSet, basename="bingo")
router.register(r"bingo-task", BingoUserTaskViewSet, basename="bingo-task")
router.register(r"bingo-review", BingoReviewViewSet, basename="bingo-review")

urlpatterns = [
    path("", include(router.urls)),
]
