import datetime
import os
import zipfile
from datetime import timedelta
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from administration.models import PhotoDelivery, PhotoClient
from client.form import CreateAlbumForm, UpdateBook
from client.models import BookMe, UserClient, Photo
from homepage.models import Album as AlbumHomepage
from homepage.models import Photo as PhotoHomepage
from portfolio.models import Album as AlbumPortfolio
from portfolio.models import Photo as PhotoPortfolio
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import email_check, c_print, send_client_email, is_ajax


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
                if request.GET.get('next') is not None:
                    c_print(f"next is {request.GET.get('next')}")
                    return redirect(request.GET.get('next'))
                return redirect('administration:index')
        else:
            # Return an 'invalid login' error message.
            messages.info(request, "")
    else:
        if request.user.is_authenticated:
            c_print(f"user is authenticated {request.user}, {request.user.is_staff}")
            if request.user.is_staff:
                c_print(f"user is superuser {request.user}")
                return redirect('administration:index')
    contexts = {}
    return render(request, 'client/login_registration/log_as_owner.html', contexts)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def admin_index(request):
    user = request.user
    context = get_context(request)
    context['user'] = user
    return render(request, 'administration/view/index.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_requested_session(request):
    user = request.user
    requested_session = BookMe.objects.all().order_by("-time_book_taken")
    context = {'request_session': requested_session,
               'user': user}
    return render(request, 'administration/list/list_requested_session.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def update_requested_session(request, pk):
    user = request.user
    book = BookMe.objects.get(id=pk)
    form = UpdateBook(instance=book)
    if request.method == 'POST':
        form = UpdateBook(request.POST, instance=book)
        if form.is_valid():
            form.save()
            next_ = request.POST.get('next', '/')
            c_print("previous url is: ", next_)
            return HttpResponseRedirect(next_)
    context = {
        'user': user,
        'form': form,
    }
    return render(request, 'administration/edit/update_requested_session.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def delete_requested_session(request, pk):
    try:
        book = BookMe.objects.get(id=pk)
        book.delete()
        messages.success(request, "BookMe deleted successfully")
    except BookMe.DoesNotExist:
        messages.warning(request, "BookMe does not exist")
    return redirect('administration:session_list')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_requested_user(request):
    user = request.user
    all_clients = UserClient.objects.filter(admin=False)
    context = {'clients': all_clients,
               'user': user}
    return render(request, 'administration/list/list_user.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def send_late_booking_confirmation_email_to_users(request, pk):
    try:
        user = BookMe.objects.get(pk=pk)
        if not user.get_if_email_was_sent_boolean():
            sent = user.send_late_booking_confirmation_email()
            if sent:
                messages.success(request, _("Email sent successfully"))
            else:
                messages.warning(request, _("Email not sent"))
        else:
            messages.warning(request, _("Email already sent"))
    except BookMe.DoesNotExist:
        messages.warning(request, _("Session request does not exist"))
    return redirect('administration:session_list')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_contact_form(request):
    user = request.user
    contact_forms = ContactForm.objects.all()
    context = {'contact_forms': contact_forms,
               'user': user}
    return render(request, 'administration/list/list_contact_forms.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def delete_contact_form(request, pk):
    try:
        contact_form = ContactForm.objects.get(id=pk)
        contact_form.delete()
        messages.success(request, "Contact form deleted successfully")
        return redirect('administration:message_list')
    except ContactForm.DoesNotExist:
        messages.error(request, "Contact form does not exist")
        return redirect('administration:message_list')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def help_view(request):
    user = request.user
    context = {'user': user}
    return render(request, 'administration/view/help.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def add_photos_homepage(request):
    if request.user.is_authenticated:
        albums = AlbumHomepage.objects.all()
        if request.method == "POST":
            data = request.POST
            images = request.FILES.getlist("images_homepage")
            for image in images:
                PhotoHomepage.objects.create(
                    album_id=data['row'],
                    file=image
                )

            redirect('administration:index')
        context = {
            'user': request.user,
            'albums': albums,
            'number_of_photos': len(PhotoHomepage.objects.all()),
            'homepage': True,
            'select': "Select a row",
            'title': "Add photo to homepage",
        }
        return render(request, 'administration/add/add_photos.html', context)
    else:
        return redirect('administration:login')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def add_photos_portfolio(request):
    if request.user.is_authenticated:
        albums = AlbumPortfolio.objects.all()
        if request.method == "POST":
            data = request.POST
            images = request.FILES.getlist("images_homepage")
            c_print(f"method post {data}")
            c_print(f"images: {images}")
            for image in images:
                pc = PhotoPortfolio.objects.create(
                    album_id=data['row'],
                    file=image
                )
                c_print(f"photo created: {pc}")

            redirect('administration:index')
        context = {
            'user': request.user,
            'albums': albums,
            'homepage': False,
            'number_of_photos': len(PhotoPortfolio.objects.all()),
            'select': "Select album",
            'title': "Add photo to portfolio",
        }
        return render(request, 'administration/add/add_photos.html', context)
    else:
        return redirect('administration:login')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def add_album_portfolio(request):
    if request.method == 'POST':
        form = CreateAlbumForm(request.POST)
        if form.is_valid():
            form.save()
            next_ = request.POST.get('next', '/')
            c_print("previous url is: ", next_)
            return HttpResponseRedirect(next_)
    else:
        form = CreateAlbumForm()
    context = {'form': form}
    return render(request, 'administration/add/add_album.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_photos_portfolio(request):
    photos = PhotoPortfolio.objects.all()
    user = request.user
    context = {
        'photos': photos,
        'user': user,
        'title': "List of photos in portfolio",
        'total_photos_label': "Total photos in portfolio",
        'portfolio': True,
    }
    return render(request, 'administration/list/list_photos_portfolio.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_photos_homepage(request):
    photos = PhotoHomepage.objects.all()
    user = request.user
    context = {
        'photos': photos,
        'user': user,
        'title': "List of photos in homepage",
        'total_photos_label': "Total photos in homepage",
        'portfolio': False,
    }
    return render(request, 'administration/list/list_photos_portfolio.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def delete_photo_portfolio(request, pk):
    try:
        photo = PhotoPortfolio.objects.get(id=pk)
        photo.delete()
        messages.success(request, "Photo deleted successfully")
        return redirect('administration:list_photos_portfolio')
    except PhotoPortfolio.DoesNotExist:
        messages.error(request, "Photo does not exist")
        return redirect('administration:list_photos_portfolio')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def delete_photo_homepage(request, pk):
    try:
        photo = PhotoHomepage.objects.get(id=pk)
        photo.delete()
        messages.success(request, "Photo deleted successfully")
        return redirect('administration:list_photos_homepage')
    except PhotoHomepage.DoesNotExist:
        messages.error(request, "Photo does not exist")
        return redirect('administration:list_photos_homepage')


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def create_downloadable_file(request):
    if request.method == 'POST':
        if is_ajax(request):
            files = request.FILES.getlist("images_client_link")
            client_name = request.POST.get("client_name")
            client_email = request.POST.get("client_email")
            next_ = request.POST.get('next', '/')
            c_print(f"email: {client_email}", f"client name: {client_name}", f"next: {next_}")
            # create a set of PhotoClient objects
            photos = []
            for file in files:
                photo = PhotoClient.objects.create(file=file)
                photos.append(photo)
            delivery = PhotoDelivery(client_name=client_name, client_email=client_email)
            delivery.save()
            delivery.photos.set(photos)
            delivery.save()
            if client_email != "":
                send_client_email(email_address=client_email, subject="New images were uploaded for you",
                                  header="New images were uploaded for you",
                                  message=f"Hello {client_name}, you can download your photos now !",
                                  footer="Thank you for using our service ! The Crueltouch Team",
                                  is_contact_form=False, is_other=True, button_label="Download my photos now",
                                  button_text="Download", button_link=delivery.link_to_download)
            else:
                # return HttpResponseRedirect(next_)
                pass
            return JsonResponse({'link': delivery.link_to_download})
    nota_bene = _(f"If you want the website to send the link automatically to the client, please, put the client "
                  f"email in the field below. If you don't want to send the link automatically, leave the field "
                  f"empty.")
    context = {
        'title': _("Create downloadable file"),
        'nota_bene': nota_bene,
    }

    return render(request, 'administration/add/add_downloadable_file.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_downloadable_files_link(request):
    deliveries = PhotoDelivery.objects.all()
    context = {
        'deliveries': deliveries,
        'title': _("List of link to download images"),
    }
    return render(request, 'administration/list/list_created_link.html', context)


def get_downloadable_client_images(request, id_delivery):
    try:
        photos = PhotoDelivery.objects.get(id_delivery=id_delivery)
    except PhotoDelivery.DoesNotExist:
        return HttpResponseNotFound("Not found")
    context = {
        'client_name': photos.get_client_name,
        'photos': photos.get_photos(),
        'id_delivery': id_delivery,
    }
    return render(request, 'administration/download/downloadable_images.html', context)


def download_zip(request, id_delivery):
    # -> zipfile.ZipFile:
    try:
        photos = PhotoDelivery.objects.get(id_delivery=id_delivery)
    except PhotoDelivery.DoesNotExist:
        return HttpResponseNotFound("Not found")

    zip_subdir = "photos"
    zip_filename = "%s.zip" % zip_subdir
    s = BytesIO()
    zf = zipfile.ZipFile(s, "w")
    photos.set_downloaded_status()
    photos = photos.get_photos()
    for photo in photos:
        print(f"file path: {photo.file.path}")
        # get file name
        filename = os.path.basename(photo.file.path)
        print(f"file name: {filename}")
        zip_path = os.path.join(zip_subdir, filename)
        zf.write(photo.file.path, zip_path)
    zf.close()
    resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    return resp


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def send_photo_via_account(request, pk):
    # try:
    #     photo = PhotoClient.objects.get(id=pk)
    # except PhotoClient.DoesNotExist:
    #     return HttpResponseNotFound("Not found")
    # if request.method == 'POST':
    #     if is_ajax(request):
    #         client_name = request.POST.get("client_name")
    #         client_email = request.POST.get("client_email")
    #         next_ = request.POST.get('next', '/')
    #         c_print(f"email: {client_email}", f"client name: {client_name}", f"next: {next_}")
    #         delivery = PhotoDelivery(client_name=client_name, client_email=client_email)
    #         delivery.save()
    #         delivery.photos.add(photo)
    #         delivery.save()
    #         if client_email != "":
    #             send_client_email(email_address=client_email, subject="New images were uploaded for you",
    #                               header="New images were uploaded for you",
    #                               message=f"Hello {client_name}, you can download your photos now !",
    #                               footer="Thank you for using our service ! The Crueltouch Team",
    #                               is_contact_form=False, is_other=True, button_label="Download my photos now",
    #                               button_text="Download", button_link=delivery.link_to_download)
    #         else:
    #             # return HttpResponseRedirect(next_)
    #             pass
    #         return JsonResponse({'link': delivery.link_to_download})
    # nota_bene = _(f"If you want the website to send the link automatically to the client, please, put the client "
    #               f"email in the field below. If you don't want to send the link automatically, leave the field "
    #               f"empty.")
    context = {
        'title': _("Create downloadable file"),
        #   'nota_bene': nota_bene,
    }
    return render(request, 'administration/add/add_downloadable_file.html', context)
