from django.urls import path, include

from .user import *
from .groups import *
from .points import *

urlpatterns = [
    path('meal-validation/', include('obozstudentow.api.staff.meals')),
    path('get-user-info/', get_user_info),

    path('get-fraction/', get_fraction),
    path('get-fractions/', get_fractions),
    path('get-group/', get_group),
    path('get-groups/', get_groups),

    path('get-points/', get_points),
    path('validate-points/<int:id>/', validate_points),
    path('get-point-types/', get_point_types),
    path('add-points/', add_points),
]
