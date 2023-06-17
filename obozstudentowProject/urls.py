"""obozstudentowProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import obozstudentow.api
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.urls import reverse_lazy
from django.shortcuts import redirect

class EmailLoginBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None
    
def app(request, resource=None):
    if request.user.is_authenticated:
        return render(request, 'app.html')
    return redirect('login')

def index(request, resource=None):
    if request.user.is_authenticated:
        return redirect('app')
    return render(request, 'index.html')

urlpatterns = [

    path('', index, name="index"),
    path('app/', app, name="app"),
    path('app/<path:resource>', app, name="app2"),

    path("admin/", admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(obozstudentow.api.api_router.urls)),


    # login/logout
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # register
    path('register/', auth_views.PasswordResetView.as_view(template_name='registration/register.html', email_template_name='registration/register_email.html', success_url='done/'), name='register'),
    path('register/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/register_done.html'), name='register_done'),

    path('register/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/register_confirm.html', success_url=reverse_lazy('register_complete'), post_reset_login=True), name='register_confirm'),
    path('register/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/register_complete.html'), name='register_complete'),

    # password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset/password_reset.html', email_template_name='password_reset/password_reset_email.html', success_url='done/'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset/password_reset_done.html'), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset/password_reset_confirm.html', success_url=reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset/password_reset_complete.html'), name='password_reset_complete'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



handler404 = "obozstudentowProject.errorViews.error_404"
handler500 = "obozstudentowProject.errorViews.error_500"
handler403 = "obozstudentowProject.errorViews.error_403"
handler400 = "obozstudentowProject.errorViews.error_400"