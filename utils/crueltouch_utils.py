from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect


def c_print(msg, *args, **kwargs):
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg, *args, **kwargs)


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def check_user_login(request):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser or user.is_admin:
            c_print("User is superuser already")
            return redirect('client:ownerislogged')
        elif user.is_active:
            c_print("User is active but not admin")
            return redirect("client:client_homepage")
        else:
            messages.error(request, "User is anonymous")
            return redirect('client:login')
