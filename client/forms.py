# client/forms.py
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from client.models import UserClient
from portfolio.models import Album as AlbumForm


class RegistrationForm(UserCreationForm):
    class Meta:
        model = UserClient
        fields = ['first_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update(
                {
                    'class': 'form-control',
                    'onkeyup': 'return forceTitle(this);',
                    'placeholder': _('First name')
                })
        self.fields['email'].widget.attrs.update(
                {
                    'class': 'form-control',
                    'placeholder': _('Email address'),
                    'onkeyup': 'return forceLower(this);',
                })
        self.fields['password1'].widget.attrs.update(
                {
                    'class': 'form-control',
                    'placeholder': _('Password'),
                })
        self.fields['password2'].widget.attrs.update(
                {
                    'class': 'form-control',
                    'placeholder': _('Confirm password'),
                })


class CreateAlbumForm(ModelForm):
    class Meta:
        model = AlbumForm
        fields = ['album_title']
