from django.urls import path
from .views import *

app_name = 'pf'

urlpatterns = [
    # portfolio
    path('', index_portfolio, name='index_portfolio'),
]
