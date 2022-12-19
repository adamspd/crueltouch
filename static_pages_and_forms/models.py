from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from crueltouch import email_secrets
from crueltouch.email_secrets import DATABASE_UPDATE
from crueltouch.productions import production_debug
from utils.crueltouch_utils import c_print, send_client_email, send_email_admin


class ContactForm(models.Model):
    full_name = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("Full name"))
    email = models.EmailField(blank=False, null=True, verbose_name=_("Email"))
    subject = models.CharField(default="", null=True, blank=True, max_length=255, verbose_name=_("Subject"))
    message = models.TextField(null=False, blank=False, verbose_name=_("Message"))

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


@receiver(post_save, sender=ContactForm)
def send_email_after_saving_contact_form(sender, instance, created, *args, **kwargs):
    if created:
        if production_debug or DATABASE_UPDATE:
            client_email = email_secrets.TEST_EMAIL
        else:
            client_email = instance.email
        c_print("client.models:235 | Sending email to admin to notify of a new contact form submission")
        sent = send_client_email(
            subject=_(f"Your message has been received") + " !",
            email_address=client_email,
            header=_("Thank you for reaching out to us") + ".",
            message=_(f"Hi {instance.full_name}, thank you for reaching out to us. We will get back to you as soon as "
                      "possible. "),
            footer=_("Have a great day! CruelTouch Team"),
            is_contact_form=True,
            is_other=False,
            button_label=_("Awesome!"),
            button_link="https://crueltouch.com/portfolio/",
            button_text=_("Ok")
        )
        if sent:  # if email was sent
            send_email_admin(
                subject="New contact form submission",
                message=f"Hi, you have a new contact form submission from {instance.full_name} with email address "
                        f"{client_email}. The message is: \"{instance.message}\"",
                is_contact_form=True,
                is_other=False
            )
