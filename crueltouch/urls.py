"""crueltouch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

admin.site.site_header = 'CruelTouch Administration'
admin.site.site_title = 'CruelTouch Administration'
admin.site.index_title = 'Roos Laurore | Owner | Administration Staff'

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls, name='admin'),
    path('client/', include('client.urls'), name='client'),
    path('administration/', include('administration.urls'), name='administration'),
    path('contact/', include('static_pages_and_forms.urls'), name='flatpages'),
    path('portfolio/', include('portfolio.urls'), name='portfolio'),
    path('appointments/', include('appointments.urls')),
    path('reset_password/',
         auth_views.PasswordResetView.as_view(template_name="administration/password/forgot-password.html"),
         name='reset_password'),
    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(template_name="administration/password/reset_password_sent.html"),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>',
         auth_views.PasswordResetConfirmView.as_view(template_name="administration/password/has_to_change_password.html"),
         name='password_reset_confirm'),
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name="administration/password/reset_password_done.html"),
         name='password_reset_complete'),
    path('', include('homepage.urls'), name='homepage'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
