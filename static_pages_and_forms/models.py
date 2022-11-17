from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from utils.crueltouch_utils import c_print, send_client_email, send_email_admin


class ContactForm(models.Model):
    full_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(blank=False, null=True)
    subject = models.CharField(default="", null=True, blank=True, max_length=255)
    message = models.TextField(null=False, blank=False)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


@receiver(post_save, sender=ContactForm)
def send_email_after_saving_contact_form(sender, instance, created, *args, **kwargs):
    if created:
        c_print("client.models:235 | Sending email to admin to notify of a new contact form submission")
        sent = send_client_email(
            subject="Your message has been received !",
            email_address=instance.email,
            header="Thank you for reaching out to us.",
            message=f"Hi {instance.full_name}, thank you for reaching out to us. We will get back to you as soon as "
                    f"possible. ",
            footer="Have a great day! CruelTouch Team",
            is_contact_form=True,
            is_other=False
        )
        if sent:  # if email was sent
            send_email_admin(
                subject="New contact form submission",
                message=f"Hi, you have a new contact form submission from {instance.full_name} with email address "
                        f"{instance.email}. The message is: \"{instance.message}\"",
                is_contact_form=True,
                is_other=False
            )
