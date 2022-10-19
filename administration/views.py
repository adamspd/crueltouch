import datetime
from datetime import timedelta, timezone

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from client.models import BookMe, UserClient, Photo
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import check_user_login, c_print


# Create your views here.

def delete_all_book_me():
    BookMe.objects.all().delete()


def create_book_me():
    for i in range(0, 120):
        BookMe.objects.create(
            full_name="roos",
            email="adamspd.developer@gmail.com",
            session_type="portrait",
            place="studio",
            package="35",
            status="pending",
            # last week
            time_book_taken=datetime.datetime.now() - timedelta(days=90) + timedelta(hours=i * 12),
        )


def get_book_me_by_month():
    book_me_by_month = []
    for i in range(1, 13):
        book_me_by_month.append(BookMe.objects.filter(time_book_taken__month=i).count())
    return book_me_by_month


def get_context(request):
    requested_session = BookMe.objects.all()
    # get last 10 book_me
    last_10_book_me = BookMe.objects.all().order_by("-time_book_taken")[:10]
    photo_delivered = Photo.objects.all()
    all_clients = UserClient.objects.filter(admin=False)
    contact_forms = ContactForm.objects.all()

    # get all book_me from this month
    this_month = BookMe.objects.filter(time_book_taken__month=datetime.datetime.now().month)

    # get all book_me from last month
    last_month = BookMe.objects.filter(time_book_taken__month=datetime.datetime.now().month - 1)

    # increasing/decreasing percentage of book_me compared to last month
    if len(this_month) == 0 and len(last_month) == 0:
        percentage = 0
    elif len(last_month) == 0:
        percentage = 100
    else:
        percentage = ((len(this_month) - len(last_month)) / len(last_month)) * 100

    # return table of book_me by month
    book_me_by_month = get_book_me_by_month()

    contexts = {'photo_delivered': photo_delivered,
                'clients': all_clients,
                'request_session': last_10_book_me,
                'contact_forms': contact_forms,
                'total_photos_delivered': len(photo_delivered),
                'total_clients': len(all_clients),
                'total_request_session': len(requested_session),
                'total_contact_forms': len(contact_forms),
                'increase_percentage': percentage,
                'book_me_by_month': book_me_by_month,
                }
    return contexts


def login_admin(request):
    # if request.user.is_authenticated:
    #     check_user_login(request)
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.is_admin:
                login(request, user)
                print("roos is logged in ")
                # Redirect to a success page.
                return redirect('administration:index')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, "")
    contexts = {}
    return render(request, 'client/login_registration/log_as_owner.html', contexts)


def admin_index(request):
    user = request.user
    context = get_context(request)
    context['user'] = user
    return render(request, 'administration/view/index.html', context)


def list_requested_session(request):
    user = request.user
    requested_session = BookMe.objects.all().order_by("-time_book_taken")
    context = {'request_session': requested_session,
               'user': user}
    return render(request, 'administration/list/list_requested_session.html', context)


def list_requested_user(request):
    user = request.user
    all_clients = UserClient.objects.filter(admin=False)
    context = {'clients': all_clients,
               'user': user}
    return render(request, 'administration/list/list_user.html', context)


def list_contact_form(request):
    user = request.user
    contact_forms = ContactForm.objects.all()
    context = {'contact_forms': contact_forms,
               'user': user}
    return render(request, 'administration/list/list_contact_forms.html', context)


def help_view(request):
    user = request.user
    context = {'user': user}
    return render(request, 'administration/view/help.html', context)