# client/urls.py
from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    # --- Dashboard & Core ---
    path('', views.index, name='client_homepage'),

    # --- Authentication ---
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # --- Profile Management ---
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # --- Album & Photos ---
    # Moved to bottom to prevent ID collision with other text-based paths
    # Replaced re_path regex with modern <int:pk> converter
    path('<int:pk>/', views.user_album_details, name='album_details'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),

    # --- Commerce/Booking ---
    path('paynow/', views.paynow, name="paynow"),
    path('success/', views.success_payment, name="success_payment"),
]
