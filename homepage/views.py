# homepage/views.py
import random

from appointment.models import Service
from django.conf import settings
from django.db.models import DecimalField
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views import generic

from crueltouch import settings
from .models import City, Photo


def index(request):
    try:
        album1 = Photo.objects.filter(album_id=1)
        album2 = Photo.objects.filter(album_id=2)
    except Photo.DoesNotExist:
        album1 = []
        album2 = []

    if album1 != [] or album2 != []:
        list_of_album1 = list(album1)
        list_of_album2 = list(album2)
        random.shuffle(list_of_album1)
        random.shuffle(list_of_album2)
    else:
        list_of_album1 = []
        list_of_album2 = []

    context = {
        'album1': list_of_album1,
        'album2': list_of_album2
    }
    return render(request, 'homepage/index.html', context)


class AboutView(generic.ListView):
    template_name = 'homepage/index_about_me.html'

    def get_queryset(self):
        return Photo.objects.all()


def get_logo(request):
    try:
        with open(settings.BASE_DIR / 'static/homepage/img/logos/logo.webp', 'rb') as f:
            return HttpResponse(f.read(), content_type="image/webp")
    except IOError:
        raise Http404("Image not found")


def get_logo_mini(request):
    try:
        with open(settings.BASE_DIR / 'static/homepage/img/logos/logo-mini.webp', 'rb') as f:
            return HttpResponse(f.read(), content_type="image/webp")
    except IOError:
        raise Http404("Image not found")


def promotions(request):
    return render(request, 'client/booking_and_promotions/promotions.html')


def get_robot_txt(request):
    try:
        with open(settings.BASE_DIR / 'static/homepage/robots.txt', 'rb') as f:
            return HttpResponse(f.read(), content_type="text/plain")
    except IOError:
        raise Http404("File not found")


def services_offered(request):
    # 1. Capture the City
    selected_city_id = request.GET.get('city') or request.session.get('selected_city')
    selected_city = None

    # Get cities with specific display order (Naples first, Others last)
    cities = City.objects.all().order_by('display_order', 'name')

    # Base Query: Get everything initially
    services = Service.objects.all()

    if selected_city_id:
        try:
            selected_city = City.objects.get(id=selected_city_id)
            request.session['selected_city'] = selected_city_id

            # 2. FILTER & SORT:
            # - Only show services available in this city.
            # - Sort by price (Low to High) so the 3-picture package appears first.
            services = services.filter(
                    city_availability__city=selected_city
            ).order_by('price')

            # 3. ANNOTATE: The "Magic" C-style optimization.
            # We overwrite the 'price' attribute in memory with the custom price if it exists.
            services = services.annotate(
                    displayed_price=Coalesce(
                            'city_availability__custom_price',  # Try this first
                            'price',  # Fallback to this
                            output_field=DecimalField()
                    )
            )
        except City.DoesNotExist:
            # If city ID is invalid, show nothing
            services = Service.objects.none()
    else:
        # User hasn't picked a city yet. Show nothing to force selection.
        services = Service.objects.none()

    # Categorize (Using the 'services' queryset which is now filtered and sorted)
    context = {
        'page_title': "Services | TCHIIZ",
        'page_description': "Services offered by Tchiiz studio Photography",
        'cities': cities,
        'selected_city': selected_city,
        'wedding_service': services.filter(name__icontains='wedding'),
        'portrait_service': services.filter(name__icontains='portrait'),
        'product_service': services.filter(name__icontains='product'),
        'event_service': services.filter(name__icontains='event'),
    }
    return render(request, 'homepage/services_offered.html', context)
