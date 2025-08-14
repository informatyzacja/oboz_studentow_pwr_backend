from rest_framework import routers
from bereal import views

from django.urls import path, include

router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet)
router.register(r"bereal_photos", views.BerealHomePhotoView, basename="bereal_photos")
router.register(
    r"like_photo", views.BerealPhotoInteractionUpdateView, basename="like_photo"
)

urlpatterns = [
    path("", include(router.urls)),
]
