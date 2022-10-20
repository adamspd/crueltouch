from datetime import datetime

from django.contrib import messages
from django.core.mail import mail_admins, send_mail
from django.shortcuts import redirect
from django.template import loader


def c_print(msg, *args, **kwargs):
    """
    @author: Adams Pierre David
    @version: 1.0
    @param msg: string
    @param args: string
    @param kwargs: string
    @return: None
    @note: Print msg as django's normal output
    """
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg, *args, **kwargs)


def c_formatted_print(msg, *args, **kwargs):
    """
        @author: Adams Pierre David
        @version: 1.0
        @param msg: string
        @param args: string
        @param kwargs: string
        @return: None
        @note: Print msg as django's normal output
        """
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg.format(*args, **kwargs))


def is_ajax(request):
    """
    @author: Adams Pierre David
    @version: 1.0
    @param request: request
    @return: Check request's meta to determine if it's ajax
    """
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def check_user_login(request):
    """
    @author: Adams Pierre David
    @version: 1.0
    @param request: request
    @return: Check request's meta to determine if it's ajax
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


def send_session_request_received_email(email_address, full_name: str, session_type: str, place: str, package: bool,
                                        status: str, total: str, estimated_response_time: str, subject: str):
    recipient_list = [
        email_address,
        # settings.ADMIN_EMAIL,
    ]
    html_message = loader.render_to_string(
        'administration/email_template/session_request_received.html',
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
    send_mail(
        subject=subject,
        message="",
        from_email="no-reply.crueltouch-webmaster@gmail.com",
        html_message=html_message,
        recipient_list=recipient_list
    )


# send notification to admin when request session received
def notify_admin_session_request_received_via_email(today: str, client_name: str, client_email: str, session_type: str,
                                                    place: str, package: bool, status: str, total: str,
                                                    estimated_response_time: str, subject: str):
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


def get_estimated_response_time():
    from datetime import datetime, timedelta
    return (datetime.now() + timedelta(days=7)).strftime("%B %d, %Y")


# get today's date
def get_today_date():
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")
