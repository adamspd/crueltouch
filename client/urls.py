from django.urls import path
from django.conf.urls import url
from .views import *

app_name = 'client'

urlpatterns = [
    # client/
    path('', login_page, name='login'),

    # client/register/
    path('register/', register_page, name='register'),

    # client/clientID/
    path('user/', index, name='client_homepage'),

    # log out/
    path('logout/', logout_user, name='logout'),

    # favorite
    path('favorite/', favorite, name='favorite'),

    # owner vs superuser
    path('rooslaurore/', owner, name='owner'),
    path('adashboard/', when_owner_logged, name='ownerislogged'),
    path('superuser/', superuserlogin, name='superuserlogin'),

    # Book me
    path('bookme/', bookme, name='bookme'),

    # Book anyway
    path('bookanyway/', book_anyway, name='book_anyway'),

    # Owner help
    path('ahelp/', owner_help, name='help_owner'),

    # Owner's Client
    path('aclient/', owner_client, name='owner_client'),

    # client details
    url(r'^(?P<pk>[0-9]+)/$', user_details, name='user_details'),

    # Owner's contact form
    path('amessages/', owner_contact_form, name='owner_messages'),
]