"""
:author: Adams Pierre David
:version: 1.0
"""
import re
from datetime import datetime

from django.contrib import messages
from django.core.mail import mail_admins, send_mail
from django.shortcuts import redirect
from django.template import loader

from administration.models import PermissionsEmails


def c_print(msg, *args, **kwargs):
    """
    :param msg: string
    :param args: string
    :param kwargs: string
    :return: None
    :note: Print msg as django's normal output
    """
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg, *args, **kwargs)


def c_formatted_print(msg, *args, **kwargs):
    """
    :param msg: string
    :param args: string
    :param kwargs: string
    :return: None
    :note: Print msg as django's normal output
    """
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg.format(*args, **kwargs))


def is_ajax(request):
    """
    :author: Adams Pierre David
    :version: 1.0
    :param request: request
    :return: Check request's meta to determine if it's ajax
    """
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def check_user_login(request):
    """
    :author: Adams Pierre David
    :version: 1.0
    :param request: request
    :return: Check request's meta to determine if it's ajax
    """
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser or user.is_admin:
            c_print("User is superuser already")
            return redirect('administration:index')
        elif user.is_active:
            c_print("User is active but not admin")
            return redirect("client:client_homepage")
        else:
            messages.error(request, "User is anonymous")
            return redirect('client:login')


def email_check(user):
    if user.email.startswith('roos.laurore5') or user.email.startswith('adamspierredavid'):
        return True
    else:
        return False


def get_permissions(is_booking: bool, is_contact_form: bool, is_other: bool) -> bool:
    """
    Check if the permission is granted to send email, meaning that the quota is not exceeded.
    :param is_booking: bool
    :param is_contact_form: bool
    :param is_other: bool
    :return: bool
    """
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


def send_session_request_received_email(email_address, full_name: str, session_type: str, place: str, package: str,
                                        status: str, total: str, estimated_response_time: str, subject: str,
                                        late: bool) -> bool:
    """
    Send email to client when session request is received
    :param email_address: client's email address
    :param full_name: client's full name
    :param session_type: session type
    :param place: session place
    :param package: session package
    :param status: session status
    :param total: session total estimated cost
    :param estimated_response_time: estimated response time
    :param subject: email subject
    :param late: bool, if the request is late
    :return: bool
    """
    if get_permissions(is_booking=True, is_contact_form=False, is_other=False):
        recipient_list = [
            email_address,
            # settings.ADMIN_EMAIL,
        ]
        if late:
            email_template = 'administration/email_template/late_reply_session_request_received.html'
        else:
            email_template = 'administration/email_template/session_request_received.html'
        html_message = loader.render_to_string(
            email_template,
            {
                'full_name': full_name,
                'session_type': session_type.title(),
                'place': place.title(),
                'package': package,
                'status': status,
                'total': total,
                'estimated_response_time': estimated_response_time,
            }
        )
        c_print(f"The total is {total}")
        mail = send_mail(
            subject=subject,
            message="",
            from_email="adamspd.webmaster@gmail.com",
            html_message=html_message,
            recipient_list=recipient_list
        )
        if mail == 1:
            return True
        else:
            return False
    else:
        return False


# send notification to admin when request session received
def notify_admin_session_request_received_via_email(today: str, client_name: str, client_email: str, session_type: str,
                                                    place: str, package: str, status: str, total: str,
                                                    estimated_response_time: str, subject: str) -> bool:
    """
    Send email to admin when session request is received
    :param today: today's date
    :param client_name: client's full name
    :param client_email: client's email address
    :param session_type: session type
    :param place: session place
    :param package: session package
    :param status: session status
    :param total: session total estimated cost
    :param estimated_response_time: estimated response time
    :param subject: email subject
    :return: bool
    """
    if get_permissions(is_booking=True, is_contact_form=False, is_other=False):
        html_message = loader.render_to_string(
            'administration/email_template/notify_admin_session_request_received.html',
            {
                'today': today,
                'client_name': client_name,
                'client_email': client_email,
                'session_type': session_type.title(),
                'place': place.title(),
                'package': package,
                'status': status,
                'total': total,
                'estimated_response_time': estimated_response_time,
            }
        )
        mail_admins(subject=subject,
                    message="",
                    html_message=html_message)
        return True
    else:
        return False


def get_estimated_response_time() -> str:
    """
    Get estimated response time for session request. It's one week from today.
    :return: one week from today
    """
    from datetime import datetime, timedelta
    return (datetime.now() + timedelta(days=7)).strftime("%B %d, %Y")


