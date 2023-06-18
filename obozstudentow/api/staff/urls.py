from django.urls import path

from .meals import validate_meal

urlpatterns = [
    path('validate-meal/', validate_meal),
]
