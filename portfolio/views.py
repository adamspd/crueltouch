import random

from django.shortcuts import render
from portfolio.models import Photo


def index_portfolio(request):
    all_photos = Photo.objects.all()
    list_of_photo = list(all_photos)
    random.shuffle(list_of_photo)
    return render(request, 'portfolio/index_portfolio.html', {'all_photos': list_of_photo})


def detailed_view(request, pk):
    photo = Photo.objects.get(id=pk)
    return render(request, 'homepage/detailed.html', {'photo': photo})
