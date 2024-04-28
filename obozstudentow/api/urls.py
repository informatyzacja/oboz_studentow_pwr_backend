from django.urls import path, include

from .group import *
from .notifications import *
from .houses import *
from .register import *

# /api2/
urlpatterns = [
    path('get-group-signup-info/', get_group_signup_info),
    path('signup-group/', signup_group),

    path('register-fcm-token/', register_fcm_token),

    path('signup-user-for-house/<int:id>/', signup_user_for_house),
    path('leave-house/', leave_house),
    path('get-house-signups-info/', get_house_signups_info),

    path('send_email_verification/', send_email_verification),
    path('login_with_code/', login_with_code),
]
