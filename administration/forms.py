import random
from datetime import datetime

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


class InvoiceForm(forms.Form):
    client_name = forms.CharField()
    client_email = forms.EmailField()
    client_phone = forms.CharField()
    package_name = forms.CharField()
    package_price = forms.DecimalField()
    package_qty = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_name'].widget.attrs.update(
            {
                'class': 'form-control',
                'onkeyup': 'return forceTitle(this);',
                'placeholder': _('Full name')
            })
        self.fields['client_email'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': _('Email address'),
                'onkeyup': 'return forceLower(this);',
            })
        self.fields['client_phone'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': _('Phone number'),
            })
        self.fields['package_name'].widget.attrs.update(
            {
                'class': 'form-control',
                'placeholder': _('Service name'),
            })
        self.fields['package_qty'].widget.attrs.update(
            {
                'class': 'form-control',
            })
        self.fields['package_price'].widget.attrs.update(
            {
                'class': 'form-control',
            })

    def clean(self):
        cleaned_data = super().clean()
        # date format MMM DD, YYYY
        cleaned_data['invoice_date'] = datetime.today().strftime('%b %d, %Y')
        i_n = random.randint(0, 999999)
        # always 6 digits
        invoice_number = str(f"{i_n:06d}")
        cleaned_data['invoice_number'] = invoice_number
        cleaned_data['package_price'] = float(cleaned_data['package_price'])
        cleaned_data['package_subtotal'] = cleaned_data['package_price'] * cleaned_data['package_qty']
        cleaned_data['total'] = cleaned_data['package_price'] * cleaned_data['package_qty']
        return cleaned_data
