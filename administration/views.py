import datetime
import glob
import os
import zipfile
from io import BytesIO
from sqlite3 import IntegrityError

import PyPDF2
from PyPDF2.constants import UserAccessPermissions
from appointment.models import Appointment, StaffMember
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from endesive import pdf as endesive_pdf
from xhtml2pdf import pisa

from administration.forms import InvoiceAttachmentFormset, InvoiceForm, InvoiceServiceFormset, UserChangePasswordForm
from administration.models import Invoice, InvoiceAttachment, PhotoClient, PhotoDelivery
from client.form import CreateAlbumForm, UpdateBook
from client.models import Album as AlbumClient, BookMe, Photo, UserClient
from crueltouch.productions import production_debug
from homepage.models import Album as AlbumHomepage, Photo as PhotoHomepage
from portfolio.models import Album as AlbumPortfolio, Photo as PhotoPortfolio
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import c_print, check_user_login, email_check, is_ajax, send_client_email, \
    work_with_file_photos


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
            time_book_taken=datetime.datetime.now() - datetime.timedelta(days=90) + datetime.timedelta(hours=i * 12),
        )


def get_book_me_by_month():
    book_me_by_month = []
    for i in range(1, 13):
        book_me_by_month.append(Appointment.objects.filter(created_at__month=i).count())
    return book_me_by_month


def get_context(request):
    base_context = get_base_context(request)  # Get the base context

    requested_session = Appointment.objects.all()
    last_10_book_me = Appointment.objects.all().order_by("-created_at")[:5]
    last_10_invoices = Invoice.objects.all().order_by("-created_at")[:5]
    photo_delivered = Photo.objects.all()
    all_clients = UserClient.objects.filter(admin=False)
    contact_forms = ContactForm.objects.all()

    this_month = Appointment.objects.filter(created_at__month=datetime.datetime.now().month)
    last_month = Appointment.objects.filter(created_at__month=datetime.datetime.now().month - 1)

    if len(this_month) == 0 and len(last_month) == 0:
        percentage = 0
    elif len(last_month) == 0:
        percentage = 100
    else:
        percentage = ((len(this_month) - len(last_month)) / len(last_month)) * 100

    book_me_by_month = get_book_me_by_month()

    # Update the base context with additional information
    base_context.update({
        'photo_delivered': photo_delivered,
        'clients': all_clients,
        'request_session': last_10_book_me,
        'contact_forms': contact_forms,
        'total_photos_delivered': len(photo_delivered),
        'total_clients': len(all_clients),
        'total_request_session': len(requested_session),
        'total_contact_forms': len(contact_forms),
        'increase_percentage': percentage,
        'book_me_by_month': book_me_by_month,
        'invoices': last_10_invoices,
    })

    return base_context


def get_base_context(request):
    user = request.user
    profile_link = None
    try:
        sm = StaffMember.objects.get(user=user)
        if sm:
            profile_link = reverse('appointment:user_profile', args=[user.id])
    except StaffMember.DoesNotExist:
        pass

    return {
        'user': user,
        'profile_link': profile_link,
    }


