# client/views.py
import json

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from utils.crueltouch_utils import check
from .forms import RegistrationForm
from .models import Album, Photo

User = get_user_model()


# --- Auth Views ---

def register_page(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('client:client_homepage')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        email = request.POST.get('email', '')

        # 1. Email Validation (Kept your library check)
        try:
            from validate_email import validate_email
            is_valid = validate_email(
                    email_address=email,
                    check_format=True,
                    check_blacklist=True,
                    check_dns=False,
                    check_smtp=False
            )
            if not is_valid:
                messages.error(request, 'Invalid email address')
                return redirect('client:register')
        except ImportError:
            pass  # Graceful fallback if lib missing

        # 2. Name Validation (Kept your custom utility)
        if check(data=request.POST.get('first_name', '')):
            messages.error(request, 'First name contains invalid characters')
            return redirect('client:register')

        if form.is_valid():
            user = form.save()
            # Fixed string representation bug from original code
            name = form.cleaned_data.get('first_name')
            messages.success(request, f'Account was created for {name}')
            return redirect('client:login')
    else:
        form = RegistrationForm()

    return render(request, 'client/login_registration/register.html', {'form': form})


def login_page(request: HttpRequest):
    # Already authenticated?
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email and password are required')
            return render(request, 'client/login_registration/login.html')

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.info(request, 'Username or Password is incorrect')
            return render(request, 'client/login_registration/login.html')

        login(request, user)
        return _redirect_after_login(user)

    return render(request, 'client/login_registration/login.html')


def logout_user(request):
    """
    Logout and redirect based on role.
    """
    if not request.user.is_authenticated:
        return redirect('client:login')

    # Capture role before logging out
    is_admin = request.user.is_superuser or request.user.is_staff
    logout(request)

    return redirect('administration:login' if is_admin else 'client:login')


def _redirect_after_login(user):
    """Helper to route users based on role/status"""
    if user.has_to_change_password:
        return redirect("administration:must_change_password", user.pk)

    if user.is_staff or user.is_superuser:
        return redirect('administration:index')

    return redirect('client:client_homepage')


# --- Dashboard & Features ---

@login_required(login_url='/client/login')
def index(request: HttpRequest):
    """Client Dashboard"""
    user = request.user

    # Fetch album
    try:
        album = Album.objects.get(owner=user)
        total_photos = album.photos.count()
        favorite_photos = album.photos.filter(is_favorite=True).count()
    except Album.DoesNotExist:
        album = None
        total_photos = 0
        favorite_photos = 0

    # Fetch bookings (Soft dependency preserved)
    bookings = []
    try:
        from appointment.models import Appointment
        bookings = Appointment.objects.filter(client=user).order_by('-created_at')[:5]
    except ImportError:
        pass

    return render(request, 'client/client_view/index.html', {
        'album': album,
        'user': user,
        'total_photos': total_photos,
        'favorite_photos': favorite_photos,
        'bookings': bookings,
    })


@login_required(login_url='/client/login')
def user_album_details(request: HttpRequest, pk: int):
    # Used get() instead of get_object_or_404 to match your exact error handling style
    try:
        selected_album = Album.objects.get(id=pk, owner=request.user)
        selected_album.set_viewed()  # Using your model method
    except Album.DoesNotExist:
        messages.error(request, 'Album not found or access denied')
        return redirect('client:client_homepage')

    return render(request, 'client/client_view/photo_details.html', {
        'album': selected_album
    })


@login_required(login_url='/client/login')
@require_POST
def toggle_favorite(request: HttpRequest):
    """
    Cleaned up AJAX handler.
    """
    # 1. Handle JSON (Modern) or Form Data (Legacy)
    photo_id = None
    if request.headers.get('Content-Type') == 'application/json':
        try:
            data = json.loads(request.body)
            photo_id = data.get('photo_id')
        except:
            pass
    else:
        photo_id = request.POST.get('photo_id')

    if not photo_id:
        return JsonResponse({'error': 'Missing photo_id'}, status=400)

    # 2. Logic
    try:
        photo = Photo.objects.get(id=photo_id)

        # Verify ownership via Album
        if not Album.objects.filter(owner=request.user, photos=photo).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)

        if photo.is_favorite:
            photo.set_not_favorite()
            action = 'disliked'
        else:
            photo.set_favorite()
            action = 'liked'

        return JsonResponse({'status': 'ok', 'action': action})

    except Photo.DoesNotExist:
        return JsonResponse({'error': 'Photo not found'}, status=404)


# --- Profile Management (Restored) ---

@login_required(login_url='/client/login')
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()

        if not first_name:
            messages.error(request, 'First name is required')
            return redirect('client:edit_profile')

        # Using your 'check' utility
        if check(data=first_name):
            messages.error(request, 'First name contains invalid characters')
            return redirect('client:edit_profile')

        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        user.address = address
        user.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('client:client_homepage')

    return render(request, 'client/client_view/edit_profile.html', {
        'user': user
    })


@login_required(login_url='/client/login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # 1. Verify Current
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('client:change_password')

        # 2. Verify Match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('client:change_password')

        # 3. Verify Length (Your specific rule)
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('client:change_password')

        # 4. Save
        request.user.password = make_password(new_password)
        request.user.save()

        messages.success(request, 'Password changed successfully. Please login again.')
        logout(request)
        return redirect('client:login')

    return render(request, 'client/client_view/change_password.html')


# --- Payment Placeholders (Restored) ---

def paynow(request):
    return render(request, 'client/booking_and_promotions/payment.html')


def success_payment(request):
    return render(request, 'client/success.html')
