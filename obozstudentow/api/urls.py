from django.urls import path, include

from .group import *
from .notifications import *
from .houses import *
from .register import *
from .tinder import *
from .bereal import *

from .chat import *

# /api2/tinder/
tinderurlpatterns = [
    path("upload-profile-photo/", uploadProfilePhoto),
    path("upload-profile-data/", uploadProfileData),
    path("load-profiles/", loadTinderProfiles),
    path("action/", tinderAction),
]

# /api2/bereal/
berealurlpatterns = [
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

# /api2/
urlpatterns = [
    path("get-group-signup-info/", get_group_signup_info),
    path("signup-group/", signup_group),
    path("register-fcm-token/", register_fcm_token),
    path("enable_disable_notifications/", enable_disable_notifications),
    path("signup-user-for-house/<int:id>/", signup_user_for_house),
    path("leave-house/", leave_house),
    path("get-house-signups-info/", get_house_signups_info),
    path("send_email_verification/", send_email_verification),
    path("login_with_code/", login_with_code),
    path("tinder/", include(tinderurlpatterns)),
    path("bereal/", include(berealurlpatterns)),
    path("block_chat/<int:chat_id>/", block_chat),
    path("block_chat_notifications/<int:chat_id>/", block_chat_notifications),
]
