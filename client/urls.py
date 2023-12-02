from django.urls import path, re_path

from .views import *

app_name = 'client'

urlpatterns = [
    # client/
    path('login/', login_page, name='login'),

    # client/register/
    path('register/', register_page, name='register'),

    # log out/
    path('logout/', logout_user, name='logout'),

    # Book me with session
    path('bookme/session/<int:click_id>/', book_me_session, name='book_me_session'),

    # Book anyway
    path('bookanyway/', book_anyway, name='book_anyway'),

    # client album details
    re_path(r'^(?P<pk>\d+)/$', user_album_details, name='album_details'),

    # favorite
    re_path(r'^favorite/$', favorite, name='favorite'),
    re_path(r'^dislike/$', dislike, name='dislike'),

    # # client details
    # re_path(r'^(?P<pk>\d+)/$', user_details, name='user_details'),
    #
    # # Add photo for clients
    # path('addphotos/<str:pk>/', add_photos, name="add_photos"),

    # Schedule time with me
    path('paynow/', paynow, name="paynow"),

    # Success page
    path('success/', success_payment, name="success_payment"),

    # client/clientID/
    path('', index, name='client_homepage'),
]
