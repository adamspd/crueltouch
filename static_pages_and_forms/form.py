from django.core.exceptions import ValidationError
from django.forms import ModelForm, forms
from .models import ContactForm


class Contact(ModelForm):
    class Meta:
        model = ContactForm
        fields = '__all__'

