from django.contrib import admin

# Register your models here.

from .models import PermissionsEmails


@admin.register(PermissionsEmails)
class PermissionsEmailsAdmin(admin.ModelAdmin):
    list_display = ('date', 'booking_request', 'contact_form', 'other', 'total')
    list_display_links = ('date', 'booking_request', 'contact_form', 'other', 'total')
    list_filter = ('date', 'booking_request', 'contact_form', 'other', 'total')
    search_fields = ('date', 'booking_request', 'contact_form', 'other', 'total')
    list_per_page = 25
