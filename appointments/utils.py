import datetime
import uuid


def printing(msg, *args, **kwargs):
    """
    :param msg: string
    :param args: string
    :param kwargs: string
    :return: None
    :note: Print msg as django's normal output
    """
    print(datetime.datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg, *args, **kwargs)


def formatted_print(msg, *args, **kwargs):
    """
    :param msg: string
    :param args: string
    :param kwargs: string
    :return: None
    :note: Print msg as django's normal output
    """
    print(datetime.datetime.now().strftime('[%d/%m/%Y  %H:%M:%S] '), msg.format(*args, **kwargs))


def is_ajax(request):
    """
    :author: Adams Pierre David
    :version: 1.0
    :param request: request
    :return: Check request's meta to determine if it's ajax
    """
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def generate_random_id():
    """
    :author: Adams Pierre David
    :version: 1.0
    :return: Generate a random id long 32 characters
    """
    return uuid.uuid4().hex


def get_timestamp():
    """
    :author: Adams Pierre David
    :version: 1.0
    :return: Get current timestamp without "."
    """
    timestamp = str(datetime.datetime.now().timestamp())
    return timestamp.replace('.', '')


def get_available_slots(date, appointments):
    start_time = datetime.datetime.combine(date, datetime.time(hour=9))
    end_time = datetime.datetime.combine(date, datetime.time(hour=16, minute=30))
    slot_duration = datetime.timedelta(minutes=30)
    slots = []
    while start_time <= end_time:
        slots.append(start_time)
        start_time += slot_duration
    for appointment in appointments:
        start_time = appointment.get_start_time()
        end_time = appointment.get_end_time()
        slots = [slot for slot in slots if not (start_time <= slot <= end_time)]
    return [slot.strftime('%I:%M %p') for slot in slots]
