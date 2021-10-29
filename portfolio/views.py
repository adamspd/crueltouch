from django.shortcuts import render
from portfolio.models import Photo


def index_portfolio(request):
    all_photos = Photo.objects.all()
    return render(request, 'portfolio/index_portfolio.html', {'all_photos': all_photos})
