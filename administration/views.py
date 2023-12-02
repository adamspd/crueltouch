import datetime
import os
import zipfile
from datetime import timedelta
from io import BytesIO
from sqlite3 import IntegrityError

from appointment.models import Appointment, StaffMember
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.staticfiles import finders
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from xhtml2pdf import pisa

from administration.forms import UserChangePasswordForm, InvoiceForm
from administration.models import PhotoDelivery, PhotoClient
from client.form import CreateAlbumForm, UpdateBook
from client.models import BookMe, UserClient, Photo, Album as AlbumClient
from crueltouch.productions import production_debug
from homepage.models import Album as AlbumHomepage
from homepage.models import Photo as PhotoHomepage
from portfolio.models import Album as AlbumPortfolio
from portfolio.models import Photo as PhotoPortfolio
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import check_user_login, email_check, c_print, send_client_email, is_ajax, \
    work_with_file_photos


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
        book_me_by_month.append(Appointment.objects.filter(created_at__month=i).count())
    return book_me_by_month


def get_context(request):
    base_context = get_base_context(request)  # Get the base context

    requested_session = Appointment.objects.all()
    last_10_book_me = Appointment.objects.all().order_by("-created_at")[:10]
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
    })

    return base_context


def get_base_context(request):
    user = request.user
    profile_link = "#"
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
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    sUrl = settings.STATIC_URL  # Typically /static/
    sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
    mUrl = settings.MEDIA_URL  # Typically /media/
    mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        print(f"uri: {uri}")
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            print("URI causing issue:", uri)  # Add this line
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (sUrl, mUrl)
        )
    return path


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def invoice_form(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)
        print(f"request received {form.data}")
        if form.is_valid():
            # You might want to save the form data in session or database
            print(f"form is valid {form.cleaned_data}")
            request.session['invoice_data'] = form.cleaned_data
            return redirect('administration:generate_invoice')
    else:
        form = InvoiceForm()

    return render(request, 'administration/add/invoice_form.html', {'form': form})


@login_required(login_url="/administration/login/")
@user_passes_test(email_check, login_url='/administration/login/')
def generate_invoice(request):
    template_path = 'administration/add/invoice.html'
    context = request.session.get('invoice_data', {})
    header = "https://tchiiz.com/media/photos_clients/crueltouch_header.png"
    footer = "https://productionsdesign.com/wp-content/uploads/2022/06/footer.png"
    paid_stamps = 'https://tchiiz.com/media/photos_clients/paid_ct_ww.png'
    context['header'] = header
    context['footer'] = footer
    if context.get('payment_method', '') != 'None':
        context['paid_stamps'] = paid_stamps

    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')

    # if download
    # response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # if view
    # invoice filename should be invoice_client_name_invoice_number.pdf
    invoice_number = context.get('invoice_number', '')
    # remove spaces and - from name
    client_name = context.get('client_name', '')
    client_name = client_name.replace(" ", "_")
    client_name = client_name.replace("-", "_")
    response['Content-Disposition'] = f'filename="{client_name}_invoice_{invoice_number}.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response, link_callback=link_callback)
    # clean session
    request.session['invoice_data'] = {}
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
