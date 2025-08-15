from django.urls import path
from .api import (
    bereal_home,
    bereal_profile,
    upload_bereal_post,
    delete_bereal_post,
    like_bereal_post,
    unlike_bereal_post,
    report_bereal_post,
    bereal_status,
    update_profile_photo,
    bereal_post_detail,
)

urlpatterns = [
    path("home/", bereal_home),
    path("profile/", bereal_profile),
    path("profile/<int:user_id>/", bereal_profile),
    path("upload/", upload_bereal_post),
    path("delete/<int:post_id>/", delete_bereal_post),
    path("like/<int:post_id>/", like_bereal_post),
    path("unlike/<int:post_id>/", unlike_bereal_post),
    path("report/<int:post_id>/", report_bereal_post),
    path("status/", bereal_status),
    path("update-profile-photo/", update_profile_photo),
    path("post/<int:post_id>/", bereal_post_detail),
]
