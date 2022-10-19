from django.db import models


class ContactForm(models.Model):
    full_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(blank=False, null=True)
    subject = models.CharField(default="", null=True, blank=True, max_length=255)
    message = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.full_name

