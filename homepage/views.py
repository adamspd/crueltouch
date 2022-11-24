import random

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render

from django.views import generic

from crueltouch import settings
from .models import Photo


# Create your views here.


def index(request):
    album1 = Photo.objects.filter(album_id=1)
    album2 = Photo.objects.filter(album_id=2)
    list_of_album1 = list(album1)
    list_of_album2 = list(album2)
    random.shuffle(list_of_album1)
    random.shuffle(list_of_album2)
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


def get_favicon(request):
    try:
        with open(settings.BASE_DIR / 'static/homepage/img/icon/favicon.ico', 'rb') as f:
            return HttpResponse(f.read(), content_type="image/x-icon")
    except IOError:
        raise Http404


@login_required(login_url='/administration/login/')
def promotions(request):
    return render(request, 'client/booking_and_promotions/promotions.html')