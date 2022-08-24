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
from django.urls import path, include

admin.site.site_header = 'CruelTouch Administration'
admin.site.site_title = 'CruelTouch Administration'
admin.site.index_title = 'Roos Laurore | Owner | Administration Staff'


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', include('homepage.urls')),
    path('client/', include('client.urls')),
    path('contact/', include('static_pages_and_forms.urls'), name='flatpages'),
    path('portfolio/', include('portfolio.urls'))
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

