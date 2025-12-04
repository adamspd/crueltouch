# static_pages_and_forms/models.py
import os

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

from crueltouch.productions import production_debug
from utils.crueltouch_utils import _get_base_url, c_print, send_client_email, send_email_admin

load_dotenv()  # take environment variables from .env.

DATABASE_UPDATE = os.getenv('DATABASE_UPDATE') == 'True'
TEST_EMAIL = os.getenv('TEST_EMAIL')


class ContactForm(models.Model):
    full_name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("Full name"))
    email = models.EmailField(blank=False, null=True, verbose_name=_("Email"))
    subject = models.CharField(default="", null=True, blank=True, max_length=255, verbose_name=_("Subject"))
    message = models.TextField(null=False, blank=False, verbose_name=_("Message"))

    # meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class Quarantine(models.Model):
    # Sender Info
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(unpack_ipv4=True, blank=True, null=True)
    user_agent = models.TextField(blank=True, default="")

    # Content
    subject = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Subject"))
    message = models.TextField()

    # Internal Logic
    reason = models.TextField(help_text="Why was this quarantined?")
    is_processed = models.BooleanField(default=False, help_text="Has the background worker checked this?")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{'Processed' if self.is_processed else 'Pending'}] {self.email} - {self.reason[:30]}"


@receiver(post_save, sender=ContactForm)
def send_email_after_saving_contact_form(sender, instance, created, *args, **kwargs):
    if created:
        if production_debug or DATABASE_UPDATE:
            client_email = TEST_EMAIL
        else:
            client_email = instance.email
        c_print("Sending email to admin to notify of a new contact form submission")
        base_url = _get_base_url()
        path = reverse('pf:index_portfolio')
        portfolio_url = f"{base_url}{path}"
        sent = send_client_email(
            subject=_(f"Your message has been received") + " !",
            email_address=client_email,
            header=_("Thank you for reaching out to us") + ".",
            message=_(f"Hi {instance.full_name}, thank you for reaching out to us. We will get back to you as soon as "
                      "possible. "),
            footer=_("Have a great day! Tchiiz Studio"),
            button_label=_("Awesome!"),
            button_link=portfolio_url,
            button_text=_("Ok")
        )
        if sent:  # if email was sent
            send_email_admin(
                subject="New contact form submission",
                message=f"Hi, you have a new contact form submission from {instance.full_name} with email address "
                        f"{client_email}. The message is: \"{instance.message}\"",
                is_contact_form=True
            )
