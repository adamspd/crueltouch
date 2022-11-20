from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView

from client.models import UserClient, BookMe, Album, Photo
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import c_print, check_user_login, check
from .form import CustomRegisterForm, BookME
from validate_email import validate_email

User = get_user_model()


# ----------- User ----------- #
# Registering and login
def register_page(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        email = request.POST['email']
        # check email
        valid = validate_email(email)
        c_print(f"client.views:230 | email is valid: {valid}")
        if not valid:
            messages.error(request, 'Email is not valid')
            return redirect('client:register')
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
    if not request.user.is_anonymous:
        check_user_login(request)
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
    return render(request, 'client/login_registration/login.html', contexts)


# client dashboard after login
@login_required(login_url='/client/login')
def index(request):
    if request.user.is_authenticated:
        user = request.user
        username = request.user.pk
        album = Album.objects.filter(owner_id=username)
        print(album)
        return render(request, 'client/client_view/index.html', {
            'album': album,
            'user': user
        })
    else:
        return render(request, 'client/login_registration/login.html')


@login_required(login_url='/client/login')
def user_album_details(request, pk):
    selected_album = Album.objects.get(id=pk)
    return render(request, 'client/client_view/photo_details.html', {
        'album': selected_album
    })


# user defining a photo as favorite
@login_required(login_url='/client/login')
def favorite(request, pk):
    print("I was called")
    album = get_object_or_404(Album, pk=pk)
    print("the pictures id are: ", request.POST['photofav'])
    print("the album id is: ", pk)
    print("getting album, ", album)
    try:
        selected_photo = album.photo_set.get(pk=request.POST['photofav'])
        print("La liste des ids des photos liké: ", request.POST['photofav'])

        print("selected photo: ", selected_photo)
    except (KeyError, Photo.DoesNotExist):
        return render(request, 'client/client_view/photo_details.html', {
            'album': album,
            'error_message': "You didn't like a photo",
        })
    else:
        selected_photo.is_favorite = True
        selected_photo.save()
        redirect('client:album_details', album.pk)
        return render(request, 'client/client_view/photo_details.html', {
            'album': album,
        })


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
    # roos_profile = RoosProfilePhoto.objects.all()
    contexts = {'all_photos': all_photos,
                'all_clients': all_clients,
                'all_book_me': all_booked,
                'all_contacts': all_contacts,
                # 'roos_profile': roos_profile,
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
            print("roos is logged in ")
            # Redirect to a success page.
            return redirect('client:ownerislogged')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, "")
    contexts = {}
    return render(request, 'client/login_registration/log_as_owner.html', contexts)


# ----------- Owner's dashboard ----------- #


# manage users
# @login_required(login_url='/client/rooslaurore/')
# @user_passes_test(email_check, login_url='/client/rooslaurore/')
# def user_details(request, pk):
#     if request.user.is_authenticated:
#         user_client = UserClient.objects.get(id=pk)
#         album = Album.objects.filter(owner_id=user_client.id)
#         if len(album) != 0:
#             id_album = album[0].id
#             all_photos = Photo.objects.filter(album_id=id_album)
#             contexts = {
#                 'user_client': user_client,
#                 'all_photos': all_photos,
#             }
#             return render(request, 'client/user_details.html', contexts)
#         else:
#             print(len(album))
#             return render(request, 'client/user_details.html', {
#                 'user_client': user_client,
#             })
#     else:
#         return render(request, 'client/login_registration/log_as_owner.html')


# add pictures for users
# @login_required(login_url='/client/rooslaurore/')
# @user_passes_test(email_check, login_url='/client/rooslaurore/')
# def add_photos(request, pk):
#     if request.user.is_authenticated:
#         albums = Album.objects.all()
#         photos = Photo.objects.all()
#         if request.method == "POST":
#             data = request.POST
#             images = request.FILES.getlist('images')
#             for image in images:
#                 Photo.objects.create(
#                     album_id=data['category'],
#                     file=image
#                 )
#             redirect('client:ownerislogged')
#
#         return render(request, 'client/owners_view/owner_addphotos.html', {
#             'albums': albums,
#             'photos': photos,
#         })
#     else:
#         return render(request, 'client/login_registration/log_as_owner.html')


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
def bookme(request):
    return form_bookme(request)


def form_bookme(request_client):
    if request_client.method == 'POST':
        form = BookME(request_client.POST)
        if form.is_valid():
            c_print(f"client.views:222 | data from form: {form.cleaned_data}")
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            session_type = form.cleaned_data['session_type']
            place = form.cleaned_data['place']
            package = form.cleaned_data['package']
            # validate email exists in real world
            valid = validate_email(email)
            c_print(f"client.views:230 | email is valid: {valid}")
            if not valid:
                messages.error(request_client, 'Email is not valid')
                return redirect('client:bookme')
            obj = BookMe.objects.create(full_name=full_name, email=email, session_type=session_type, place=place,
                                        package=package)
            obj.save()
            c_print(f"client.views:237 | object created: {obj}")
            messages.success(request_client,
                             'Thank you, your booking has been registered successfully, you will receive an email'
                             ' shortly!')
            return redirect('client:bookme')
    else:
        form = BookME()
    contexts = {'form': form}
    return render(request_client, 'client/booking_and_promotions/bookme.html', contexts)


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
    return render(request, 'client/booking_and_promotions/information.html', contexts)


def book_anyway(request):
    return form_bookme(request)


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
