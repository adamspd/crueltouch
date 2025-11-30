import re
from datetime import datetime

from django.conf import settings
from django.core.mail import mail_admins, send_mail
from django.template import loader


# --- Debugging ---

def c_print(msg, *args, **kwargs):
    """
    Console print with timestamp.
    Useful for server logs.
    """
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg, *args, **kwargs)


def c_formatted_print(msg, *args, **kwargs):
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg.format(*args, **kwargs))


# --- Input Validation ---

def check(data) -> bool:
    """
    Spam filter: Returns True if spam keywords are found.
    """
    if data is not None:
        search_list = [
            "http", "https", "www.", "%", "business", "robot", " earn", "#1", "income",
            "# 1", "financial", "Make money", "Making money", "Invest $1", "Passive income", "NFT", "invest"
        ]
        # Check against regex
        if re.compile('|'.join(search_list), re.IGNORECASE).search(str(data)):
            c_print(f"SPAM DETECTED: {data[:50]}...")
            return True
    return False


def phone_number_validation(phone_number: str) -> bool:
    """
    Validates 10 digit phone numbers.
    """
    return bool(re.match(r"^[0-9]{10}$", str(phone_number)))


# --- Email Wrappers ---

def send_client_email(email_address, subject, header, message, footer,
                      button_label=None, button_text=None, button_link=None,
                      is_contact_form=False, is_other=False):
    """
    Simplified email sender to clients.
    """
    try:
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

        send_mail(
                subject=subject,
                message="",  # Text message fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_address],
                html_message=html_message
        )
        return True
    except Exception as e:
        c_print(f"Client Email Error: {e}")
        return False


def send_email_admin(subject: str, message: str, is_contact_form: bool = False, is_other: bool = False) -> bool:
    """
    RESTORED: Sends notification email to admins.
    Stripped of the old 'get_permissions' check since that model is gone.
    """
    try:
        html_message = loader.render_to_string(
                "administration/email_template/admin_email.html",
                {
                    'message': message,
                    'subject': subject,
                }
        )
        mail_admins(
                subject=subject,
                message="",
                html_message=html_message
        )
        return True
    except Exception as e:
        c_print(f"Admin Email Error: {e}")
        return False


def send_password_reset_email(first_name: str, email_address: str) -> bool:
    """
    Sends the default password email on account creation.
    """
    # Auto-detect domain for development vs production
    base_url = "http://localhost:8000" if settings.DEBUG else "https://tchiiz.com"
    login_link = f"{base_url}/client/login/"

    try:
        html_message = loader.render_to_string(
                "administration/email_template/client_email.html",
                {
                    'header': "Account Created",
                    'message': (f"Hello {first_name}, an account has been created for you. "
                                f"Your username is {email_address}. "
                                f"Your temporary password is: Crueltouch2022 (Change on login)."),
                    'footer': "Welcome to Tchiiz Studio.",
                    'subject': "Your Tchiiz Studio Account",
                    'button_label': "Login Now",
                    'button_text': "Login",
                    'button_link': login_link,
                }
        )

        send_mail(
                subject="Account Login Details",
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_address],
                html_message=html_message
        )
        return True
    except Exception as e:
        c_print(f"Password Email Error: {e}")
        return False


# --- Legacy Helper ---

def is_ajax(request):
    """
    Kept for legacy support in other apps.
    """
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
