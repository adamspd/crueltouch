import random

from django.shortcuts import render

from django.views import generic
from .models import Photo


# Create your views here.


def index(request):
    album1 = Photo.objects.filter(album_id=1)
    album2 = Photo.objects.filter(album_id=2)
    list_of_album1 = list(album1)
    list_of_album2 = list(album2)
    random.shuffle(list_of_album1)
    random.shuffle(list_of_album2)
    # random.shuffle(album1, random=None)
    # random.shuffle(album2, random=None)
    context = {
        'album1': list_of_album1,
        'album2': list_of_album2
    }
    return render(request, 'homepage/index.html', context)


def detailed_view(request, pk):
    photo = Photo.objects.get(id=pk)
    return render(request, 'homepage/detailed.html', {'photo': photo})


class AboutView(generic.ListView):
    template_name = 'homepage/index_about_me.html'

    def get_queryset(self):
        return Photo.objects.all()
