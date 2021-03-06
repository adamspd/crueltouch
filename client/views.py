from deprecated.classic import deprecated
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

from .form import CustomRegisterForm, BookME, UpdateBook, CreateAlbumForm
from client.models import UserClient, BookMe, Album, OwnerProfilePhoto, Photo
from homepage.models import Album as AlbumHomepage
from homepage.models import Photo as PhotoHomepage
from portfolio.models import Album as AlbumPortfolio
from portfolio.models import Photo as PhotoPortfolio
from static_pages_and_forms.models import ContactForm

User = get_user_model()


# ----------- User ----------- #
# Registering and login
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
    return render(request, 'client/login_registration/register.html', contexts)


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
    return render(request, 'client/login_registration/login.html', contexts)


# client dashboard after login
@login_required(login_url='login')
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


@login_required(login_url='login')
def user_album_details(request, pk):
    selected_album = Album.objects.get(id=pk)
    return render(request, 'client/client_view/photo_details.html', {
        'album': selected_album
    })


# user defining a photo as favorite
@login_required(login_url='login')
def favorite(request, pk):
    print("I was called")
    album = get_object_or_404(Album, pk=pk)
    print("the pictures id are: ", request.POST['photofav'])
    print("the album id is: ", pk)
    print("getting album, ", album)
    try:
        selected_photo = album.photo_set.get(pk=request.POST['photofav'])
        print("La liste des ids des photos lik??: ", request.POST['photofav'])

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
    return render(request, 'client/login_registration/log_as_owner.html', contexts)


@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def when_owner_logged(request):
    if request.user.is_authenticated:
        contexts = context(request)
        print('owner is logged')
        return render(request, 'client/owners_view/owner_dashboard.html', contexts)
    else:
        print("Can't login")
        return render(request, 'client/login_registration/log_as_owner.html')


# ----------- Owner's dashboard ----------- #
# add photo to homepage
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def add_photos_homepage(request):
    if request.user.is_authenticated:
        albums = AlbumHomepage.objects.all()
        photos = PhotoHomepage.objects.all()

        if request.method == "POST":
            data = request.POST
            images = request.FILES.getlist('images')
            for image in images:
                post_photos = PhotoHomepage.objects.create(
                    album_id=data['row'],
                    file=image
                )
            redirect('client:ownerislogged')

        return render(request, 'client/owners_view/addphotos_website.html', {
            'albums': albums,
            'photos': photos,
        })
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# add photo to portfolio page
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def add_photos_portfolio(request):
    if request.user.is_authenticated:
        albums = AlbumPortfolio.objects.all()
        photos = PhotoPortfolio.objects.all()

        if request.method == "POST":
            data = request.POST
            images = request.FILES.getlist('images')
            for image in images:
                PhotoPortfolio.objects.create(
                    album_id=data['alb'],
                    file=image
                )
            redirect('client:ownerislogged')

        return render(request, 'client/owners_view/addphotos_portfolio.html', {
            'albums': albums,
            'photos': photos,
        })
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# Owner help dashboard
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_help(request):
    if request.user.is_authenticated:
        contexts = context(request)
        return render(request, 'client/owners_view/owner_help.html', contexts)
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# Owner list of client
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_client(request):
    if request.user.is_authenticated:
        contexts = context(request)
        return render(request, 'client/owners_view/owner_client.html', contexts)
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# manage contact form
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_contact_form(request):
    if request.user.is_authenticated:
        all_contact = ContactForm.objects.all()
        return render(request, 'client/owners_view/owner_contact_form.html', {'all_contact': all_contact})
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# views all booking
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def owner_bookme(request):
    if request.user.is_authenticated:
        all_book = BookMe.objects.all()
        return render(request, 'client/owners_view/owner_bookmes.html', {'all_book': all_book})
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# manage users
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def user_details(request, pk):
    if request.user.is_authenticated:
        user_client = UserClient.objects.get(id=pk)
        album = Album.objects.filter(owner_id=user_client.id)
        if len(album) != 0:
            id_album = album[0].id
            all_photos = Photo.objects.filter(album_id=id_album)
            contexts = {
                'user_client': user_client,
                'all_photos': all_photos,
            }
            return render(request, 'client/user_details.html', contexts)
        else:
            print(len(album))
            return render(request, 'client/user_details.html', {
                'user_client': user_client,
            })
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# MANAGE BOOKING
# update booking
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def updateBookme(request, pk):
    book = BookMe.objects.get(id=pk)
    form = UpdateBook(instance=book)
    if request.method == 'POST':
        form = UpdateBook(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('client:ownerislogged')

    context = {'form': form}
    return render(request, 'client/owners_view/owner_update_bookme.html', context)


# delete booking
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def delete_book(request, pk):
    book = BookMe.objects.get(id=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('client:ownerislogged')
    context = {'book': book}
    return render(request, 'client/owners_view/delete_book.html', context)


# add pictures for users
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def add_photos(request, pk):
    if request.user.is_authenticated:
        albums = Album.objects.all()
        photos = Photo.objects.all()
        if request.method == "POST":
            data = request.POST
            images = request.FILES.getlist('images')
            for image in images:
                Photo.objects.create(
                    album_id=data['category'],
                    file=image
                )
            redirect('client:ownerislogged')

        return render(request, 'client/owners_view/owner_addphotos.html', {
            'albums': albums,
            'photos': photos,
        })
    else:
        return render(request, 'client/login_registration/log_as_owner.html')


# Creation of albums
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def creationofalbum(request):
    if request.method == 'POST':
        form = CreateAlbumForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client:add_photos_portfolio')
    else:
        form = CreateAlbumForm()
    context = {'form': form}
    return render(request, 'client/owners_view/create_album_portfolio.html', context)


# delete a picture from portfolio page
@login_required(login_url='/client/rooslaurore/')
@user_passes_test(email_check, login_url='/client/rooslaurore/')
def delete_photo(request, pk):
    photo = PhotoPortfolio.objects.get(id=pk)
    if request.method == 'POST':
        photo.delete()
        return redirect('client:add_photos_portfolio')
    context = {'photo': photo}
    return render(request, 'client/owners_view/delete_photo_portfolio.html', context)


def superuserlogin(request):
    return render(request, 'client/login_registration/superusers.html')


def logout_user(request):
    if request.user.is_superuser:
        logout(request)
        return redirect('client:owner')
    else:
        logout(request)
        return redirect('client:login')


# ----------- Booking ----------- #
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
            client_name = form.cleaned_data['full_name']
            client_email = form.cleaned_data['email']
            return render(request=request_client, template_name='client/booking_and_promotions/scheduletimewithme.html',
                          context={
                              "client_name": client_name,
                              "client_email": client_email
                          })
    else:
        form = BookME()
    contexts = {'form': form}
    return render(request_client, 'client/booking_and_promotions/bookme.html', contexts)


@deprecated("Don't use it because of user experience")
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


@deprecated("Works with the information function (previous), hence, no use")
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
