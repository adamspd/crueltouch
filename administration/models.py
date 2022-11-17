from django.db import models
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



