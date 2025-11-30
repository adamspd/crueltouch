# utils/email_handling.py
import smtplib

from django.core.mail import EmailMessage
from django.template import loader

from crueltouch import settings


def create_email_content(email_template, context):
    return loader.render_to_string(email_template, context)


def attach_files_to_email(email, invoice_number, invoice_file, attachments):
    if invoice_file:
        try:
            with open(invoice_file, 'rb') as file:
                email.attach(invoice_number + '.pdf', file.read(), 'application/pdf')
        except IOError as e:
            print(f"Error attaching invoice file: {e}")
            return False

    if attachments:
        for attachment in attachments:
            try:
                email.attach_file(attachment.file.path)
            except Exception as e:
                print(f"Error attaching file: {e}")
                return False
    return True


def send_email_(subject, html_message, recipient_list, invoice_number, invoice_file, attachments):
    email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email="TCHIIZ Studio",
            to=recipient_list
    )
    email.content_subtype = 'html'  # HTML content

    if not attach_files_to_email(email, invoice_number, invoice_file, attachments):
        return False

    try:
        email.send()
        return True
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        return False


def send_invoice_email(email_address, full_name, invoice_number, url, status, total, due_date, subject,
                       invoice_file=None, attachments=None, late=False, test=True):
    """
    Send email to a client with an optional attachment.
    """

    recipient_list = [settings.ADMIN_EMAIL] if test else [email_address]
    email_template = 'administration/email_template/late_reply_session_request_received.html' if late else \
        'administration/email_template/notifications.html'

    html_message = create_email_content(
            email_template,
            {
                'full_name': full_name,
                'due_date': due_date,
                'status': status,
                'total': total,
                'invoice_number': invoice_number,
                'url': url,
            }
    )

    # Send email to client or admin
    if not send_email_(subject, html_message, recipient_list, invoice_number, invoice_file, attachments):
        return False

    # Send a copy to admins
    admin_subject = f"Admin Copy: {subject}"
    admin_recipient_list = [settings.ADMIN_EMAIL, settings.OTHER_ADMIN_EMAIL]
    return send_email_(admin_subject, html_message, admin_recipient_list, invoice_number, invoice_file, attachments)