# get today's date
def get_today_date():
    """
    Get today's date
    :return: today's date
    """
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")


# status of session request changed
def status_change_email(book_me, subject: str) -> bool:
    """
    Send email to client when session request status is changed
    :param book_me: BookMe object
    :param subject: email subject
    :return: bool
    """
    recipient_list = [
        book_me.email,
        # settings.ADMIN_EMAIL,
    ]
    if book_me.status == 'accepted':
        message = "Your booking session request has been accepted. More information may be sent to you. " \
                  "Thank you for choosing us."
        footer = "Regards, CruelTouch Team"
        header = "Booking Session Request Accepted"
    elif book_me.status == 'canceled':
        message = "Your booking session request has been canceled. " \
                  "We are sorry for the inconvenience."
        footer = "Regards, CruelTouch Team"
        header = "Booking Session Request Canceled"
    else:
        message = "Your booking session request has been completed. " \
                  "Thank you for choosing us."
        footer = "Regards, CruelTouch Team"
        header = "Booking Session Request Completed"
    html_message = loader.render_to_string(
        "administration/email_template/session_request_status_changed.html",
        {
            'full_name': book_me.full_name,
            'session_type': book_me.session_type.title(),
            'place': book_me.place.title(),
            'package': book_me.package,
            'status': book_me.status,
            'total': book_me.estimated_total,
            'message': message,
            'header': header,
            'footer': footer,
        }
    )
    mail = send_mail(
        subject=subject,
        message="",
        from_email="adamspd.webmaster@gmail.com",
        html_message=html_message,
        recipient_list=recipient_list
    )
    if mail == 1:
        return True
    else:
        return False


def check(data) -> bool:
    """
    Check if data contains any word from the list
    :param data: data to check
    :return: bool
    """
    c_print(f"Checking {data}")
    if data is not None:
        search_list = [
            "http", "https", "www.", "%", "business", "robot", " earn", "#1",
            "# 1", "financial", "Make money", "Making money", "Invest $1", "Passive income", "NFT",
        ]
        if re.compile('|'.join(search_list), re.IGNORECASE).search(data):
            c_print(f"Found spam word in data")
            return True


def send_client_email(email_address, subject: str, header: str, message: str, footer: str, is_contact_form: bool,
                      is_other: bool) -> bool:
    """
    This function sends email to client, and returns True if email is sent successfully.
    It sends email when client filled out the contact form or when admin wants to reply to client.
    It checks if there is a permission to send email, meaning that the number of emails sent today is less than 300.
    Before sending email, it checks if the email address is valid and exists.
    Use models `ContactForm` and `PermissionsEmails`.
    :param email_address: client's email address
    :param subject: subject of the email
    :param header: header of the email
    :param message: message of the email
    :param footer: footer of the email
    :param is_contact_form: True if email is sent when client filled out the contact form
    :param is_other: True if email is sent when admin wants to reply to client
    :return: True if email is sent successfully
    """
    if get_permissions(is_booking=False, is_contact_form=is_contact_form, is_other=is_other):
        recipient_list = [
            email_address,
            # settings.ADMIN_EMAIL,
        ]
        html_message = loader.render_to_string(
            "administration/email_template/client_email.html",
            {
                'header': header,
                'message': message,
                'footer': footer,
                'subject': subject,
            }
        )
        mail = send_mail(
            subject=subject,
            message="",
            from_email="crueltouch.photo.web@gmail.com",
            html_message=html_message,
            recipient_list=recipient_list
        )
        if mail == 1:
            return True
        else:
            return False
    else:
        return False


def send_email_admin(subject: str, message: str, is_contact_form: bool, is_other: bool) -> bool:
    """
    This function sends email to admin, and returns True if email is sent successfully.
    It sends email when client filled out the contact form to notify admin.
    It checks if there is a permission to send email, meaning that the number of emails sent today is less than 300.
    Use models `PermissionsEmails`.
    :param subject: subject of the email
    :param message: message of the email
    :param is_contact_form: True if email is sent when client filled out the contact form
    :param is_other: True if email is sent when admin wants to reply to client
    :return: True if email is sent successfully
    """
    get_permissions(is_booking=False, is_contact_form=is_contact_form, is_other=is_other)
    html_message = loader.render_to_string(
        "administration/email_template/admin_email.html",
        {
            'message': message,
            'subject': subject,
        }
    )
    mail_admins(subject=subject,
                message="",
                html_message=html_message)
    return True
