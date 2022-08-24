from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from client.models import UserClient, BookMe
from portfolio.models import Album as AlbumForm


class CustomRegisterForm(UserCreationForm):
    class Meta:
        model = UserClient
        fields = ['first_name', 'email', 'password1', 'password2']


class BookME(ModelForm):
    class Meta:
        model = BookMe
        fields = ['full_name', 'email', 'session_type', 'place', 'package']


class UpdateBook(ModelForm):
    class Meta:
        model = BookMe
        fields = ['full_name', 'email', 'session_type', 'place', 'package', 'status']


class CreateAlbumForm(ModelForm):
    class Meta:
        model = AlbumForm
        fields = ['album_title']
