from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.

class PermissionsEmails(models.Model):
    date = models.CharField(max_length=255, null=False, blank=False, unique=True, verbose_name=_('The date'))
    number_of_emails = models.IntegerField(default=0, verbose_name=_('Number of emails sent for booking request'))

    def __str__(self):
        return str(self.date)

    class Meta:
        verbose_name_plural = _('Permissions Emails')

    @property
    def can_send_email(self):
        return self.number_of_emails < 300



