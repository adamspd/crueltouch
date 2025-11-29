# client/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
# from validate_email import validate_email

from client.models import UserClient, BookMe, Album, Photo
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import c_print, check_user_login, check, is_ajax
from .form import CustomRegisterForm, BookME

User = get_user_model()


# ----------- User ----------- #
# Registering and login
def register_page(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        email = request.POST['email']
        # Must check if email is valid.
        # c_print(f"email: {email}")
        # valid = validate_email(email)
        # c_print(f"client.views:230 | email is valid: {valid}")
        # if not valid:
        #     messages.error(request, 'Email is not valid')
        #     return redirect('client:register')
        if check(data=request.POST['first_name']):
            messages.error(request, 'First name is not valid')
            return redirect('client:register')
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('first_name')
            messages.success(request, 'Account was created for ' + user)
            return redirect('client:login')
    else:
        form = CustomRegisterForm()
    contexts = {'form': form}
    return render(request, 'client/login_registration/register.html', contexts)


def login_page(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            print("user is logged in")
            # Check if user needs to change password
            if user.has_to_change_password:
                return redirect("administration:must_change_password", user.pk)

            # Redirect based on user type
            if user.is_admin or user.is_staff:
                return redirect('administration:index')
            else:
                return redirect('client:client_homepage')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, 'Username or Password is incorrect')
    else:
        if request.user.is_authenticated:
            # Check if logged-in user needs to change password
            if request.user.has_to_change_password:
                return redirect("administration:must_change_password", request.user.pk)

            # Redirect based on the user type
            if request.user.is_admin or request.user.is_staff:
                return redirect('administration:index')
            else:
                return redirect('client:client_homepage')

    contexts = {}
    return render(request, 'client/login_registration/login.html', contexts)


# client dashboard after login
@login_required(login_url='/client/login')
def index(request):
    if request.user.is_authenticated:
        user = request.user
        username = request.user.pk
        try:
            album = Album.objects.get(owner_id=username)
        except Album.DoesNotExist:
            album = None
        c_print(f"found album: {album}")
        return render(request, 'client/client_view/index.html', {
            'album': album,
            'user': user
        })
    else:
        return render(request, 'client/login_registration/login.html')


@login_required(login_url='/client/login')
def user_album_details(request, pk):
    try:
        selected_album = Album.objects.get(id=pk)
        selected_album.set_viewed()
    except Album.DoesNotExist:
        selected_album = None
    return render(request, 'client/client_view/photo_details.html', {
        'album': selected_album
    })


# user defining a photo as favorite
@login_required(login_url='/client/login')
@csrf_exempt
def favorite(request):
    c_print(f"favorite is called with request: {request.POST}")
    if request.method == 'POST':
        photo_id = request.POST.get('photo_id')
        c_print(f"favorite is called with pk {photo_id}")
        if is_ajax(request):
            try:
                photo = Photo.objects.get(id=photo_id)
                photo.set_favorite()
                return JsonResponse({'like photo': 'ok'})
            except Photo.DoesNotExist:
                return JsonResponse({'error': 'Photo does not exist'})


@login_required(login_url='/client/login')
@csrf_exempt
def dislike(request):
    c_print(f"un-favorite is called with request")
    if request.method == 'POST':
        photo_id = request.POST.get('photo_id')
        c_print(f"favorite is called with pk {photo_id}")
        if is_ajax(request):
            try:
                photo = Photo.objects.get(id=photo_id)
                photo.set_not_favorite()
                return JsonResponse({'dislike photo': 'ok'})
            except Photo.DoesNotExist:
                return JsonResponse({'error': 'Photo does not exist'})


# ----------- Useful functions ----------- #
def email_check(user):
    if user.email.startswith('roos.laurore5') or user.email.startswith('adamspierredavid'):
        return True
    else:
        return False


def context(request):
    all_booked = BookMe.objects.all()
    all_photos = Photo.objects.all()
    all_clients = UserClient.objects.all()
    all_contacts = ContactForm.objects.all()
    contexts = {'all_photos': all_photos,
                'all_clients': all_clients,
                'all_book_me': all_booked,
                'all_contacts': all_contacts,
                }
    return contexts


# ----------- Owner's Login ----------- #
def owner(request):
    if request.user.is_authenticated:
        check_user_login(request)
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            print("admin is logged in")
            # Redirect to a success page.
            return redirect('client:ownerislogged')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, "")
    contexts = {}
    return render(request, 'client/login_registration/log_as_owner.html', contexts)


