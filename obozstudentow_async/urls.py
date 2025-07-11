from django.urls import path, include
from obozstudentow_async import views as chat_views
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    # path("", chat_views.chatPage, name="chat-page"),
]
