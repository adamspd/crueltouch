# administration/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from administration.models import InvoiceAttachment, InvoiceService
from .models import Invoice


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


class InvoiceServiceForm(forms.ModelForm):
    class Meta:
        model = InvoiceService
        fields = ('service_name', 'service_price', 'service_quantity')

    def __init__(self, *args, **kwargs):
        super(InvoiceServiceForm, self).__init__(*args, **kwargs)
        self.fields['service_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['service_price'].widget.attrs.update({'class': 'form-control'})
        self.fields['service_quantity'].widget.attrs.update({'class': 'form-control'})


InvoiceServiceFormset = inlineformset_factory(
    Invoice, InvoiceService,
    form=InvoiceServiceForm,
    extra=1, can_delete=True
)


class InvoiceAttachmentForm(forms.ModelForm):
    class Meta:
        model = InvoiceAttachment
        fields = ('file',)

    def __init__(self, *args, **kwargs):
        super(InvoiceAttachmentForm, self).__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'class': 'form-control'})


InvoiceAttachmentFormset = inlineformset_factory(
    Invoice, InvoiceAttachment,
    form=InvoiceAttachmentForm,
    extra=1, can_delete=True
)


class InvoiceForm(forms.ModelForm):
    client_email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'data-ajax-url': '/administration/get-client-emails/',
        'autocomplete': 'off',
        'id': 'id_client_email'
    }))
    client_first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'onkeyup': 'return forceTitle(this);',
        'placeholder': _('First name')
    }))
    client_last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'onkeyup': 'return forceTitle(this);',
        'placeholder': _('Last name')
    }))
    client_phone = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': _('Phone number')
    }))
    client_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 1,
            'placeholder': _('Address'),
        }))

    class Meta:
        model = Invoice
        fields = [
            'payment_method', 'discount', 'tax_rate', 'amount_paid', 'due_date', 'details', 'notes', 'status'
        ]
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = Invoice.INVOICE_STATUS_CHOICES

        # Pre-populate client fields if editing an existing invoice
        if instance and instance.client:
            self.initial['client_email'] = instance.client.email
            self.initial['client_first_name'] = instance.client.first_name
            self.initial['client_last_name'] = instance.client.last_name
            self.initial['client_phone'] = instance.client.phone_number
            self.initial['client_address'] = instance.client.address

        # Rearranging field order
        new_order = ['client_email', 'client_first_name', 'client_last_name', 'client_phone', 'client_address',
                     'payment_method', 'discount', 'tax_rate', 'amount_paid', 'due_date', 'details', 'notes', 'status']
        new_fields = {k: self.fields[k] for k in new_order}
        self.fields = new_fields
