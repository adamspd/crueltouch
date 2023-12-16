from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.views.generic.base import RedirectView

from administration.views import download_zip, get_downloadable_client_images
from crueltouch.sitemaps import ImportantStaticViewSitemap, StaticViewSitemap
from static_pages_and_forms.views import privacy_policy, terms_and_conditions
from .views import *

app_name = 'homepage'

sitemaps = {
    'important': ImportantStaticViewSitemap,
    'static': StaticViewSitemap,
}

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
    # /download/<str:id_delivery>/
    path('download/<str:id_delivery>/', get_downloadable_client_images, name='get_downloadable_client_images'),
    # /download/zip/<str:id_delivery>/
    path('download/zip/<str:id_delivery>/', download_zip, name='download_zip'),
    # /privacy-policy/
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    # /terms-and-conditions/
    path('terms-and-conditions/', terms_and_conditions, name='terms_and_conditions'),
    # /services/
    path('services/', services_offered, name='services_offered'),
    path('sitemap.xml/', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt/', get_robot_txt, name='robots_txt'),
]
