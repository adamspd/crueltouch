# administration/urls.py
from django.urls import include, path

from . import views

app_name = 'administration'

user_patterns = [
    path('list/', views.list_requested_user, name='user_list'),
    path('creation/', views.create_new_client, name='create_new_client'),
    path('<int:pk>/edit/', views.update_client, name='update_client'),
    path('<int:pk>/details/', views.view_client_details, name='view_client_details'),

    # Client Album (Likes)
    path('album/liked/', views.view_client_album_created, name='view_client_album_created'),
    path('album/<int:pk>/liked/', views.view_all_liked_photos, name='view_all_liked_photos'),
    path('album/<int:pk>/delete/', views.delete_client_album, name='delete_client_album'),
]

message_patterns = [
    path('list/', views.list_contact_form, name='message_list'),
    path('delete/<int:pk>/', views.delete_contact_form, name='message_delete'),
    # Fixed: mapped to views.send_invoice_to_client
    path('send-invoice/<str:invoice_number>/', views.send_invoice_to_client, name='send_invoice'),
]

add_photos_patterns = [
    path('homepage/', views.add_photos_homepage, name='add_photos_homepage'),
    path('portfolio/', views.add_photos_portfolio, name='add_photos_portfolio'),
    # Proofing
    path('clients/', views.send_photos_for_client_to_choose_from, name='send_photos_for_client_to_choose_from'),
]

link_pattern = [
    # Guest Links
    path('creation/', views.create_downloadable_file, name='create_downloadable_file'),
    path('show-all/', views.list_downloadable_files_link, name='show_all_links_created'),
    # Account Delivery
    path('via-account/', views.send_photo_via_account, name='via_account'),
    path('delete/<int:pk>/', views.delete_delivery, name='delete_delivery'),
]

urlpatterns = [
    # Auth
    path('login/', views.login_admin, name='login'),
    path('', views.admin_index, name='index'),

    # Groups
    path('users/', include(user_patterns)),
    path('messages/', include(message_patterns)),
    path('add-photos/', include(add_photos_patterns)),
    path('link/', include(link_pattern)),

    # Misc
    path('help/', views.help_view, name='help'),
    path('password-change/<int:pk>/', views.must_change_password, name="must_change_password"),

    # Website Content
    path('add-album/', views.add_album_portfolio, name='add_album'),
    path('portfolio/list-photos/', views.list_photos_portfolio, name='list_photos_portfolio'),
    path('homepage/list-photos/', views.list_photos_homepage, name='list_photos_homepage'),
    path('portfolio/delete-photo/<int:pk>/', views.delete_photo_portfolio, name='delete_photo_portfolio'),
    path('homepage/delete-photo/<int:pk>/', views.delete_photo_homepage, name='delete_photo_homepage'),

    # --- INVOICES (RESTORED & UNCOMMENTED) ---
    path('invoices/', views.list_invoices, name='list_invoices'),
    path('invoices/form/', views.invoice_form, name='create_invoice'),
    path('invoices/form/<str:invoice_number>/', views.invoice_form, name='edit_invoice'),

    # PDF Generation / Viewing
    path('invoices/<str:invoice_number>/', views.generate_and_process_invoice, name="generate_invoice"),
    path('invoice/<str:invoice_number>/', views.view_invoice, name='view_invoice'),

    # Actions
    path('invoices/delete/<str:invoice_number>/', views.delete_invoice, name='delete_invoice'),
    path('invoices/<str:invoice_number>/update_status/', views.update_invoice_status, name='update_invoice_status'),

    # Helpers
    path('get-client-emails/', views.get_client_emails, name='get_client_emails'),
]
