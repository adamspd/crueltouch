from django import forms
from django.utils.translation import gettext_lazy as _


class UserChangePasswordForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update(
            {
                'placeholder': _('Password'),
                'type': 'password',
                'class': 'form-control',
            })
        self.fields['new_password2'].widget.attrs.update(
            {
                'placeholder': _('Repeat password'),
                'type': 'password',
                'class': 'form-control',
            })
