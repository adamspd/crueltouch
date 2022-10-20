from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver

from utils.crueltouch_utils import c_print, c_formatted_print


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    c_formatted_print(
        "User {} is logged in through page {}".format(user.get_full_name(), request.META.get('HTTP_REFERER')))


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    c_print("User failed to log in spectacularly")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    c_formatted_print(
        "User logged out through page {}".format(request.META.get('HTTP_REFERER')))