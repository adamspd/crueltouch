# administration/models.py
import random
import string
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from client.models import UserClient


class PermissionsEmails(models.Model):
    date = models.CharField(max_length=255, null=False, blank=False, unique=True, verbose_name=_('The date'))
    booking_request = models.IntegerField(default=0, verbose_name=_('Number of emails sent for booking request'))
    contact_form = models.IntegerField(default=0, verbose_name=_('Number of emails sent for contact form'))
    other = models.IntegerField(default=0, verbose_name=_('Other emails sent'))
    total = models.IntegerField(default=0, verbose_name=_('Total number of emails sent'))

    def __str__(self):
        return str(self.date)

    class Meta:
        verbose_name_plural = _('Permissions Emails')

    def save(self, *args, **kwargs):
        self.total = self.booking_request + self.contact_form + self.other
        return super().save(*args, **kwargs)

    @property
    def can_send_email(self):
        return self.total < 300


class PhotoClient(models.Model):
    file = models.ImageField(upload_to='photos_clients', verbose_name=_('Photo'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    was_downloaded = models.BooleanField(default=False, verbose_name=_('Was downloaded'))

    def __str__(self):
        # filename without an extension
        name = self.file.path.split('/')[-1].split('.')[0]
        return name

    def get_absolute_url(self):
        return self.file.url

    def get_name_with_extension(self):
        return self.file.path.split('/')[-1]

    def get_name_without_extension(self):
        return self.file.path.split('/')[-1].split('.')[0]

    def set_was_downloaded_to_true(self):
        self.was_downloaded = True
        self.save()

    def was_downloaded_(self):
        return self.was_downloaded

    def delete(self, using=None, keep_parents=False):
        self.file.delete()
        super().delete(using, keep_parents)


# contains a list of PhotoClient objects
class PhotoDelivery(models.Model):
    photos = models.ManyToManyField(PhotoClient, verbose_name=_('Photos'))
    date = models.DateField(auto_now_add=True, verbose_name=_('Date'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    expiration_date = models.DateField(verbose_name=_('Expiration date'), null=True, blank=True)
    was_downloaded = models.BooleanField(default=False, verbose_name=_('Was downloaded'))
    link_to_download = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Link to download'))
    id_delivery = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('ID delivery'))
    client_name = models.CharField(max_length=255, null=True, blank=False, verbose_name=_('Client name'), default='')
    client_email = models.EmailField(max_length=255, null=True, blank=True, verbose_name=_('Client email'), default='')

    def __str__(self):
        return str(self.date)

    def save(self, *args, **kwargs):
        if not self.id_delivery:
            super().save(*args, **kwargs)
            self.generate_id_delivery()
        if not self.link_to_download:
            self.generate_link_to_download()
        if not self.expiration_date:
            self.generate_expiration_date()
        return super().save(*args, **kwargs)

    def generate_expiration_date(self):
        self.expiration_date = timezone.now() + timezone.timedelta(days=3)
        self.save()

    def generate_id_delivery(self):
        # generate a random string of 10 characters
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
        print(f"random_str, ", random_str)
        date_str = str(self.date).replace('-', random_str[0], 1)
        date_str = date_str.replace('-', random_str[9], 1)
        self.id_delivery = f'{self.id}{random_str}{date_str}'
        self.save()

    def generate_link_to_download(self):
        self.link_to_download = f'https://tchiiz.com/download/{self.id_delivery}/'
        self.save()

    def set_downloaded_status(self):
        self.was_downloaded = True
        # set the status of all photos to True
        for photo in self.photos.all():
            photo.was_downloaded = True
            photo.save()
        self.save()

    def get_photos(self):
        return self.photos.all()

    def get_photos_active(self):
        return self.photos.filter(is_active=True)

    def get_photos_expired(self):
        return self.photos.filter(is_active=False)

    def get_photos_downloaded(self):
        return self.photos.filter(was_downloaded=True)

    def get_photos_not_downloaded(self):
        return self.photos.filter(was_downloaded=False)

    def get_photos_active_not_downloaded(self):
        return self.photos.filter(is_active=True, was_downloaded=False)

    def get_photos_active_downloaded(self):
        return self.photos.filter(is_active=True, was_downloaded=True)

    def get_photos_expired_not_downloaded(self):
        return self.photos.filter(is_active=False, was_downloaded=False)

    def get_photos_expired_downloaded(self):
        return self.photos.filter(is_active=False, was_downloaded=True)

    def get_photos_not_downloaded_count(self):
        return self.photos.filter(was_downloaded=False).count()

    def get_photos_downloaded_count(self):
        return self.photos.filter(was_downloaded=True).count()

    def get_photos_active_count(self):
        return self.photos.filter(is_active=True).count()

    def get_photos_expired_count(self):
        return self.photos.filter(is_active=False).count()

    def get_photos_active_not_downloaded_count(self):
        return self.photos.filter(is_active=True, was_downloaded=False).count()

    def get_photos_active_downloaded_count(self):
        return self.photos.filter(is_active=True, was_downloaded=True).count()

    def get_photos_expired_not_downloaded_count(self):
        return self.photos.filter(is_active=False, was_downloaded=False).count()

    def get_photos_expired_downloaded_count(self):
        return self.photos.filter(is_active=False, was_downloaded=True).count()

    def get_photos_count(self):
        return self.photos.all().count()

    def get_client_name(self):
        return self.client_name

    def get_client_email(self):
        return self.client_email

    # delete files on the disk when deleting the object
    def delete_files(self, *args, **kwargs):
        for photo in self.photos.all():
            photo.delete()
        return super().delete(*args, **kwargs)


class Invoice(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('_', '--- Select a payment method ---'),
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('paypal', 'Paypal'),
        ('cashapp', 'CashApp'),
        ('venmo', 'Venmo'),
        ('zelle', 'Zelle'),
        ('check', 'Check'),
        ('others', 'Others'),
        ('none', 'N/A'),
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

    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(UserClient, on_delete=models.CASCADE, related_name="invoices", default=1)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='_')
    due_date = models.DateField(null=True, blank=True)
    old_status = models.CharField(max_length=14, choices=INVOICE_STATUS_CHOICES, default=STATUS_PENDING)
    status = models.CharField(max_length=14, choices=INVOICE_STATUS_CHOICES, default=STATUS_PENDING, )
    details = models.TextField(null=True, blank=True,
                               help_text="Details about the invoice (will be displayed to the client)")
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(null=True, blank=True,
                             help_text="Internal notes about the invoice (won't be displayed to the client)")
    history = HistoricalRecords()
    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.client.get_full_name()}"

    @classmethod
    def verify_invoice(cls, invoice_number):
        try:
            invoice = cls.objects.get(invoice_number=invoice_number)
            return invoice
        except cls.DoesNotExist:
            return None

    def clean(self):
        if not self.discount_correct():
            raise ValidationError(_('Discount must be between 0 and 100'))
        if not self.tax_rate_correct():
            raise ValidationError(_('Tax rate must be between 0 and 100'))

    def discount_correct(self):
        if 0 <= self.discount <= 100:
            return True

    def tax_rate_correct(self):
        if 0 <= self.tax_rate <= 100:
            return True

    def get_base_amount(self):
        return sum(service.get_subtotal() for service in self.invoice_services.all())

    def get_discount(self, base_amount):
        return base_amount * (self.discount / 100)

    def get_net_amount(self):
        base_amount = self.get_base_amount()
        discount_amount = self.get_discount(base_amount=base_amount)
        return round(base_amount - discount_amount, 2)

    def get_tax(self, net_amount):
        return net_amount * (self.tax_rate / 100)

    def total_amount(self):
        base_amount = self.get_base_amount()
        discount_amount = self.get_discount(base_amount=base_amount)
        net_amount = base_amount - discount_amount
        tax_amount = self.get_tax(net_amount=net_amount)
        total = net_amount + tax_amount
        return round(total, 2)

    def balance_due(self):
        return max(self.total_amount() - self.amount_paid, Decimal(0))

    @staticmethod
    def set_invoice_number():
        while True:
            invoice_number = uuid.uuid4().hex[:8]
            if not Invoice.objects.filter(invoice_number=invoice_number).exists():
                return invoice_number

    def set_status(self):
        # If status is one of these, don't change it automatically
        if self.status in [self.STATUS_CANCELLED, self.STATUS_OVERDUE]:
            return

        # Set status based on balance due
        if self.old_status == self.status:
            if self.balance_due() == 0:
                self.status = self.STATUS_PAID
            elif 0 < self.balance_due() < self.total_amount():
                self.status = self.STATUS_PARTIALLY_PAID
            else:
                self.status = self.STATUS_PENDING
        else:
            self.old_status = self.status
            # if paid, change amount paid to total amount
            if self.status == self.STATUS_PAID:
                self.amount_paid = self.total_amount()
            elif self.status == self.STATUS_PENDING:
                self.amount_paid = 0

    def get_stamp_link(self):
        stamp_links = {
            self.STATUS_PAID: 'media/Logo/paid_stamps.webp',
            self.STATUS_PARTIALLY_PAID: 'media/Logo/partial_payment.webp',
            self.STATUS_PENDING: 'media/Logo/unpaid_stamps.webp',
            self.STATUS_CANCELLED: 'media/Logo/cancelled_stamps.webp',
            self.STATUS_OVERDUE: 'media/Logo/overdue_stamps.webp'
        }
        return stamp_links.get(self.status, 'media/Logo/default_stamps.webp')

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.set_invoice_number()
        self.full_clean()  # Call full_clean to run clean method
        if self.id:
            self.set_status()
        super().save(*args, **kwargs)

    def generate_pdf_if_no_file(self, request):
        from administration.views import generate_and_process_invoice
        try:
            with open(self.get_path(), 'r'):
                print(f"File exists, {self.get_path()}")
                return True
        except FileNotFoundError:
            print(f"File does not exist, {self.get_path()}")
            # Directly call the function to generate the PDF
            generate_and_process_invoice(request, self.invoice_number)
            return False

    def get_absolute_url(self):
        return reverse('administration:view_invoice', args=[self.invoice_number])

    def get_name(self):
        client_name = (self.client.get_full_name().replace(" ", "_").replace("-", "_")
                       .replace("'", "_").lower())
        return f'{client_name}_invoice_{self.invoice_number}'

    def get_path(self):
        # return media/invoices/invoice_name
        return f'media/invoices/{self.get_name()}.pdf'

    def get_if_email_sent(self):
        if self.email_sent:
            return 'Yes'
        else:
            return 'No'

    def send_email(self, request, url):
        from utils.emails_handling import send_invoice_email
        self.generate_pdf_if_no_file(request)
        send_invoice_email(email_address=self.client.email, full_name=self.client.get_full_name(),
                           invoice_number=self.invoice_number, url=url, status=self.status, total=self.total_amount(),
                           due_date=self.due_date, subject='Invoice from Tchiiz', invoice_file=self.get_path(),
                           attachments=self.attachments.all(), test=False)
        self.email_sent = True
        self.save()

    def status_changed(self):
        return self.old_status != self.status


class InvoiceService(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='invoice_services', on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    service_quantity = models.IntegerField(default=1)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service_name} - {self.service_quantity} x {self.service_price}"

    def get_subtotal(self):
        return self.service_price * self.service_quantity


class InvoiceAttachment(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='invoice_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name
