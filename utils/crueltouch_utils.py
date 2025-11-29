# utils/crueltouch_utils.py
"""
:author: Adams Pierre David
:version: 1.0
"""
import os
import re
from datetime import datetime

from PIL import Image
from django.core.mail import mail_admins, send_mail
from django.template import loader

from crueltouch import settings
from crueltouch.productions import production_debug
from utils.emails_handling import get_permissions


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
        if user.is_superuser or user.is_staff:
            return 'admin'
        elif user.is_active:
            return 'active'
    return 'anonymous'


def email_check(user):
    if user.is_superuser or user.is_staff:
        return True
    else:
        return False


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
            from_email="TCHIIZ Studio",
            html_message=html_message,
            recipient_list=recipient_list
        )
        if mail == 1:
            return True
        else:
            return False
    else:
        return False


# get today's date
def get_today_date():
    """
    Get today's date
    :return: today's date
    """
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")


def get_today_date_formatted(date_format: str):
    """
    Get today's date
    :param date_format: format of the date
    :return: today's date
    """
    from datetime import datetime
    return datetime.now().strftime(date_format)


def check(data) -> bool:
    """
    Check if data contains any word from the list
    :param data: data to check
    :return: bool
    """
    c_print(f"Checking {data}")
    if data is not None:
        search_list = [
            "http", "https", "www.", "%", "business", "robot", " earn", "#1", "income",
            "# 1", "financial", "Make money", "Making money", "Invest $1", "Passive income", "NFT", "invest"
        ]
        if re.compile('|'.join(search_list), re.IGNORECASE).search(data):
            c_print(f"Found spam word in data")
            return True


def send_client_email(email_address, subject: str, header: str, message: str, footer: str, button_label: str,
                      button_text: str, button_link: str, is_contact_form: bool, is_other: bool) -> bool:
    """
    This function sends email to client, and returns True if email is sent successfully.
    It sends email when client filled out the contact form or when admin wants to reply to client.
    It checks if there is a permission to send email, meaning that the number of emails sent today is less than 300.
    Before sending email, it checks if the email address is valid and exists.
    Use models `ContactForm` and `PermissionsEmails`.
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
                'button_label': button_label,
                'button_text': button_text,
                'button_link': button_link,
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


# phone number validation
def phone_number_validation(phone_number: str) -> bool:
    """
    Check if phone number is valid
    :param phone_number: phone number
    :return: bool
    """
    phone_number_regex = re.compile(r"^[0-9]{10}$")
    if phone_number_regex.search(phone_number):
        return True
    else:
        return False


def send_password_reset_email(first_name: str, email_address: str) -> bool:
    """
    This function sends email to client with his password, and returns True if email is sent successfully.
    Use models `PermissionsEmails`.
    """
    if get_permissions(is_booking=False, is_contact_form=False, is_other=True):
        recipient_list = [
            email_address,
        ]
        if production_debug:
            button_link = "http://localhost:8000/client/login/"
        else:
            button_link = "https://tchiiz.com/client/login/"
        html_message = loader.render_to_string(
            "administration/email_template/client_email.html",
            {
                'header': "Login details",
                'message': f"Hello {first_name},we have created an account for you on our website "
                           f"so that we can communicate confidential data to you in a secure manner. Your username "
                           f"is {email_address}. Your password is: Crueltouch2022, you'll be asked to change it when "
                           f"you log in for the first time.",
                'footer': "Thank you for your trust in Tchiiz Studio.",
                'subject': "Login details on Tchiiz website",
                'button_label': "Login right now !",
                'button_text': "Login",
                'button_link': button_link,
            }
        )
        mail = send_mail(
            subject="Password reset",
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
