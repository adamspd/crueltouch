from django.urls import path

from .views import *

app_name = 'homepage'

urlpatterns = [
    # homepage
    path('', index, name='index'),
    # /logo/
    path('logo/', get_logo, name="get_logo"),
    # /logo-mini/
    path('logo-mini/', get_logo_mini, name="get_logo_mini"),
    # /photoId/
    path('<int:pk>/', detailed_view, name='detail'),
    path('about/', AboutView.as_view(), name='about'),
    # DetailedView.as_view()  r'^(?P<pk>[0-9]+)/$'
]
