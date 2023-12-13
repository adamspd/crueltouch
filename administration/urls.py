from django.urls import include, path

from .views import *

app_name = 'administration'

session_patterns = [
    path('list/', list_requested_session, name='session_list'),
    path('update/<int:pk>/', update_requested_session, name='session_update'),
    path('delete/<int:pk>/', delete_requested_session, name='session_delete'),
]

user_patterns = [
    path('list/', list_requested_user, name='user_list'),
    # /administration/users/creation/
    path('creation/', create_new_client, name='create_new_client'),
    # /administration/users/album/liked/
    path('album/liked/', view_client_album_created, name='view_client_album_created'),
    # /administration/users/album/<int:pk>/liked/
    path('album/<int:pk>/liked/', view_all_liked_photos, name='view_all_liked_photos'),
    # /administration/users/album/<int:pk>/delete/
    path('album/<int:pk>/delete/', delete_client_album, name='delete_client_album'),
]

message_patterns = [
    path('list/', list_contact_form, name='message_list'),
    path('delete/<int:pk>/', delete_contact_form, name='message_delete'),
    path('send-reply/<int:pk>/', send_late_booking_confirmation_email_to_users, name='send_email'),
    path('send-invoice/<str:invoice_number>/', send_invoice_to_client, name='send_invoice'),
]

add_photos_patterns = [
    path('homepage/', add_photos_homepage, name='add_photos_homepage'),
    path('portfolio/', add_photos_portfolio, name='add_photos_portfolio'),
    path('clients/', send_photos_for_client_to_choose_from, name='send_photos_for_client_to_choose_from'),
]

link_pattern = [
    path('creation/', create_downloadable_file, name='create_downloadable_file'),
    path('show-all/', list_downloadable_files_link, name='show_all_links_created'),
    path('via-account/', send_photo_via_account, name='via_account'),
    path('delete/<int:pk>/', delete_delivery, name='delete_delivery'),
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
    # /administration/password-change/<int-pk>/
    path('password-change/<int:pk>/', must_change_password, name="must_change_password"),
    # /administration/invoice-form/
    path('invoice-form/', invoice_form, name="invoice_form"),
    # /administration/generate-invoice/
    path('invoices/<str:invoice_number>/', generate_and_process_invoice, name="generate_invoice"),
    # /administration/invoices/view/<str:invoice_number>/
    path('invoice/<str:invoice_number>/', view_invoice, name='view_invoice'),
    # /administration/invoices/update/<str:invoice_number>/status/
    path('invoices/<str:invoice_number>/update_status/', update_invoice_status, name='update_invoice_status'),
    # /administration/administration/get-client-emails/
    path('get-client-emails/', get_client_emails, name='get_client_emails'),
]
