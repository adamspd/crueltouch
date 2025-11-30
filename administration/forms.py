from django import forms
from django.forms import inlineformset_factory
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from administration.models import Invoice, InvoiceAttachment, InvoiceService


class UserChangePasswordForm(forms.Form):
    """
    Form for forcing a user to change their password on first login
    or via admin intervention.
    """
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': _('Password'),
        'class': 'form-control',
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': _('Repeat password'),
        'class': 'form-control',
    }))


class InvoiceServiceForm(forms.ModelForm):
    class Meta:
        model = InvoiceService
        fields = ('service_name', 'service_price', 'service_quantity')
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service Name'}),
            'service_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'service_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1'}),
        }


# Formset for line items (Services)
InvoiceServiceFormset = inlineformset_factory(
        Invoice, InvoiceService,
        form=InvoiceServiceForm,
        extra=1,
        can_delete=True
)


class InvoiceAttachmentForm(forms.ModelForm):
    class Meta:
        model = InvoiceAttachment
        fields = ('file',)
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


# Formset for file attachments
InvoiceAttachmentFormset = inlineformset_factory(
        Invoice, InvoiceAttachment,
        form=InvoiceAttachmentForm,
        extra=1,
        can_delete=True
)


class InvoiceForm(forms.ModelForm):
    """
    Main Invoice Form.
    Includes fields for creating/updating the related Client on the fly.
    """
    # --- Client Fields (Not on Invoice model, but used to update UserClient) ---
    client_email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        # dynamic URL resolution instead of hardcoded string
        'data-ajax-url': reverse_lazy('administration:get_client_emails'),
        'autocomplete': 'off',
        'id': 'id_client_email',
        'placeholder': _('Client Email')
    }))
    client_first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'onkeyup': 'return forceTitle(this);',  # Relies on custom JS in template
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
            'payment_method', 'discount', 'tax_rate', 'amount_paid',
            'due_date', 'details', 'notes', 'status'
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

        # Ensure status choices align with Model
        self.fields['status'].choices = Invoice.INVOICE_STATUS_CHOICES

        # Pre-populate client fields if editing an existing invoice
        if instance and instance.client:
            self.initial['client_email'] = instance.client.email
            self.initial['client_first_name'] = instance.client.first_name
            self.initial['client_last_name'] = instance.client.last_name
            self.initial['client_phone'] = instance.client.phone_number
            self.initial['client_address'] = instance.client.address

        # Explicitly order fields for the template rendering
        new_order = [
            'client_email', 'client_first_name', 'client_last_name',
            'client_phone', 'client_address', 'payment_method',
            'discount', 'tax_rate', 'amount_paid', 'due_date',
            'details', 'notes', 'status'
        ]
        self.fields = {k: self.fields[k] for k in new_order}
