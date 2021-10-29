from django.db import models


class ContactForm(models.Model):
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(default="", null=True, blank=True)
    subject = models.CharField(default="", null=True, blank=True, max_length=255)
    message = models.TextField(default="", null=True, blank=True)

    def __str__(self):
        return self.full_name

