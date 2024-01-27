from django.urls import path, include

from .group import *
from .notifications import *
from .houses import *

urlpatterns = [
    path('get-group-signup-info/', get_group_signup_info),
    path('signup-group/', signup_group),

    path('register-fcm-token/', register_fcm_token),

    path('signup-user-for-house/<int:id>/', signup_user_for_house),
    path('leave-house/', leave_house),
]
