import random
import string

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# Create your models here.

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
        # filename without extension
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
        self.link_to_download = f'https://crueltouch.com/download/{self.id_delivery}/'
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

