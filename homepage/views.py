# homepage/views.py
import random

from appointment.models import Service
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views import generic

from crueltouch import settings
from .models import Photo


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
    page_title = _("Services | TCHIIZ")
    page_description = _("Services offered by Tchiiz studio Photography")
    all_services = Service.objects.all()
    wedding_services = all_services.filter(name__icontains='wedding')
    portrait_services = all_services.filter(name__icontains='portrait')
    # rest of category that isn't wedding and portrait
    product_services = all_services.filter(name__icontains='product')
    event_services = all_services.filter(name__icontains='event')
    context = {
        'page_title': page_title,
        'page_description': page_description,
        'wedding_service': wedding_services,
        'portrait_service': portrait_services,
        'product_service': product_services,
        'event_service': event_services,
    }
    return render(request, 'homepage/services_offered.html', context=context)
