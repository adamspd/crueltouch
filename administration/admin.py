from django.contrib import admin

# Register your models here.

from .models import PermissionsEmails


@admin.register(PermissionsEmails)
class PermissionsEmailsAdmin(admin.ModelAdmin):
    list_display = ('date', 'number_of_emails')
    list_display_links = ('date', 'number_of_emails')
    list_filter = ('date', 'number_of_emails')
    search_fields = ('date', 'number_of_emails')
    list_per_page = 25
