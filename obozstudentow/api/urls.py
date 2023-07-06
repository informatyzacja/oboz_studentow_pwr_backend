from django.urls import path, include

from .group import *

urlpatterns = [
    path('get-group-signup-info/', get_group_signup_info),
    path('signup-group/', signup_group),
]
