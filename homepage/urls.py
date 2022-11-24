from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.views.generic.base import RedirectView

from .views import *

app_name = 'homepage'

urlpatterns = [
    # homepage
    path('', index, name='index'),
    # /logo/
    path('logo/', get_logo, name="get_logo"),
    # /logo-mini/
    path('logo-mini/', get_logo_mini, name="get_logo_mini"),
    # /about/
    path('about/', AboutView.as_view(), name='about'),
    # /promotions/
    path('promotions/', promotions, name='promotions'),
    # /favicon.ico
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico')), name="get_favicon"),
]
