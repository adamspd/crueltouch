from django.contrib import admin

# Register your models here.

from .models import PermissionsEmails, PhotoClient, PhotoDelivery


@admin.register(PermissionsEmails)
class PermissionsEmailsAdmin(admin.ModelAdmin):
    list_display = ('date', 'booking_request', 'contact_form', 'other', 'total')
    list_display_links = ('date', 'booking_request', 'contact_form', 'other', 'total')
    list_filter = ('date', 'booking_request', 'contact_form', 'other', 'total')
    search_fields = ('date', 'booking_request', 'contact_form', 'other', 'total')
    list_per_page = 25


@admin.register(PhotoClient)
class PhotoClientAdmin(admin.ModelAdmin):
    list_display = ('file', 'is_active', 'was_downloaded')
    list_display_links = ('file', 'is_active', 'was_downloaded')
    list_filter = ('file', 'is_active', 'was_downloaded')
    search_fields = ('file', 'is_active', 'was_downloaded')
    list_per_page = 25


@admin.register(PhotoDelivery)
class PhotoDeliveryAdmin(admin.ModelAdmin):
    list_display = ('date', 'is_active', 'expiration_date', 'was_downloaded', 'link_to_download', 'id_delivery')
    list_display_links = ('date', 'is_active', 'expiration_date', 'was_downloaded', 'link_to_download', 'id_delivery')
    list_filter = ('date', 'is_active', 'expiration_date', 'was_downloaded', 'link_to_download', 'id_delivery')
    search_fields = ('date', 'is_active', 'expiration_date', 'was_downloaded', 'link_to_download', 'id_delivery')
    list_per_page = 25
