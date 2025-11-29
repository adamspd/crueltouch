# static_pages_and_forms/form.py
from captcha.fields import CaptchaField
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import ContactForm


class Contact(ModelForm):
    captcha = CaptchaField()

    class Meta:
        model = ContactForm
        fields = ['full_name', 'email', 'subject', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control',
                'onkeyup': 'return forceTitle(this);',
                'placeholder': _("How do I call you ?")
            })
        self.fields['email'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control',
                'onkeyup': 'return forceLower(this);',
                'placeholder': _("A valid email address, please... !")
            })
        self.fields['subject'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control',
                'placeholder': _("What is the subject of your message... ?")
            })
        self.fields['message'].widget.attrs.update(
            {
                'type': 'text',
                'class': 'form-control',
                'placeholder': _("I'm listening... !")
            })
