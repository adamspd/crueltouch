from django.urls import path, re_path, include

from .views import *

app_name = 'administration'

session_patterns = [
    path('list/', list_requested_session, name='session_list'),
    path('update/<int:pk>/', update_requested_session, name='session_update'),
    path('delete/<int:pk>/', delete_requested_session, name='session_delete'),
]

user_patterns = [
    path('list/', list_requested_user, name='user_list'),
]

message_patterns = [
    path('list/', list_contact_form, name='message_list'),
    path('delete/<int:pk>/', delete_contact_form, name='message_delete'),
    path('send-reply/<int:pk>/', send_late_booking_confirmation_email_to_users, name='send_email'),
]

add_photos_patterns = [
    path('homepage/', add_photos_homepage, name='add_photos_homepage'),
    path('portfolio/', add_photos_portfolio, name='add_photos_portfolio'),
]

link_pattern = [
    path('creation/', create_downloadable_file, name='create_downloadable_file'),
    path('show-all/', list_downloadable_files_link, name='show_all_links_created'),
    path('via-account/', send_photo_via_account, name='via_account'),
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
    # /administration/add-photos/
    path('add-photos/', include(add_photos_patterns)),
    # /administration/help/
    path('help/', help_view, name='help'),
    # /administration/add-album/
    path('add-album/', add_album_portfolio, name='add_album'),
    # /administration/portfolio/list-photos/
    path('portfolio/list-photos/', list_photos_portfolio, name='list_photos_portfolio'),
    # /administration/homepage/list-photos/
    path('homepage/list-photos/', list_photos_homepage, name='list_photos_homepage'),
    # /administration/portfolio/delete-photo/<int:pk>/
    path('portfolio/delete-photo/<int:pk>/', delete_photo_portfolio, name='delete_photo_portfolio'),
    # /administration/homepage/delete-photo/<int:pk>/
    path('homepage/delete-photo/<int:pk>/', delete_photo_homepage, name='delete_photo_homepage'),
    # /administration/link/
    path('link/', include(link_pattern)),
]
