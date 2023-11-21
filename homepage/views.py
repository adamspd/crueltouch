import json
import random

from appointment.models import Service
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views import generic

from crueltouch import settings
from utils.crueltouch_utils import email_check
from .models import Photo


# Create your views here.


def index(request):
    try:
        album1 = Photo.objects.filter(album_id=1)
        album2 = Photo.objects.filter(album_id=2)
    except Photo.DoesNotExist:
        album1 = []
        album2 = []

    if album1 != [] or album2 != []:
        change_file_format(album1)
        change_file_format(album2)
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


def change_file_format(list_of_photo: list[Photo]):
    for photo in list_of_photo:
        photo.change_file_format()


class AboutView(generic.ListView):
    template_name = 'homepage/index_about_me.html'

    def get_queryset(self):
        return Photo.objects.all()


def get_logo(request):
    try:
        with open(settings.BASE_DIR / 'static/homepage/img/logos/logo.png', 'rb') as f:
            return HttpResponse(f.read(), content_type="image/png")
    except IOError:
        raise Http404


def get_logo_mini(request):
    try:
        with open(settings.BASE_DIR / 'static/homepage/img/logos/logo-mini.png', 'rb') as f:
            return HttpResponse(f.read(), content_type="image/png")
    except IOError:
        raise Http404


def promotions(request):
    return render(request, 'client/booking_and_promotions/promotions.html')


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
