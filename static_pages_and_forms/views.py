from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from crueltouch import settings
from .form import Contact
# Create your views here.


def contact(request):
    if request.method == 'POST':
        form = Contact(request.POST)
        if form.is_valid():
            form.save()
            email_subject = f'New Form from: {form.cleaned_data["full_name"]}'
            email_message = f'Request from: {form.cleaned_data["email"]}\n\n' \
                            f'Subject: {form.cleaned_data["subject"]}\n\n'\
                            f'Message => \n{form.cleaned_data["message"]}'
            # send_mail(subject=email_subject, message=email_message,
            #           from_email=settings.CONTACT_EMAIL, recipient_list=settings.ADMIN_EMAILS)
            return redirect('flatpages:success')
    else:
        form = Contact()
    context = {'form': form}
    return render(request, 'static_pages_and_forms/contact.html', context)


def success(request):
    return render(request, 'static_pages_and_forms/success.html')