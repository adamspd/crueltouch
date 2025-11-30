# administration/views.py
import datetime
import os
import zipfile
from typing import Any

from appointment.models import Appointment, StaffMember
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.db import models
from django.db.models import Count, Func
from django.db.models.functions import TruncMonth
from django.http import FileResponse, HttpResponse, HttpResponseNotFound, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from administration.forms import (InvoiceAttachmentFormset, InvoiceForm, InvoiceServiceFormset, UserChangePasswordForm)
from administration.models import Invoice, PhotoClient, PhotoDelivery
from administration.pdf_utils import perform_invoice_generation
from client.forms import CreateAlbumForm
from client.models import Album as AlbumClient, Photo, UserClient
from homepage.models import Album as AlbumHomepage, Photo as PhotoHomepage
from portfolio.models import Album as AlbumPortfolio, Photo as PhotoPortfolio
from static_pages_and_forms.models import ContactForm
from utils.crueltouch_utils import c_print, check, send_client_email


# ==============================================================================
# DASHBOARD HELPERS (RESTORED)
# ==============================================================================

class Month(Func):
    """
    Custom DB function to extract month for SQLite/Chart data.
    """
    function = "STRFTIME"
    template = "%(function)s('%%m', %(expressions)s)"
    output_field = models.CharField()


def get_base_context(request):
    """
    Base context with user and optional StaffMember profile link.
    """
    user = request.user
    profile_link = None
    try:
        sm = StaffMember.objects.get(user=user)
        if sm:
            profile_link = reverse('appointment:user_profile', args=[user.id])
    except StaffMember.DoesNotExist:
        pass

    base_context: dict[str, Any] = {
        'user': user,
        'profile_link': profile_link,
    }
    return base_context


