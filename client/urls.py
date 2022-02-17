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

    # owner vs superuser
    path('rooslaurore/', owner, name='owner'),
    path('adashboard/', when_owner_logged, name='ownerislogged'),
    path('superuser/', superuserlogin, name='superuserlogin'),

    # Book me
    path('bookme/', bookme, name='bookme'),

    # Book anyway
    path('bookanyway/', book_anyway, name='book_anyway'),

    # client album details
    url(r'^user/(?P<pk>[0-9]+)/$', user_album_details, name='album_details'),

    # favorite
    url(r'^user/(?P<pk>[0-9]+)/favorite$', favorite, name='favorite'),

    # Owner help
    path('ahelp/', owner_help, name='help_owner'),

    # Owner's Client
    path('aclient/', owner_client, name='owner_client'),

    # client details
    url(r'^(?P<pk>[0-9]+)/$', user_details, name='user_details'),

    # Owner's contact form
    path('amessages/', owner_contact_form, name='owner_messages'),

    # Owner's book me
    path('abook/', owner_bookme, name='owner_bookmes'),

    # Update current book
    path('a_update_bookme/<str:pk>/', updateBookme, name="update_bookmes"),

    # Delete current book
    path('adelete/<str:pk>/', delete_book, name="delete_bookmes"),

    # Add photo for clients
    path('addphotos/<str:pk>/', add_photos, name="add_photos"),

    # Add photo to the homepage
    path('addphotos/', add_photos_homepage, name="add_photos_homepage"),

    # Add photo to the portfolio
    path('addportfolio/', add_photos_portfolio, name="add_photos_portfolio"),

    # Schedule time with me
    path('paynow/', paynow, name="paynow"),

    # Success page
    path('success/', success_payment, name="success_payment"),

    # create album for portfolio
    path('createalbum/', creationofalbum, name="creationofalbum"),

    # delete photo from portfolio
    path('deletephoto/<str:pk>', delete_photo, name="deletephotoportfolio"),
]
