from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from administration.models import Invoice, InvoiceAttachment, InvoiceService


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


PAYMENT_METHOD = (
    ('_', _('--- Select a payment method ---')),
    ('cash', _('Cash')),
    ('credit', _('Credit')),
    ('debit', _('Debit')),
    ('paypal', _('Paypal')),
    ('cashapp', _('CashApp')),
    ('venmo', _('Venmo')),
    ('zelle', _('Zelle')),
    ('check', _('Check')),
    ('others', _('Others')),
    ('none', _('None')),
)


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
    class Meta:
        model = Invoice
        fields = [
            'client_name', 'client_email', 'client_phone', 'payment_method', 'client_address',
            'discount', 'tax_rate', 'amount_paid', 'due_date', 'details', 'notes', 'status'
        ]
        widgets = {
            'client_name': forms.TextInput(
                attrs={'class': 'form-control', 'onkeyup': 'return forceTitle(this);', 'placeholder': _('Full name')}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email address'),
                                                    'onkeyup': 'return forceLower(this);'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Phone number')}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'client_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize additional fields if needed
        self.fields['status'].choices = Invoice.INVOICE_STATUS_CHOICES
