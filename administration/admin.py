from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Invoice, InvoiceAttachment, InvoiceService, PermissionsEmails, PhotoClient, PhotoDelivery


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


@admin.register(InvoiceService)
class InvoiceServiceAdmin(admin.ModelAdmin):
    fields = ('invoice', 'service_name', 'service_price', 'service_quantity')


@admin.register(InvoiceAttachment)
class InvoiceAttachmentAdmin(admin.ModelAdmin):
    fields = ('invoice', 'file',)


class InvoiceServiceInline(admin.TabularInline):
    model = InvoiceService
    extra = 1
    fields = ('service_name', 'service_price', 'service_quantity')


class InvoiceAttachmentInline(admin.TabularInline):
    model = InvoiceAttachment
    extra = 1
    fields = ('file',)


@admin.register(Invoice)
class InvoiceAdmin(SimpleHistoryAdmin):
    list_display = (
        'client', 'status', 'payment_method', 'invoice_number', 'created_at', 'total_amount')
    list_display_links = (
        'client', 'status', 'payment_method', 'invoice_number', 'created_at')
    list_filter = (
        'client', 'status', 'payment_method', 'invoice_number', 'created_at')
    search_fields = (
        'client', 'status', 'payment_method', 'invoice_number', 'created_at')
    list_per_page = 25
    inlines = [InvoiceServiceInline, InvoiceAttachmentInline]

    fieldsets = (
        (None, {
            'fields': (
                'client', 'payment_method', 'due_date', 'status', 'details', 'discount', 'tax_rate', 'amount_paid',
                'notes', 'email_sent'
            )}),
    )
