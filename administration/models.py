# administration/models.py
import secrets
from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

# Import UserClient for linking invoices
from client.models import UserClient
# Import BasePhoto for inheritance
from core.models import BasePhoto


class PhotoClient(BasePhoto):
    """
    Photos specifically uploaded for a 'Quick Delivery' (Guest) link.
    Inherits thumbnail/webp logic from BasePhoto.
    """
    # BasePhoto provides 'file', 'thumbnail', 'date_uploaded'
    # We override the file to set a specific upload location
    file = models.ImageField(upload_to='photos_clients', verbose_name=_('Photo'))

    is_active = models.BooleanField(default=True)
    was_downloaded = models.BooleanField(default=False)

    def __str__(self):
        return f"Client Photo {self.id}"

    def delete(self, *args, **kwargs):
        """
        Override delete to ensure file cleanup on disk.
        """
        if self.file:
            self.file.delete(save=False)
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        super().delete(*args, **kwargs)


class PhotoDelivery(models.Model):
    """
    Represents a 'WeTransfer' style delivery.
    Generates a unique link for guests to download photos without an account.
    """
    photos = models.ManyToManyField(PhotoClient)
    date = models.DateField(auto_now_add=True)

    # Configuration
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateField(null=True, blank=True)

    # Status
    was_downloaded = models.BooleanField(default=False)

    # Access
    id_delivery = models.CharField(max_length=255, unique=True, blank=True, default="")
    link_to_download = models.CharField(max_length=255, blank=True, default="")

    # Guest Info
    client_name = models.CharField(max_length=255, default='')
    client_email = models.EmailField(max_length=255, blank=True, default='')

    def save(self, *args, **kwargs):
        # Generate Secure ID if missing
        if not self.id_delivery:
            self.id_delivery = secrets.token_urlsafe(16)

        # Set Default Expiration (7 days standard, adjustable)
        if not self.expiration_date:
            self.expiration_date = timezone.now().date() + timezone.timedelta(days=7)

        if not self.link_to_download:
            self.link_to_download = self.get_absolute_url()

        super().save(*args, **kwargs)

    def delete_files(self):
        """
        Manually delete all associated photos and the delivery record.
        """
        for photo in self.photos.all():
            photo.delete()
        self.delete()

    def get_photos(self):
        return self.photos.all()

    def get_absolute_url(self):
        """Generate the download URL using reverse() - no hardcoded domains"""
        from django.urls import reverse
        return reverse('homepage:get_downloadable_client_images', args=[self.id_delivery])

    def get_download_link(self, request=None):
        """
        Get the full download URL.
        If a request is provided, builds absolute URI.
        Otherwise, returns a relative path.
        """
        if request:
            return request.build_absolute_uri(self.get_absolute_url())
        return self.get_absolute_url()


class Invoice(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('none', 'N/A'),
        ('cash', 'Cash'),
        ('credit', 'Credit Card'),
        ('paypal', 'Paypal'),
        ('zelle', 'Zelle'),
        ('check', 'Check'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_PARTIALLY_PAID = 'partially_paid'
    STATUS_CANCELLED = 'cancelled'
    STATUS_OVERDUE = 'overdue'

    INVOICE_STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_PAID, _('Paid')),
        (STATUS_PARTIALLY_PAID, _('Partially Paid')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_OVERDUE, _('Overdue'))
    ]

    # Core Info
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(UserClient, on_delete=models.CASCADE, related_name="invoices")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Financials
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='none')
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default=STATUS_PENDING)
    due_date = models.DateField(null=True, blank=True)

    # Amounts
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage (0-100)")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Percentage (0-100)")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Text Content
    details = models.TextField(blank=True, default='', help_text="Client visible details")
    notes = models.TextField(blank=True, default='', help_text="Internal notes (not visible to client)")

    # Flags
    email_sent = models.BooleanField(default=False)

    # Audit Log
    history = HistoricalRecords()

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client}"

    def get_absolute_url(self):
        return reverse('administration:view_invoice', args=[self.invoice_number])

    def save(self, *args, **kwargs):
        # Auto-generate Invoice Number if missing
        if not self.invoice_number:
            # YYYYMMDD-Random
            date_str = timezone.now().strftime('%Y%m%d')
            rand_str = secrets.token_hex(2).upper()
            self.invoice_number = f"INV-{date_str}-{rand_str}"

        # Auto-update status logic
        if self.pk:
            # Calculate financials
            balance = self.balance_due()
            total = self.total_amount()

            if self.status != self.STATUS_CANCELLED:
                if balance <= 0 < total:
                    self.status = self.STATUS_PAID
                elif total > balance > 0:
                    self.status = self.STATUS_PARTIALLY_PAID
                # Note: We don't auto-revert to PENDING to avoid overwriting manual OVERDUE status

        super().save(*args, **kwargs)

    # --- Financial Calculations ---

    def get_base_amount(self):
        """Sum of all service line items"""
        return sum(item.get_subtotal() for item in self.invoice_services.all())

    def get_discount_amount(self):
        if self.discount > 0:
            return self.get_base_amount() * (self.discount / Decimal(100))
        return Decimal(0)

    def total_amount(self):
        base = self.get_base_amount()
        discounted_base = base - self.get_discount_amount()
        tax_amount = discounted_base * (self.tax_rate / Decimal(100))
        return round(discounted_base + tax_amount, 2)

    def balance_due(self):
        return max(self.total_amount() - self.amount_paid, Decimal(0))

    # --- Utils ---

    def get_name(self):
        """Filename helper"""
        safe_name = f"{self.client.first_name}_{self.client.last_name}".replace(" ", "_").lower()
        return f"{safe_name}_{self.invoice_number}"

    def get_path(self):
        return f'media/invoices/{self.get_name()}.pdf'

    def get_stamp_link(self):
        """
        Legacy helper for HTML templates.
        TODO: Check if these image paths exist in your static folder!
        """
        if self.status == self.STATUS_PAID:
            return "media/assets/img/stamps/paid.png"
        elif self.status == self.STATUS_OVERDUE:
            return "media/assets/img/stamps/overdue.png"
        return None


class InvoiceService(models.Model):
    """Line items for the invoice (e.g. 'Photo Session', 'Extra Edit')"""
    invoice = models.ForeignKey(Invoice, related_name='invoice_services', on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    service_quantity = models.IntegerField(default=1)

    def get_subtotal(self):
        return self.service_price * self.service_quantity


class InvoiceAttachment(models.Model):
    """Files attached to an invoice (Receipts, Contracts, etc.)"""
    invoice = models.ForeignKey(Invoice, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='invoice_attachments/')

    def delete(self, *args, **kwargs):
        """Ensure attachment file is deleted from disk"""
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)
