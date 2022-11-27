from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from client.models import UserClient, BookMe
from portfolio.models import Album as AlbumForm

PACKAGE = (
    ('_', _('--- Select a package ---')),
    ('7', _('7 photos')),
    ('15', _('15 photos')),
    ('30', _('30 photos + mini video')),
    ('3', _('3 photos')),
)
SESSION_TYPE = (
    ('_', _('--- Select a session type ---')),
    ('portrait', _('Portrait')),
    ('birthday', _('Birthday')),
    ('wOthers', _('Wedding and other events')),
)
WHERE = (
    ('_', _('--- Select a location ---')),
    ('studio', _('Studio')),
    ('outdoor', _('Outdoor')),
    ('orlando', _('Orlando')),
    ('others', _('Others')),
)


class CustomRegisterForm(UserCreationForm):
    class Meta:
        model = UserClient
        fields = ['first_name', 'email', 'password1', 'password2']


class BookME(forms.Form):
    full_name = forms.CharField(max_length=100, required=True, label=_("Full Name"))
    email = forms.EmailField(label=_("Email"))
    phone_number = forms.CharField(max_length=10)
    session_type = forms.ChoiceField(choices=SESSION_TYPE, label=_("Type of photo session"))
    place = forms.ChoiceField(choices=WHERE, label=_("Location"))
    package = forms.ChoiceField(choices=PACKAGE, label=_("Package"))
    desired_date = forms.DateField(label=_("Desired Date"))
    address = forms.CharField(max_length=100, label=_("Address"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs.update(
            {
                'class': 'form-control',
                'onkeyup': 'return forceTitle(this);',
                'placeholder': _('Full name') + '...'
            })
        self.fields['email'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': _("A valid email address, please... !"),
                'onkeyup': 'return forceLower(this);'
            })
        self.fields['phone_number'].widget.attrs.update(
            {
                'class': 'form-control',
                'type': 'tel',
                'placeholder': _('No spaces, letters or special characters, only 10 digits...'),
                'onkeyup': 'return forceNumber(this);'
            })
        self.fields['session_type'].widget.attrs.update(
            {
                'class': 'form-control',
            })
        self.fields['place'].widget.attrs.update(
            {
                'class': 'form-control',
            })
        # add choices to package
        self.fields['package'].widget.attrs.update(
            {
                'class': 'form-control',
            })
        self.fields['desired_date'].widget.attrs.update(
            {
                'class': 'form-control',
            })
        self.fields['address'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': _('Does not have to be specific, just the city and the state') + '...',
            })

    def clean_package(self):
        super(BookME, self).clean()
        package = self.cleaned_data['package']
        place = self.cleaned_data['place']
        session = self.cleaned_data['session_type']
        if place == "_" or package == "_" or session == "_":
            raise forms.ValidationError(_("Fill in all the fields"))
        if package == '3' and place != 'orlando':
            raise forms.ValidationError(_("Sorry, we only offer this package in Orlando"))
        return package


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
