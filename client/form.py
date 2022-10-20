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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs['readonly'] = True
        self.fields['full_name'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control',
                'onkeyup': 'return forceTitle(this);',
                'value': self.instance.full_name,
            })
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['email'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control',
                'onkeyup': 'return forceLower(this);',
                'value': self.instance.email,
            })
        self.fields['session_type'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control custom-select',
            })
        self.fields['place'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control custom-select',
            })
        self.fields['package'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control custom-select',
            })
        self.fields['status'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control custom-select',
            })


class CreateAlbumForm(ModelForm):
    class Meta:
        model = AlbumForm
        fields = ['album_title']
