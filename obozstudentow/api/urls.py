from django.urls import path, include

from .group import *
from .notifications import *
from .houses import *
from .register import *
from .tinder import *

from .chat import *

# /api2/tinder/
tinderurlpatterns = [
    path("upload-profile-photo/", uploadProfilePhoto),
    path("upload-profile-data/", uploadProfileData),
    path("load-profiles/", loadTinderProfiles),
    path("action/", tinderAction),
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
    path("block_chat/<int:chat_id>/", block_chat),
    path("block_chat_notifications/<int:chat_id>/", block_chat_notifications),
]
