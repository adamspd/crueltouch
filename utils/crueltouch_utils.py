from datetime import datetime


def c_print(msg, *args, **kwargs):
    print(datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg, *args, **kwargs)


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def first_login(user):
    return not user.has_to_change_password
