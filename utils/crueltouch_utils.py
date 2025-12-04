import re
from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import mail_admins, send_mail
from django.template import loader
from django.urls import reverse


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
        if re.compile('|'.join(search_list), re.IGNORECASE).search(str(data)):
            c_print(f"SPAM DETECTED: {data[:50]}...")
            return True
    return False


def phone_number_validation(phone_number: str) -> bool:
    """
    Validates 10 digit phone numbers.
    """
    return bool(re.match(r"^[0-9]{10}$", str(phone_number)))


# --- Internal Helpers ---

def _get_base_url() -> str:
    """
    Gets the base URL for the current site.
    Works automatically for local dev and production.
    """
    current_site = Site.objects.get_current()
    # Use http for localhost/127.0.0.1, https for everything else
    protocol = 'http' if current_site.domain.startswith(('127.0.0.1', 'localhost')) else 'https'
    return f"{protocol}://{current_site.domain}"


def _send_templated_email(recipient: str, subject: str, template: str, context: dict, plain_text: str = None) -> bool:
    """
    Internal helper to send templated HTML emails.
    Reduces duplication across all email functions.
    """
    try:
        html_message = loader.render_to_string(template, context)
        send_mail(
                subject=subject,
                message=plain_text or "",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=html_message
        )
        return True
    except Exception as e:
        c_print(f"Email Error: {e}")
        return False


# --- Public Email Functions ---

def send_client_email(email_address: str, subject: str, header: str, message, footer,
                      button_label = None, button_text = None, button_link: str = None) -> bool:
    """
    Sends templated email to a client.
    """
    context = {
        'header': header,
        'message': message,
        'footer': footer,
        'subject': subject,
        'button_label': button_label,
        'button_text': button_text,
        'button_link': button_link,
    }
    return _send_templated_email(
            recipient=email_address,
            subject=subject,
            template="administration/email_template/client_email.html",
            context=context,
            plain_text=f"{header}\n\n{message}\n\n{footer}"
    )


def send_email_admin(subject: str, message: str, is_contact_form: bool = False) -> bool:
    """
    Sends notification email to admins with a dashboard link.
    """
    try:
        base_url = _get_base_url()

        # Route to appropriate admin page
        path = reverse('administration:message_list') if is_contact_form else reverse('administration:index')
        dashboard_url = f"{base_url}{path}"

        html_message = loader.render_to_string(
                "administration/email_template/admin_email.html",
                {
                    'message': message,
                    'subject': subject,
                    'dashboard_url': dashboard_url,
                }
        )

        mail_admins(
                subject=subject,
                message=message,  # Plain text fallback
                html_message=html_message
        )
        return True
    except Exception as e:
        c_print(f"Admin Email Error: {e}")
        return False


def send_password_reset_email(first_name: str, email_address: str) -> bool:
    """
    Sends default password email on account creation.
    """
    base_url = _get_base_url()
    login_link = f"{base_url}/client/login/"

    return send_client_email(
            email_address=email_address,
            subject="Account Login Details",
            header="Account Created",
            message=(
                f"Hello {first_name}, an account has been created for you. "
                f"Your username is {email_address}. "
                f"Your temporary password is: Crueltouch2022 (Change on login)."
            ),
            footer="Welcome to Tchiiz Studio.",
            button_label="Login Now",
            button_text="Login",
            button_link=login_link
    )