def logout_user(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            logout(request)
            return redirect('administration:login')
        else:
            logout(request)
            return redirect('client:login')
    return redirect('client:register')


# ----------- Booking ----------- #d
def book_me(request):
    return form_book_me(request)


def book_me_session(request, click_id):
    if click_id == 1:
        request.session['click_id'] = click_id
        request.session['location'] = "orlando"
        request.session['package'] = "3"
    elif click_id == 2:
        request.session['click_id'] = click_id
        request.session['package'] = "7"
    elif click_id == 3:
        request.session['click_id'] = click_id
        request.session['package'] = "15"
    elif click_id == 4:
        request.session['click_id'] = click_id
        request.session['package'] = "30"
    return form_book_me(request)


def form_book_me(request_client):
    if request_client.method == 'POST':
        form = BookME(request_client.POST)
        c_print(f"form is valid: {form.is_valid()}")
        c_print(f"form errors: {form.errors}")
        if form.is_valid():
            c_print(f"client.views:222 | data from form: {form.cleaned_data}")
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            session_type = form.cleaned_data['session_type']
            place = form.cleaned_data['place']
            package = form.cleaned_data['package']
            desired_date = form.cleaned_data['desired_date']
            address = form.cleaned_data['address']
            phone_number = form.cleaned_data['phone_number']
            c_print(
                f"client.views:232 | data from form: {full_name}, {email}, {session_type}, {place}, {package}, "
                f"{desired_date}, {address}, {phone_number}")
            if check(full_name):
                messages.error(request_client, "Form not valid, try again !")
                return redirect('client:book_me')
            # validate email exists in real world
            valid = True
            # valid = validate_email(email)
            # valid = True
            c_print(f"client.views:230 | email is valid: {valid}")
            if not valid:
                messages.error(request_client, 'Email is not valid')
                return redirect('client:book_me')
            obj = BookMe.objects.create(
                full_name=full_name,
                email=email,
                session_type=session_type,
                place=place,
                package=package,
                desired_date=desired_date,
                address=address,
                phone_number=phone_number,
            )
            obj.save()
            c_print(f"client.views:263 | object saved: {obj}")
            messages.success(request_client,
                             _('Thank you, your booking has been registered successfully, you will receive an email '
                               'shortly!'))
            return redirect('client:book_me')
    else:
        if request_client.session.get('click_id') == 1:
            form = BookME(initial={'place': request_client.session.get('location'),
                                   'package': request_client.session.get('package')})
            clear_session(request_client)
        elif request_client.session.get('click_id') == 2:
            form = BookME(initial={'package': request_client.session.get('package')})
            clear_session(request_client)
        elif request_client.session.get('click_id') == 3:
            form = BookME(initial={'package': request_client.session.get('package')})
            clear_session(request_client)
        elif request_client.session.get('click_id') == 4:
            form = BookME(initial={'package': request_client.session.get('package')})
            clear_session(request_client)
            # clear session
        else:
            form = BookME()
    contexts = {'form': form}
    return render(request_client, 'client/booking_and_promotions/bookme.html', contexts)


def clear_session(request):
    request.session.clear()


def book_anyway(request):
    return form_book_me(request)


# ----------- Payment ----------- #
def paynow(request):
    return render(request, 'client/booking_and_promotions/payment.html')


def success_payment(request):
    return render(request, 'client/success.html')


class AdminView(RedirectView):
    pattern_name = 'admin/'
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.pattern_name,
                       args=args, kwargs=kwargs,
                       current_app=self.request.resolver_match.namespace)