def get_appointments_by_month():
    """
    Returns appointment counts for the last 12 months (rolling window).
    Returns tuple: (month_labels, appointment_counts)
    """
    today = datetime.date.today()
    # Start from 11 months ago
    start_date = today - relativedelta(months=11)
    start_date = start_date.replace(day=1)

    # Get appointments grouped by month for the last 12 months
    monthly_counts = (
        Appointment.objects
        .filter(created_at__gte=start_date)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Build dictionary of results
    monthly_dict = {entry["month"].strftime("%Y-%m"): entry["count"] for entry in monthly_counts}

    # Generate all 12 months and their labels
    month_labels = []
    appointment_counts = []

    current = start_date
    for i in range(12):
        month_key = current.strftime("%Y-%m")
        month_label = current.strftime("%b %Y")  # e.g. "Jan 2024"

        month_labels.append(month_label)
        appointment_counts.append(monthly_dict.get(month_key, 0))

        current += relativedelta(months=1)

    return month_labels, appointment_counts


def get_context(request):
    """
    Aggregates all stats for the Admin Dashboard.
    """
    base_context = get_base_context(request)

    requested_session = Appointment.objects.all()
    last_10_book_me = Appointment.objects.all().order_by("-created_at")[:5]
    last_10_invoices = Invoice.objects.all().order_by("-created_at")[:5]
    photo_delivered = Photo.objects.all()
    all_clients = UserClient.objects.filter(is_superuser=False)
    contact_forms = ContactForm.objects.all()

    # Calculate Month-over-Month percentage increase
    current_month = datetime.datetime.now().month
    appointments_by_month = Appointment.objects.annotate(month=TruncMonth('created_at')).filter(
            created_at__month__in=[current_month, current_month - 1]
    )
    this_month = [a for a in appointments_by_month if a.created_at.month == current_month]
    last_month = [a for a in appointments_by_month if a.created_at.month == current_month - 1]

    this_month_count = len(this_month)
    last_month_count = len(last_month)

    if this_month_count == 0 and last_month_count == 0:
        percentage = 0
    elif last_month_count == 0:
        percentage = 100
    else:
        percentage = ((this_month_count - last_month_count) / last_month_count) * 100

    # Get last 12 months data
    month_labels, appointment_counts = get_appointments_by_month()

    # Update the base context with additional information
    base_context.update({
        'photo_delivered': photo_delivered,
        'clients': all_clients,
        'request_session': last_10_book_me,
        'contact_forms': contact_forms,
        'total_photos_delivered': photo_delivered.count(),
        'total_clients': all_clients.count(),
        'total_request_session': requested_session.count(),
        'total_contact_forms': contact_forms.count(),
        'increase_percentage': percentage,
        'month_labels': month_labels,
        'appointment_counts': appointment_counts,
        'invoices': last_10_invoices,
    })
    return base_context


# ==============================================================================
# AUTH & DASHBOARD VIEW
# ==============================================================================

def login_admin(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('administration:index')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('administration:index')
        else:
            messages.error(request, "Access Denied. Staff only.")

    return render(request, 'client/login_registration/log_as_owner.html')


@staff_member_required(login_url='administration:login')
def admin_index(request):
    if request.user.has_to_change_password:
        return redirect('administration:must_change_password', pk=request.user.id)

    # Restored: Use the full context generator
    context = get_context(request)
    return render(request, 'administration/view/index.html', context)


@staff_member_required(login_url='administration:login')
def help_view(request):
    return render(request, 'administration/view/help.html', get_base_context(request))


# ==============================================================================
# INVOICE MANAGEMENT
# ==============================================================================

@staff_member_required(login_url='administration:login')
def list_invoices(request):
    invoices = Invoice.objects.all().order_by('-created_at')
    return render(request, 'administration/list/list_invoices.html', {'invoices': invoices})


@staff_member_required(login_url='administration:login')
def invoice_form(request, invoice_number=None):
    invoice = None
    title = "Create Invoice"

    if invoice_number:
        invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
        title = f"Edit Invoice {invoice.invoice_number}"

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        service_formset = InvoiceServiceFormset(request.POST, instance=invoice)
        attachment_formset = InvoiceAttachmentFormset(request.POST, request.FILES, instance=invoice)

        if form.is_valid() and service_formset.is_valid() and attachment_formset.is_valid():
            # Client Logic
            client, _ = UserClient.objects.get_or_create(email=form.cleaned_data['client_email'])
            client.first_name = form.cleaned_data['client_first_name']
            client.last_name = form.cleaned_data['client_last_name']
            client.phone_number = form.cleaned_data['client_phone']
            client.address = form.cleaned_data['client_address']
            client.save()

            # Invoice Logic
            invoice_obj = form.save(commit=False)
            invoice_obj.client = client
            invoice_obj.save()

            service_formset.instance = invoice_obj
            service_formset.save()
            attachment_formset.instance = invoice_obj
            attachment_formset.save()

            generate_and_process_invoice(request, invoice_obj.invoice_number)
            messages.success(request, "Invoice saved successfully.")
            return redirect('administration:list_invoices')
    else:
        form = InvoiceForm(instance=invoice)
        service_formset = InvoiceServiceFormset(instance=invoice)
        attachment_formset = InvoiceAttachmentFormset(instance=invoice)

    context = {
        'title': title, 'form': form,
        'service_formset': service_formset,
        'attachment_formset': attachment_formset
    }
    return render(request, 'administration/add/invoice_form.html', context)


@staff_member_required(login_url='administration:login')
def generate_and_process_invoice(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    try:
        perform_invoice_generation(invoice, request)
    except Exception as e:
        # HERE is where you handle user feedback for the manual click
        c_print(f"Manual Generation Error: {e}")
        # Optionally add messages.error(request, "Failed...")

    return redirect('administration:list_invoices')


@staff_member_required(login_url='administration:login')
def view_invoice(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    path = invoice.get_path()

    # logic to decide if we regenerate
    force_regen = False
    if not os.path.exists(path):
        force_regen = True
    else:
        # ... check timestamps logic ...
        pass

    if force_regen:
        # We call the PURE function.
        # If this fails, it RAISES an exception, which stops execution here.
        perform_invoice_generation(invoice, request)

    try:
        return FileResponse(open(path, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        # The file is missing. Try ONE LAST TIME safely.
        if not force_regen:
            try:
                perform_invoice_generation(invoice, request)
                return FileResponse(open(path, 'rb'), content_type='application/pdf')
            except Exception as e:
                # Now we have the REAL error in 'e'.
                # We can log it or print it to console
                print(f"CRITICAL INVOICE FAILURE: {e}")
                return HttpResponseServerError(f"Invoice generation failed: {e}")

        return HttpResponseServerError("Invoice generation produced no file.")


@staff_member_required(login_url='administration:login')
def send_invoice_to_client(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    download_url = request.build_absolute_uri(reverse('administration:view_invoice', args=[invoice_number]))

    if not os.path.exists(invoice.get_path()):
        generate_and_process_invoice(request, invoice_number)

    send_client_email(
            email_address=invoice.client.email,
            subject=f"Invoice {invoice.invoice_number}",
            header="Your Invoice is Ready",
            message=f"Hello {invoice.client.first_name}, please find your invoice attached.",
            footer="Thank you.",
            button_label="View Invoice",
            button_text="Download PDF",
            button_link=download_url
    )
    invoice.email_sent = True
    invoice.save(update_fields=['email_sent'])
    messages.success(request, f"Invoice sent to {invoice.client.email}")
    return redirect('administration:list_invoices')


@staff_member_required(login_url='administration:login')
@require_POST
def update_invoice_status(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    new_status = request.POST.get('status')
    if new_status in dict(Invoice.INVOICE_STATUS_CHOICES):
        invoice.status = new_status
        invoice.save()
        messages.success(request, f"Status updated to {new_status}")
    return redirect('administration:list_invoices')


@staff_member_required(login_url='administration:login')
def delete_invoice(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)

    # Archive before delete
    archive_dir = os.path.join(settings.MEDIA_ROOT, "archived_invoices")
    os.makedirs(archive_dir, exist_ok=True)
    zip_path = os.path.join(archive_dir, f"{invoice.get_name()}_{timezone.now().strftime('%Y%m%d%H%M%S')}.zip")

    files_to_zip = [invoice.get_path()] if os.path.exists(invoice.get_path()) else []
    for att in invoice.attachments.all():
        if att.file and os.path.exists(att.file.path):
            files_to_zip.append(att.file.path)

    if files_to_zip:
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for f in files_to_zip:
                zf.write(f, os.path.basename(f))

    invoice.delete()
    messages.success(request, "Invoice archived and deleted.")
    return redirect('administration:list_invoices')


@staff_member_required(login_url='administration:login')
def get_client_emails(request):
    query = request.GET.get('term', '')
    clients = UserClient.objects.filter(email__icontains=query)[:5]
    results = [{'label': c.email, 'value': c.email, 'first_name': c.first_name,
                'last_name': c.last_name, 'phone': c.phone_number, 'address': c.address} for c in clients]
    return JsonResponse(results, safe=False)


# ==============================================================================
# PHOTO DELIVERY - GUEST (Create Downloadable File)
# ==============================================================================

@staff_member_required(login_url='administration:login')
def create_downloadable_file(request):
    if request.method == 'POST':
        files = request.FILES.getlist("images_client_link")
        client_name = request.POST.get("client_name")
        client_email = request.POST.get("client_email")

        delivery = PhotoDelivery.objects.create(client_name=client_name, client_email=client_email)
        photos = [PhotoClient(file=f) for f in files]
        for p in photos: p.save()
        delivery.photos.add(*photos)
        delivery.save()

        if client_email:
            send_client_email(
                    client_email, "Photos Ready", "Download Photos",
                    f"Hello {client_name}, download your photos here.", "Tchiiz Studio",
                    "Download", "Download", delivery.link_to_download
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'link': delivery.link_to_download})
        return redirect('administration:show_all_links_created')

    return render(request, 'administration/add/add_downloadable_file.html', {'title': "Create Download Link"})


@staff_member_required(login_url='administration:login')
def list_downloadable_files_link(request):
    deliveries = PhotoDelivery.objects.all().order_by('-date')
    return render(request, 'administration/list/list_created_link.html', {'deliveries': deliveries})


@staff_member_required(login_url='administration:login')
def delete_delivery(request, pk):
    delivery = get_object_or_404(PhotoDelivery, pk=pk)
    delivery.delete_files()
    messages.success(request, "Delivery deleted.")
    return redirect('administration:show_all_links_created')


# --- Public Views (Imported by Homepage) ---

def get_downloadable_client_images(request, id_delivery):
    """
    PUBLIC VIEW: Used by guests to view their photos via the unique token.
    Imported by homepage/urls.py to serve clean URLs.
    """
    try:
        delivery = PhotoDelivery.objects.get(id_delivery=id_delivery)
    except PhotoDelivery.DoesNotExist:
        return HttpResponseNotFound("Link invalid or expired.")

    # Check expiration
    if delivery.expiration_date and delivery.expiration_date < datetime.date.today():
        return HttpResponse("This link has expired.", status=410)

    context = {
        'client_name': delivery.client_name,
        'photos': delivery.photos.all(),
        'id_delivery': id_delivery,
        'is_guest_view': True
    }
    return render(request, 'administration/download/downloadable_images.html', context)


def download_zip(request, id_delivery):
    """
    PUBLIC VIEW: Download all photos in the delivery as a ZIP.
    Renamed back from 'download_guest_zip' to fix ImportError in homepage/urls.py.
    """
    delivery = get_object_or_404(PhotoDelivery, id_delivery=id_delivery)

    # Mark as downloaded
    if not delivery.was_downloaded:
        delivery.was_downloaded = True
        delivery.save(update_fields=['was_downloaded'])

    # Stream Zip Response
    response = HttpResponse(content_type='application/zip')
    # Sanitize filename
    safe_name = delivery.client_name.replace(' ', '_').replace('/', '') or "photos"
    zip_filename = f"Tchiiz_Photos_{safe_name}.zip"
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'

    with zipfile.ZipFile(response, 'w') as zf:
        for photo in delivery.photos.all():
            if photo.file and os.path.exists(photo.file.path):
                zf.write(photo.file.path, os.path.basename(photo.file.path))

    return response


# ==============================================================================
# PHOTO DELIVERY - ACCOUNT (Send Photo Via Account)
# ==============================================================================

@staff_member_required(login_url='administration:login')
def send_photo_via_account(request):
    """
    Final Delivery: Uploads photos directly to a user's account in a specific album.
    """
    clients = UserClient.objects.filter(is_superuser=False).order_by('first_name')
    if request.method == 'POST':
        client_id = request.POST.get('client')  # Changed to match the select name usually used
        files = request.FILES.getlist('final_photos')

        user = get_object_or_404(UserClient, id=client_id)
        # Create a "Finals" album or add to the existing active one
        album = AlbumClient.objects.create(owner=user, is_active=True)

        photos = [Photo.objects.create(file=f, is_favorite=False, can_be_downloaded=True) for f in files]
        album.photos.add(*photos)

        send_client_email(
                user.email, "Final Photos Ready", "Final Delivery",
                f"Hello {user.first_name}, your final photos are in your dashboard.", "Enjoy",
                "Login", "Login", request.build_absolute_uri(reverse('client:login'))
        )
        messages.success(request, f"Sent {len(photos)} photos to {user.get_full_name()}")
        return redirect('administration:index')

    return render(request, 'administration/add/add_account_delivery.html', {'clients': clients})


# ==============================================================================
# WEBSITE MANAGEMENT (Homepage / Portfolio)
# ==============================================================================

@staff_member_required(login_url='administration:login')
def add_photos_homepage(request):
    albums = AlbumHomepage.objects.all()
    if request.method == "POST":
        images = request.FILES.getlist("images_homepage")
        album_id = request.POST.get('row')
        for image in images:
            PhotoHomepage.objects.create(album_id=album_id, file=image)
        return redirect('administration:list_photos_homepage')

    context = {'albums': albums, 'homepage': True, 'title': "Add to Homepage"}
    return render(request, 'administration/add/add_photos.html', context)


@staff_member_required(login_url='administration:login')
def add_photos_portfolio(request):
    albums = AlbumPortfolio.objects.all()
    if request.method == "POST":
        images = request.FILES.getlist("images_homepage")  # check input name in template
        album_id = request.POST.get('row')
        for image in images:
            PhotoPortfolio.objects.create(album_id=album_id, file=image)
        return redirect('administration:list_photos_portfolio')

    context = {'albums': albums, 'homepage': False, 'title': "Add to Portfolio"}
    return render(request, 'administration/add/add_photos.html', context)


@staff_member_required(login_url='administration:login')
def add_album_portfolio(request):
    form = CreateAlbumForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('administration:list_photos_portfolio')
    return render(request, 'administration/add/add_album.html', {'form': form})


@staff_member_required(login_url='administration:login')
def list_photos_portfolio(request):
    photos = PhotoPortfolio.objects.all()
    return render(request, 'administration/list/list_photos_portfolio.html',
                  {'photos': photos, 'portfolio': True, 'title': "Portfolio Photos"})


@staff_member_required(login_url='administration:login')
def list_photos_homepage(request):
    photos = PhotoHomepage.objects.all()
    return render(request, 'administration/list/list_photos_portfolio.html',
                  {'photos': photos, 'portfolio': False, 'title': "Homepage Photos"})


@staff_member_required(login_url='administration:login')
def delete_photo_portfolio(request, pk):
    photo = get_object_or_404(PhotoPortfolio, pk=pk)
    photo.delete()
    return redirect('administration:list_photos_portfolio')


@staff_member_required(login_url='administration:login')
def delete_photo_homepage(request, pk):
    photo = get_object_or_404(PhotoHomepage, pk=pk)
    photo.delete()
    return redirect('administration:list_photos_homepage')


# ==============================================================================
# CLIENT ALBUM MANAGEMENT (Review Liked Photos)
# ==============================================================================

@staff_member_required(login_url='administration:login')
def send_photos_for_client_to_choose_from(request):
    """Admin uploads Proofs for client."""
    client_list = UserClient.objects.filter(is_superuser=False)
    if request.method == 'POST':
        client_id = request.POST.get("client")
        files = request.FILES.getlist("id_photo")
        user = get_object_or_404(UserClient, id=client_id)

        album, _ = AlbumClient.objects.get_or_create(owner=user, defaults={'is_active': True})
        photos = [Photo.objects.create(file=f) for f in files]
        album.photos.add(*photos)

        url = request.build_absolute_uri(reverse('client:album_details', args=[album.id]))
        send_client_email(user.email, "Select Favorites", "Action Required",
                          "Please select your favorites.", "Tchiiz", "View", "View", url)
        return redirect('administration:index')

    return render(request, 'administration/add/add_client_photos.html', {'client_list': client_list})


@staff_member_required(login_url='administration:login')
def view_client_album_created(request):
    albums = AlbumClient.objects.all()
    return render(request, 'administration/list/list_album_client.html', {'album_list': albums})


@staff_member_required(login_url='administration:login')
def view_all_liked_photos(request, pk):
    album = get_object_or_404(AlbumClient, pk=pk)
    return render(request, 'administration/list/list_album_client_photos.html', {
        'album': album,
        'photos_liked': album.photos.filter(is_favorite=True),
        'photos_not_liked': album.photos.filter(is_favorite=False)
    })


@staff_member_required(login_url='administration:login')
def delete_client_album(request, pk):
    album = get_object_or_404(AlbumClient, pk=pk)
    album.delete_files()  # Model method
    return redirect("administration:view_client_album_created")


# ==============================================================================
# USER MANAGEMENT
# ==============================================================================

@staff_member_required(login_url='administration:login')
def list_requested_user(request):
    clients = UserClient.objects.filter(is_superuser=False)
    return render(request, 'administration/list/list_user.html', {'clients': clients})


@staff_member_required(login_url='administration:login')
def create_new_client(request):
    if request.method == 'POST':
        try:
            client = UserClient.objects.create_user(
                    first_name=request.POST.get("client_name"),
                    email=request.POST.get("client_email"),
                    password="ChangeMe123!"
            )
            client.set_first_login()
            client.send_password_email()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'client': client.id})
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)})
    return render(request, 'administration/add/add_new_client.html')


@staff_member_required(login_url='administration:login')
def update_client(request, pk):
    """Edit existing client details"""
    client = get_object_or_404(UserClient, pk=pk)

    if request.method == 'POST':
        # Extract form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()

        # Validation
        if not first_name:
            messages.error(request, 'First name is required')
            return redirect('administration:update_client', pk=pk)

        if not email:
            messages.error(request, 'Email is required')
            return redirect('administration:update_client', pk=pk)

        # Check for duplicate email (excluding current client)
        if UserClient.objects.filter(email=email).exclude(pk=pk).exists():
            messages.error(request, f'Email {email} is already in use')
            return redirect('administration:update_client', pk=pk)

        # Name validation using your utility
        if check(data=first_name):
            messages.error(request, 'First name contains invalid characters')
            return redirect('administration:update_client', pk=pk)

        if last_name and check(data=last_name):
            messages.error(request, 'Last name contains invalid characters')
            return redirect('administration:update_client', pk=pk)

        # Update client
        client.first_name = first_name
        client.last_name = last_name
        client.email = email
        client.phone_number = phone_number
        client.address = address
        client.save()

        messages.success(request, f'Client {client.get_full_name()} updated successfully')
        return redirect('administration:user_list')

    context = {
        'client': client,
        'title': f'Edit Client: {client.get_full_name()}'
    }
    return render(request, 'administration/add/update_client.html', context)


@staff_member_required(login_url='administration:login')
def view_client_details(request, pk):
    """Comprehensive client details page"""
    client = get_object_or_404(UserClient, pk=pk)

    # Gather all client data
    albums = AlbumClient.objects.filter(owner=client).order_by('-created_at')

    # Get bookings if appointment app exists
    bookings = []
    try:
        from appointment.models import Appointment
        bookings = Appointment.objects.filter(client=client).order_by('-created_at')[:10]
    except ImportError:
        pass

    # Get invoices
    invoices = Invoice.objects.filter(client=client).order_by('-created_at')[:10]

    # Calculate stats
    total_photos = 0
    total_liked = 0
    for album in albums:
        total_photos += album.photos.count()
        total_liked += album.photos.filter(is_favorite=True).count()

    total_invoiced = sum(inv.total_amount() for inv in invoices)
    total_paid = sum(inv.amount_paid for inv in invoices)

    context = {
        'client': client,
        'albums': albums,
        'bookings': bookings,
        'invoices': invoices,
        'total_photos': total_photos,
        'total_liked': total_liked,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'balance_due': total_invoiced - total_paid,
        'title': f'Client Details: {client.get_full_name()}'
    }
    return render(request, 'administration/view/client_details.html', context)


@login_required(login_url="/client/login/")
def must_change_password(request, pk):
    """Force password change logic."""
    form = UserChangePasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = get_object_or_404(UserClient, pk=pk)
        new_pass = form.cleaned_data['new_password1']
        if user.check_password(new_pass):
            messages.warning(request, "Cannot use old password.")
        else:
            user.password = make_password(new_pass)
            user.set_not_first_login()
            user.save()
            return redirect("client:login")

    return render(request, "administration/password/has_to_change_password.html",
                  {'form': form, 'first_login': True})


# ==============================================================================
# MESSAGES
# ==============================================================================

@staff_member_required(login_url='administration:login')
def list_contact_form(request):
    forms = ContactForm.objects.all()
    return render(request, 'administration/list/list_contact_forms.html', {'contact_forms': forms})


@staff_member_required(login_url='administration:login')
def delete_contact_form(request, pk):
    get_object_or_404(ContactForm, pk=pk).delete()
    return redirect('administration:message_list')
