from django.forms import ModelForm
from .models import ContactForm


class Contact(ModelForm):
    class Meta:
        model = ContactForm
        fields = ['full_name', 'email', 'subject', 'message']
