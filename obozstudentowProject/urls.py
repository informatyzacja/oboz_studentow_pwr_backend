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
from django.urls import reverse_lazy
from django.views.generic import RedirectView

import obozstudentow.views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

admin.site.site_header = "Panel administracyjny Obozu Studentów PWr"
admin.site.site_title = "Panel administracyjny Obozu Studentów PWr"
admin.site.index_title = "Witaj w panelu administracyjnym Obozu Studentów PWr"

auth_views.site_header = "ObozStudentow"

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('staff-api/', include('obozstudentow.api.staff.urls')),

    path("admin/", admin.site.urls, name="admin"),
    path('api/', include(obozstudentow.api.api_router.urls)),
    path('api2/', include('obozstudentow.api.urls')),

    path('download-image/<int:image_id>/', obozstudentow.views.download_image, name='download'),


    # # register
    path('register/', auth_views.PasswordResetView.as_view(email_template_name='registration/register_email.txt', subject_template_name='registration/register_email_subject.txt' , success_url='done/', title='Rejestracja'), name='register'),

    path('register/done/', auth_views.PasswordResetDoneView.as_view(), name='register_done'),

    path('register/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('register_complete'), post_reset_login=True), name='register_confirm'),

    path('register/complete/', auth_views.PasswordResetCompleteView.as_view(title = "Hasło ustawione"), name='register_complete'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



handler404 = "obozstudentowProject.errorViews.error_404"
handler500 = "obozstudentowProject.errorViews.error_500"
handler403 = "obozstudentowProject.errorViews.error_403"
handler400 = "obozstudentowProject.errorViews.error_400"