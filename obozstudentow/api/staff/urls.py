from django.urls import path, include



urlpatterns = [
    path('meal-validation/', include('obozstudentow.api.staff.meals')),
]
