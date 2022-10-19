from django.urls import path, re_path, include

from .views import *

app_name = 'administration'

session_patterns = [
    path('list/', list_requested_session, name='session_list'),
]

user_patterns = [
    path('list/', list_requested_user, name='user_list'),
]

message_patterns = [
    path('list/', list_contact_form, name='message_list'),
]

urlpatterns = [
    # /administration/login
    path('login/', login_admin, name='login'),
    # /administration/
    path('', admin_index, name='index'),
    # /administration/session/
    path('session/', include(session_patterns)),
    # /administration/users/
    path('users/', include(user_patterns)),
    # /administration/messages/
    path('messages/', include(message_patterns)),
    # /administration/help/
    path('help/', help_view, name='help'),
]
