from django.urls import path
from django.conf.urls import url
from .views import *

app_name = 'homepage'

urlpatterns = [
    # homepage
    path('', index, name='index'),

    # /photoId/
    path('<int:pk>/', detailed_view, name='detail'),

    path('about/', AboutView.as_view(), name='about'),
    # DetailedView.as_view()  r'^(?P<pk>[0-9]+)/$'
]