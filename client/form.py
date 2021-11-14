from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

from client.models import UserClient, BookMe


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
