from django.urls import path
from .api import (
    uploadProfilePhoto,
    uploadProfileData,
    loadTinderProfiles,
    tinderAction,
)

urlpatterns = [
    path("upload-profile-photo/", uploadProfilePhoto),
    path("upload-profile-data/", uploadProfileData),
    path("load-profiles/", loadTinderProfiles),
    path("action/", tinderAction),
]
