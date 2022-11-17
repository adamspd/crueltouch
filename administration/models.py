from django.db import models


# Create your models here.

class PermissionsEmails(models.Model):
    date = models.CharField(max_length=255, null=False, blank=False, unique=True)
    number_of_emails = models.IntegerField(default=0)

    def __str__(self):
        return str(self.date)

    class Meta:
        verbose_name_plural = "Permissions Emails"

    @property
    def can_send_email(self):
        return self.number_of_emails < 300



