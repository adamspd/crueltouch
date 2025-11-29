# static_pages_and_forms/urls.py
from django.urls import path
from .views import *

app_name = 'flatpages'

urlpatterns = [
    # contact/
    path('', contact, name='contact'),
    path('success/', success, name='success'),
]
