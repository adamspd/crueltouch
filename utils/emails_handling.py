from datetime import datetime

from django.template import loader
from crueltouch import settings


def get_permissions(is_booking: bool, is_contact_form: bool, is_other: bool) -> bool:
    """
    Check if the permission is granted to send email, meaning that the quota is not exceeded.
    :param is_booking: bool
    :param is_contact_form: bool
    :param is_other: bool
    :return: bool
    """
    from administration.models import PermissionsEmails
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        permission = PermissionsEmails.objects.get(date=today)
        if permission.can_send_email and is_booking:
            permission.booking_request += 1
            permission.save()
            return True
        elif permission.can_send_email and is_contact_form:
            permission.contact_form += 1
            permission.save()
            return True
        elif permission.can_send_email and is_other:
            permission.other += 1
            permission.save()
            return True
        else:
            return False
    except PermissionsEmails.DoesNotExist:
        if is_booking:
            PermissionsEmails.objects.create(
                date=today,
                booking_request=1)
            return True
        elif is_contact_form:
            PermissionsEmails.objects.create(
                date=today,
                contact_form=1)
            return True
        elif is_other:
            PermissionsEmails.objects.create(
                date=today,
                other=1)
            return True


def send_invoice_email(email_address, full_name, invoice_number, url,
                       status, total, due_date, subject, invoice_file=None, attachments=None, late=False, test=True):
    """
    Send email to client with optional attachment
    """
    if get_permissions(is_booking=True, is_contact_form=False, is_other=False):
        recipient_list = [email_address if not test else settings.ADMIN_EMAIL]

        if late:
            email_template = 'administration/email_template/late_reply_session_request_received.html'
        else:
            email_template = 'administration/email_template/notifications.html'

        html_message = loader.render_to_string(
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

        from django.core.mail import EmailMessage
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email="TCHIIZ Studio",
            to=recipient_list
        )
        email.content_subtype = 'html'  # If the message is in HTML

        # Attach additional files if any
        if invoice_file:
            # get the file from path str
            file = open(invoice_file, 'rb')
            email.attach(invoice_number + '.pdf', file.read(), 'application/pdf')
        if attachments:
            for attachment in attachments:
                email.attach_file(attachment.file.path)

        try:
            email.send()
            return True
        except:
            return False
    else:
        return False