def login_admin(request):
    if request.user.is_authenticated:
        resp = check_user_login(request)
        if resp == "admin" or resp == "staff":
            return redirect('administration:index')
        elif resp == "active":
            return redirect('client:client_homepage')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.is_admin or user.is_staff:
                login(request, user)
                print(f"User {user} with role admin/staff logged in")
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
    context = get_context(request)
    return render(request, 'administration/view/index.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_requested_session(request):
    requested_session = BookMe.objects.all().order_by("-time_book_taken")
    context = get_base_context(request)
    context.update({'request_session': requested_session})
    return render(request, 'administration/list/list_requested_session.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def update_requested_session(request, pk):
    book = BookMe.objects.get(id=pk)
    form = UpdateBook(instance=book)
    if request.method == 'POST':
        form = UpdateBook(request.POST, instance=book)
        if form.is_valid():
            form.save()
            next_ = request.POST.get('next', '/')
            c_print("previous url is: ", next_)
            return HttpResponseRedirect(next_)
    context = get_base_context(request)
    context.update({'form': form})
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
    all_clients = UserClient.objects.filter(admin=False)
    context = get_base_context(request)
    context.update({'clients': all_clients})
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
    contact_forms = ContactForm.objects.all()
    context = get_base_context(request)
    context.update({'contact_forms': contact_forms})
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
    context = get_base_context(request)
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
        context = get_base_context(request)
        context.update({
            'albums': albums,
            'number_of_photos': len(PhotoHomepage.objects.all()),
            'homepage': True,
            'select': "Select a row",
            'title': "Add photo to homepage",
        })
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
        context = get_base_context(request)
        context.update({
            'albums': albums,
            'homepage': False,
            'number_of_photos': len(PhotoPortfolio.objects.all()),
            'select': "Select album",
            'title': "Add photo to portfolio",
        })
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
    context = get_base_context(request)
    context.update({'form': form})
    return render(request, 'administration/add/add_album.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_photos_portfolio(request):
    photos = PhotoPortfolio.objects.all()
    context = get_base_context(request)
    context.update({
        'photos': photos,
        'title': "List of photos in portfolio",
        'total_photos_label': "Total photos in portfolio",
        'portfolio': True,
    })
    return render(request, 'administration/list/list_photos_portfolio.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_photos_homepage(request):
    photos = PhotoHomepage.objects.all()
    context = get_base_context(request)
    context.update({
        'photos': photos,
        'title': "List of photos in homepage",
        'total_photos_label': "Total photos in homepage",
        'portfolio': False,
    })
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
                                  footer="Thank you for using our service ! The Tchiiz Team",
                                  is_contact_form=False, is_other=True, button_label="Download my photos now",
                                  button_text="Download", button_link=delivery.link_to_download)
            else:
                # return HttpResponseRedirect(next_)
                pass
            return JsonResponse({'link': delivery.link_to_download})
    nota_bene = _(f"If you want the website to send the link automatically to the client, please, put the client "
                  f"email in the field below. If you don't want to send the link automatically, leave the field "
                  f"empty.")
    context = get_base_context(request)
    context.update({
        'title': _("Create downloadable file"),
        'nota_bene': nota_bene,
    })

    return render(request, 'administration/add/add_downloadable_file.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def list_downloadable_files_link(request):
    deliveries = PhotoDelivery.objects.all()
    context = get_base_context(request)
    context.update({
        'deliveries': deliveries,
        'title': _("List of link to download images"),
    })
    return render(request, 'administration/list/list_created_link.html', context)


def get_downloadable_client_images(request, id_delivery):
    try:
        photos = PhotoDelivery.objects.get(id_delivery=id_delivery)
    except PhotoDelivery.DoesNotExist:
        return HttpResponseNotFound("Not found")
    context = get_base_context(request)
    context.update({
        'client_name': photos.get_client_name,
        'photos': photos.get_photos(),
        'id_delivery': id_delivery,
    })
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
def delete_delivery(request, pk):
    try:
        delivery = PhotoDelivery.objects.get(pk=pk)
        delivery.delete_files()
        messages.success(request, "Delivery deleted successfully")
        return redirect('administration:show_all_links_created')
    except PhotoDelivery.DoesNotExist:
        messages.error(request, "Delivery does not exist")
        return redirect('administration:show_all_links_created')


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


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def send_photos_for_client_to_choose_from(request):
    client_list = UserClient.objects.filter(staff=False).order_by('first_name')
    c_print(f"client list: {client_list}")
    if request.method == 'POST':
        if is_ajax(request):
            client = request.POST.get("client")
            files = request.FILES.getlist("id_photo")
            next_ = request.POST.get('next', '/')
            # get client name
            user_client = UserClient.objects.get(id=client)
            # get client album if exists
            try:
                client_album = AlbumClient.objects.get(owner=client)
            except AlbumClient.DoesNotExist:
                client_album = AlbumClient.objects.create(owner=user_client)
                # create a set of PhotoClient objects
            photos = []
            for file in files:
                f = work_with_file_photos(file)
                photo = Photo.objects.create(file=f)
                photos.append(photo)
            client_album.save()
            # if client album already has photos, add new photos to it
            if client_album.photos.all():
                client_album.photos.add(*photos)
            else:
                client_album.photos.set(photos)
            client_album.save()
            if production_debug:
                button_link = f"http://localhost:8000/client/{client_album.id}"
            else:
                button_link = f"https://tchiiz.com/client/{client_album.id}"
            # notify client
            send_client_email(
                email_address=user_client.email, subject="New images were uploaded for you to choose from",
                header="New images were uploaded for you to choose from",
                message=f"Hello {user_client.first_name}, we uploaded new photos for you to choose from! If this will "
                        f"be your first login, your password is 'Crueltouch2022' without the quote.",
                footer="Thank you for using our service ! The Tchiiz Team",
                is_contact_form=False, is_other=True, button_label="Click on the button below to do so",
                button_text="Choose photos", button_link=button_link
            )

            c_print(f"client: {user_client}", f"photos: {files}", f"next: {next_}", f"client album: {client_album}")

    context = get_base_context(request)
    context.update({
        'title': _("Send photos to client"),
        'client_list': client_list,
    })
    return render(request, 'administration/add/add_client_photos.html', context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def create_new_client(request):
    previous = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        if is_ajax(request):
            client_name = request.POST.get("client_name")
            client_email = request.POST.get("client_email")
            client_password = 'Crueltouch2022'
            c_print(f"email: {client_email}", f"client name: {client_name}", f"next: {previous}")
            try:
                client = UserClient.objects.create_user(first_name=client_name, email=client_email,
                                                        password=client_password)
            except IntegrityError:
                return JsonResponse({'error': 'Client already exists'})
            client.save()
            client.set_first_login()
            client.send_password_email()
            return JsonResponse({'success': True, 'client': client.id, 'message': 'Client created successfully !'})
    context = get_base_context(request)
    context.update({
        'title': _("Create new client"),
        'previous': previous,
    })
    return render(request, 'administration/add/add_new_client.html', context)


@login_required(login_url="/client/login/")
def must_change_password(request, pk):
    form = UserChangePasswordForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            try:
                user = UserClient.objects.get(pk=pk)
                password = form.cleaned_data['new_password1']
                if user.password_is_same(password=password):
                    messages.warning(request, _("You can't use your old password"))
                    return redirect("administration:must_change_password")
                user.password = make_password(password)
                user.save()
                user.set_not_first_login()
                user.save()
                return redirect("client:login")
            except UserClient.DoesNotExist:
                messages.warning(request, _("This user no longer exists !"))
                return redirect("client:register")
    else:
        form = UserChangePasswordForm()
    first_logon = True
    msg = "You must change your password before you can log in"
    context = get_base_context(request)
    context.update({
        'form': form,
        'first_login': first_logon,
        'msg': msg
    })
    return render(request, "administration/password/has_to_change_password.html", context)


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def view_client_album_created(request):
    album = AlbumClient.objects.all()
    context = get_base_context(request)
    context.update({
        'title': _("View chosen photos"),
        'album_list': album,
    })
    return render(request, 'administration/list/list_album_client.html', context)


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def view_all_liked_photos(request, pk):
    album = AlbumClient.objects.get(pk=pk)
    context = get_base_context(request)
    context.update({
        'title': _("View chosen photos"),
        'album': album,
        'photos_liked': album.get_photos_liked(),
        'photos_not_liked': album.get_photos_not_liked(),
        'total_photos_label': _("Total photos sent"),
    })
    return render(request, 'administration/list/list_album_client_photos.html', context)


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def delete_client_album(request, pk):
    album = AlbumClient.objects.get(pk=pk)
    album.delete_files()
    return redirect("administration:view_client_album_created")


def link_callback(uri, rel):
    from django.contrib.staticfiles import finders
    import os
    from django.conf import settings
    c_print(f"uri: {uri}", f"rel: {rel}")
    # Check if the URI is in static files
    result = finders.find(uri)
    if result:
        return result

    # Handling media files
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith('/media/'):  # If the URI starts with '/media/'
        path = os.path.join(settings.MEDIA_ROOT, uri.replace('/media/', ""))
    elif uri.startswith('media/'):  # Directly starts with 'media/'
        path = os.path.join(settings.MEDIA_ROOT, uri[6:])  # Skip 'media/' part
    else:
        # Log or print the problematic URI
        print("URI causing issue:", uri)
        return uri  # Return as is for further investigation

    # Check if the file exists
    if not os.path.isfile(path):
        print("File not found:", path)
        raise Exception(f'File with URI {uri} not found.')

    return path


def get_client_emails(request):
    query = request.GET.get('query', '')
    clients = UserClient.objects.filter(email__icontains=query).values('email', 'first_name', 'last_name',
                                                                       'phone_number', 'address')[
              :5]  # Limit to 5 results for example
    client_list = list(clients)
    return JsonResponse(client_list, safe=False)


def invoice_form(request, invoice_number=None):
    invoice_instance = None
    title = "Create Invoice"  # Default title

    if invoice_number:
        invoice_instance = Invoice.objects.get(invoice_number=invoice_number)
        title = "Edit Invoice"

    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES, instance=invoice_instance)
        attachment_formset = InvoiceAttachmentFormset(request.POST, request.FILES, prefix='attachments',
                                                      instance=invoice_instance)
        service_formset = InvoiceServiceFormset(request.POST, prefix='services', instance=invoice_instance)

        if form.is_valid() and attachment_formset.is_valid() and service_formset.is_valid():
            client = handle_client_data(form.cleaned_data)
            saved_invoice = save_invoice_and_formsets(form, attachment_formset, service_formset, client)
            return redirect('administration:generate_invoice', invoice_number=saved_invoice.invoice_number)
    else:
        form = InvoiceForm(instance=invoice_instance)
        attachment_formset = InvoiceAttachmentFormset(prefix='attachments', instance=invoice_instance)
        service_formset = InvoiceServiceFormset(prefix='services', instance=invoice_instance)

    context = {
        'form': form,
        'attachment_formset': attachment_formset,
        'service_formset': service_formset,
        'title': title
    }
    return render(request, 'administration/add/invoice_form.html', context)


def handle_client_data(form_data):
    client_email = form_data['client_email']
    first_name = form_data['client_first_name']
    last_name = form_data['client_last_name']
    client_phone = form_data['client_phone']
    client_address = form_data['client_address']

    client, created = UserClient.objects.get_or_create(
        email=client_email,
        defaults={'first_name': first_name, 'last_name': last_name, 'phone_number': client_phone,
                  'address': client_address}
    )

    if not created:
        client.first_name = first_name
        client.last_name = last_name
        client.phone_number = client_phone
        client.address = client_address
        client.save()

    return client


def save_invoice_and_formsets(form, attachment_formset, service_formset, client):
    invoice = form.save(commit=False)
    invoice.client = client
    invoice.save()

    attachment_formset.instance = invoice
    service_formset.instance = invoice
    attachment_formset.save()
    service_formset.save()
    return invoice


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def invoice_form2(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)
        attachment_formset = InvoiceAttachmentFormset(request.POST, request.FILES, prefix='attachments')
        service_formset = InvoiceServiceFormset(request.POST, prefix='services')
        if form.is_valid():
            client_email = form.cleaned_data['client_email']
            first_name = form.cleaned_data['client_first_name']
            last_name = form.cleaned_data['client_last_name']
            client_phone = form.cleaned_data['client_phone']
            client_address = form.cleaned_data['client_address']

            client, created = UserClient.objects.get_or_create(
                email=client_email,
                defaults={'first_name': first_name, 'last_name': last_name, 'phone_number': client_phone,
                          'address': client_address}
            )

            if client.phone_number is None or client.phone_number == "":
                client.phone_number = client_phone
            if client.address is None or client.address == "":
                client.address = client_address
            if client.last_name is None or client.last_name == "":
                client.last_name = last_name
            client.save()

            # Save Invoice instance to database
            invoice = form.save(commit=False)
            invoice.client = client
            invoice.save()

            # Now that the invoice instance is saved, assign it to the formsets
            attachment_formset.instance = invoice
            service_formset.instance = invoice

            if attachment_formset.is_valid() and service_formset.is_valid():
                attachment_formset.save()
                service_formset.save()
                invoice.save()
            return redirect('administration:generate_invoice', invoice_number=invoice.invoice_number)
    else:
        form = InvoiceForm()
        attachment_formset = InvoiceAttachmentFormset(prefix='attachments')
        service_formset = InvoiceServiceFormset(prefix='services')

    context = {
        'form': form,
        'attachment_formset': attachment_formset,
        'service_formset': service_formset
    }
    return render(request, 'administration/add/invoice_form.html', context)


def archive_invoice_files(invoice):
    # Define the directories
    invoice_files_dir = "media/invoices/"
    archive_dir = "media/archived_invoices/"

    # Create the archive directory if it doesn't exist
    os.makedirs(archive_dir, exist_ok=True)

    # Generate the base name for the invoice files
    invoice_base_name = invoice.get_name()

    # Find all invoice files
    invoice_files = glob.glob(f"{invoice_files_dir}{invoice_base_name}*")

    # Retrieve attachment files using the InvoiceAttachment model
    attachment_files = [attachment.file.path for attachment in InvoiceAttachment.objects.filter(invoice=invoice)]

    # Timestamp for the archive name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{archive_dir}{invoice_base_name}_{timestamp}.zip"

    # Creating the archive
    with zipfile.ZipFile(archive_name, 'w') as archive:
        for file in invoice_files + attachment_files:
            archive.write(file, os.path.basename(file))
            os.remove(file)  # Remove the original file after adding to the archive

    # Return the path of the created archive for further use (optional)
    return archive_name


def delete_invoice(request, invoice_number):
    invoice = Invoice.objects.get(invoice_number=invoice_number)
    archive_invoice_files(invoice)
    invoice.delete()
    return redirect('administration:index')


def list_invoices(request):
    invoices = Invoice.objects.all()
    return render(request, 'administration/list/list_invoices.html', {'invoices': invoices})


def view_invoice(request, invoice_number):
    invoice = Invoice.objects.get(invoice_number=invoice_number)
    pdf_path = f'media/invoices/{invoice.get_name()}.pdf'

    # Check if the PDF exists
    if not os.path.exists(pdf_path):
        generate_and_process_invoice(request, invoice.invoice_number)
    else:
        # Get the updated date info about the file (Linux/ macOS)
        updated_date = datetime.datetime.fromtimestamp(os.path.getmtime(pdf_path))

        # If the PDF updated date is not the same as the invoice updated date, regenerate the PDF
        if updated_date.replace(microsecond=0) != invoice.updated_at.replace(tzinfo=None, microsecond=0):
            # rename the old PDF by adding its updated date to the name
            os.rename(pdf_path, f'media/invoices/{invoice.get_name()}_{invoice.updated_at}.pdf')
            generate_and_process_invoice(request, invoice.invoice_number)

    # After regeneration or if no regeneration was needed, open and return the PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="{invoice.get_name()}.pdf"'
    return response


@require_POST
def update_invoice_status(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    new_status = request.POST.get('status')

    # Check if the new status is valid
    if new_status in dict(Invoice.INVOICE_STATUS_CHOICES):
        invoice.status = new_status
        invoice.save()
        # Optionally, add a message to notify the user of the update
        messages.success(request, f'Invoice {invoice_number} status updated to {new_status}.')
    else:
        # Handle invalid status update
        messages.error(request, 'Invalid status update.')

    return redirect('administration:index')


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def generate_and_process_invoice(request, invoice_number):
    os.makedirs("media/invoices", exist_ok=True)
    invoice = Invoice.objects.get(invoice_number=invoice_number)

    # Step 1: Generate Invoice PDF
    pdf_path = generate_invoice_pdf(request, invoice.invoice_number)
    # Step 2: Sign the PDF
    signed_pdf_path = sign_pdf(invoice_number)
    # Step 3: Secure the PDF
    secure_pdf_path = f'media/invoices/{invoice.get_name()}.pdf'
    secure_pdf(signed_pdf_path, secure_pdf_path, "owner_password", invoice)
    # Cleanup: Remove temporary PDFs and serve the final secured PDF
    os.remove(pdf_path)
    os.remove(signed_pdf_path)

    # Serve the final secured PDF
    with open(secure_pdf_path, 'rb') as f:
        pdf_content = f.read()
    # response = HttpResponse(pdf_content, content_type='application/pdf')
    # response['Content-Disposition'] = f'filename="{invoice.get_name()}.pdf"'
    return redirect('administration:index')


def generate_invoice_pdf(request, invoice_number):
    invoice = Invoice.objects.get(invoice_number=invoice_number)
    template_path = 'administration/add/invoice.html'
    header = "media/Logo/header_tchiiz.webp"
    footer = "media/Logo/footer_tchiiz.webp"
    if invoice.client.phone_number == "" or invoice.client.phone_number is None:
        invoice.client.phone_number = "N/A"
    if invoice.payment_method == "_":
        invoice.payment_method = "none"

    if invoice.discount > 0:
        discount_percent = round(invoice.discount, 1)
        discount_value = round(invoice.get_discount(invoice.get_base_amount()), 1)
    else:
        discount_percent = None
        discount_value = None

    if invoice.tax_rate > 0:
        tax_percent = round(invoice.tax_rate, 1)
        tax_value = round(invoice.get_tax(invoice.get_net_amount()), 1)
    else:
        tax_percent = None
        tax_value = None

    context = {
        'invoice_number': invoice.invoice_number,
        'client_name': invoice.client.get_full_name(),
        'client_email': invoice.client.email,
        'client_phone': invoice.client.phone_number,
        'services': invoice.invoice_services.all(),
        'payment_method': invoice.payment_method,
        'invoice_date': invoice.created_at,
        'details': invoice.details,
        'total': invoice.get_base_amount(),
        'header': header,
        'footer': footer,
        'stamps': invoice.get_stamp_link(),
        'url': request.build_absolute_uri(),
        'due_date': invoice.due_date,
        'discount_percent': discount_percent,
        'discount_value': discount_value,
        'amount_paid': invoice.amount_paid,
        'balance_due': invoice.balance_due(),
        'tax_percent': tax_percent,
        'tax_value': tax_value,
    }
    # Create a Django response object, and specify content_type as pdf
    filename = f"{invoice.get_name()}_generated.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'invoices', filename)

    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    buffer = BytesIO()

    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=buffer, link_callback=link_callback)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    with open(pdf_path, 'wb') as f:
        f.write(buffer.getvalue())
    buffer.close()
    return pdf_path


def sign_pdf(invoice_number):
    pdf_obj = Invoice.objects.get(invoice_number=invoice_number)
    pdf_path = f"media/invoices/{pdf_obj.get_name()}_generated.pdf"

    # Read the contents of the private key and certificate files
    with open(settings.PRIVATE_KEY_PATH, 'rb') as key_file:
        private_key_data = key_file.read()
    with open(settings.CERTIFICATE_PATH, 'rb') as cert_file:
        certificate_data = cert_file.read()

    # Load the private key and certificate
    private_key = serialization.load_pem_private_key(
        private_key_data,
        password=None,  # Assuming the private key is not password protected
        backend=default_backend()
    )
    certificate = x509.load_pem_x509_certificate(
        certificate_data,
        default_backend()
    )

    # Read the PDF
    reader = PyPDF2.PdfReader(pdf_path)
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Save to a temporary file
    tmp_pdf_path = f'media/invoices/{pdf_obj.get_name()}_tmp.pdf'
    with open(tmp_pdf_path, 'wb') as f:
        writer.write(f)

    # Sign the PDF
    dct = {
        'sigflags': 3,
        'contact': 'tchiiz.web.studio@gmail.com',
        'location': 'Naples/Florida',
        'signingdate': datetime.datetime.utcnow().strftime("D:%Y%m%d%H%M%S+00'00'"),
        'reason': 'Signing the invoice',
    }

    with open(tmp_pdf_path, 'rb') as f:
        datau = f.read()

    # Pass the certificate object directly to the sign function
    datas = endesive_pdf.cms.sign(
        datau, dct,
        private_key,  # Private key object
        certificate,  # Certificate object
        [],  # Additional certificates, if any, as a list
        'sha256'
    )

    output_pdf_path = f'media/invoices/{pdf_obj.get_name()}_signed.pdf'
    with open(output_pdf_path, 'wb') as fp:
        fp.write(datau)
        fp.write(datas)
    # delete tmp file
    os.remove(tmp_pdf_path)
    return output_pdf_path


def secure_pdf(input_pdf_path, output_pdf_path, owner_password, invoice):
    """
    Apply security restrictions to a PDF without requiring a user password to open.

    Args:
    input_pdf_path (str): Path to the input PDF file.
    output_pdf_path (str): Path where the secured PDF will be saved.
    owner_password (str): Owner password to change permissions.
    """
    with open(input_pdf_path, "rb") as input_stream:
        reader = PyPDF2.PdfReader(input_stream)
        from PyPDF2 import PdfWriter
        writer = PdfWriter()

        # Add pages
        for page in reader.pages:
            writer.add_page(page)

        # Set up permissions
        permissions = UserAccessPermissions.PRINT

        # Add metadata to the PDF like author, title, etc.
        metadata = {
            '/Author': 'tchiiz.com',
            '/Title': invoice.get_name(),
            '/Subject': 'Invoice from tchiiz.com for photography services',
            '/Producer': 'https://tchiiz.com',
            '/Creator': 'https://tchiiz.com',
            '/CreationDate': 'D:' + invoice.created_at.strftime('%Y%m%d%H%M%S'),
            '/ModDate': 'D:' + invoice.updated_at.strftime('%Y%m%d%H%M%S'),
            '/Keywords': f'tchiiz.com, invoice, services, secure, pdf, {invoice.status}',
            '/Trapped': '/False',
            '/PTEX.Fullbanner': 'This document was created by tchiiz.com',
            '/BaseURL': 'https://tchiiz.com',
        }

        writer.add_metadata(metadata)
        # Encrypt the PDF with an empty user password and the owner password
        writer.encrypt(user_password='', owner_pwd=owner_password, use_128bit=True, permissions_flag=permissions)

        with open(output_pdf_path, "wb") as output_stream:
            writer.write(output_stream)


def send_invoice_to_client(request, invoice_number):
    invoice = Invoice.objects.get(invoice_number=invoice_number)
    # get default domain
    domain = request.get_host()
    if settings.DEBUG:
        prefix = "http" + "://"
    else:
        prefix = "https://"
    url = f"{prefix}{domain}{invoice.get_absolute_url()}"

    # Check and generate the PDF if it doesn't exist
    pdf_generation_response = invoice.generate_pdf_if_no_file(request)
    if isinstance(pdf_generation_response, HttpResponseRedirect):
        return pdf_generation_response

    # Continue to send the email
    invoice.send_email(request, url)
    return redirect('administration:index')
