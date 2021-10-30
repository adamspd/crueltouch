from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model

# Create your views here.
from django.urls import reverse
from django.views.generic import ListView, RedirectView

from crueltouch import settings
from .form import CustomRegisterForm, BookME
from client.models import UserClient, BookMe, Album, OwnerProfilePhoto
# from client.models import Photo, UserClient, BookMe, RoosProfilePhoto
from static_pages_and_forms.models import ContactForm

User = get_user_model()


def register_page(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('first_name')
            messages.success(request, 'Account was created for ' + user)
            return redirect('client:login')
    else:
        form = CustomRegisterForm()
    contexts = {'form': form}
    return render(request, 'client/register.html', contexts)


def login_page(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            print("user is logged in ")
            # Redirect to a success page.
            return redirect('client:client_homepage')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, 'Username or Password is incorrect')

    contexts = {}
    return render(request, 'client/login.html', contexts)


@login_required(login_url='login')
def index(request):
    if request.user.is_authenticated:
        user = request.user
        username = request.user.pk
        album = Album.objects.filter(owner_id=username)
        print(album)
        return render(request, 'client/index.html', {
            'album': album,
            'user': user
        })
    else:
        return render(request, 'client/login.html')


@login_required(login_url='login')
def user_album_details(request, pk):
    selected_album = Album.objects.get(id=pk)
    return render(request, 'client/photo_details.html', {
        'album': selected_album
    })


def owner(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            print("roos is logged in ")
            # Redirect to a success page.
            return redirect('client:ownerislogged')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, "")
    contexts = {}
    return render(request, 'client/log_as_owner.html', contexts)


def email_check(user):
    if user.email.startswith('roos.laurore5') or user.email.startswith('adamspierredavid'):
        return True
    else:
        return False


def context(request):
    all_booked = BookMe.objects.all()
    # all_photos = Photo.objects.all()
    all_photos = []
    all_clients = UserClient.objects.all()
    all_contacts = ContactForm.objects.all()
    # roos_profile = RoosProfilePhoto.objects.all()
    contexts = {'all_photos': all_photos,
                'all_clients': all_clients,
                'all_book_me': all_booked,
                'all_contacts': all_contacts,
                # 'roos_profile': roos_profile,
                }
    return contexts


@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def when_owner_logged(request):
    if request.user.is_authenticated:
        contexts = context(request)
        return render(request, 'client/owner_index.html', contexts)
    else:
        return render(request, 'client/log_as_owner.html')


@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_help(request):
    if request.user.is_authenticated:
        contexts = context(request)
        return render(request, 'client/owner_help.html', contexts)
    else:
        return render(request, 'client/log_as_owner.html')


@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_client(request):
    if request.user.is_authenticated:
        contexts = context(request)
        return render(request, 'client/owners_client.html', contexts)
    else:
        return render(request, 'client/log_as_owner.html')


@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_contact_form(request):
    if request.user.is_authenticated:
        all_contact = ContactForm.objects.all()
        return render(request, 'client/owners_contact_form.html', {'all_contact': all_contact})
    else:
        return render(request, 'client/log_as_owner.html')


@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def user_details(request, pk):
    if request.user.is_authenticated:
        user_client = UserClient.objects.get(id=pk)
        # all_photos = Photo.objects.filter(owner_id=user_client.id)
        all_photos = []
        contexts = {
            'user_client': user_client,
            'all_photos': all_photos,
        }
        return render(request, 'client/user_details.html', contexts)
    else:
        return render(request, 'client/log_as_owner.html')


# @login_required(login_url='login')
# def favorite(request, photo_id):
#     photo = get_object_or_404(Photo, pk=photo_id)
#     try:
#         selected_photo = photo.objects.get(pk=request.POST['photo'])
#     except (KeyError, Photo.DoesNotExist):
#         return render(request, 'client/index.html', {
#             'photo': photo,
#             'error_message': "You didn't like a photo",
#         })
#     else:
#         selected_photo.is_favorite = True
#         selected_photo.save()
#         return render(request, 'client/index.html', {
#             'photo': photo,
#         })


def superuserlogin(request):
    return render(request, 'client/superusers.html')


def logout_user(request):
    if request.user.is_superuser:
        logout(request)
        return redirect('client:owner')
    else:
        logout(request)
        return redirect('client:login')


def bookme(request):
    return form_bookme(request)


def form_bookme(request_client):
    if request_client.method == 'POST':
        form = BookME(request_client.POST)
        if form.is_valid():
            form.save()
            email_subject = f'New Form from: {form.cleaned_data["full_name"]}'
            email_message = f'Request from: {form.cleaned_data["email"]}\n\n' \
                            f'session_type: {form.cleaned_data["session_type"]}\n\n' \
                            f'place => \n{form.cleaned_data["place"]}'
            # send_mail(subject=email_subject, message=email_message,
            #           from_email=settings.CONTACT_EMAIL, recipient_list=settings.ADMIN_EMAILS)
            return redirect('homepage:index')
    else:
        form = BookME()
    contexts = {'form': form}
    return render(request_client, 'client/bookme.html', contexts)


def book_anyway(request):
    return form_bookme(request)


def information(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('first_name')
            messages.success(request, 'Account was created for ' + user)
            return redirect('client:login')
    else:
        form = CustomRegisterForm()
    contexts = {'form': form}
    return render(request, 'client/information.html', contexts)


class AdminView(RedirectView):
    pattern_name = 'admin/'
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.pattern_name,
                       args=args, kwargs=kwargs,
                       current_app=self.request.resolver_match.namespace)
