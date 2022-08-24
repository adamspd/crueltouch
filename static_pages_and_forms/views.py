from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from crueltouch import settings
from utils.crueltouch_utils import c_print
from .form import Contact


# Create your views here.


def contact(request):
    if request.method == 'POST':
        form = Contact(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            c_print(full_name, email, subject, message)
            if check_email(email) or check_message(message) or check_subject(subject) or check_full_name(full_name):
                messages.error(request, "Messages from bot are not accepted !")
                return redirect("flatpages:contact")
            else:
                form.save()
                email_subject = f'New Form from: {form.cleaned_data["full_name"]}'
                email_message = f'Request from: {form.cleaned_data["email"]}\n\n' \
                                f'Subject: {form.cleaned_data["subject"]}\n\n' \
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


def check_message(data):
    if data is not None:
        if "http" in data \
                or "https" in data \
                or "www." in data \
                or "%" in data \
                or "Contact us" in data \
                or "contact" in data \
                or "business" in data \
                or "robot" in data \
                or "Robot" in data \
                or " Earn" in data \
                or " earn" in data \
                or "#1" in data \
                or "# 1" in data \
                or "Financial" in data \
                or "financial" in data \
                or "us" in data \
                or "Make money" in data \
                or "Making money" in data \
                or "Invest $1" in data \
                or "Passive income" in data \
                or "NFT" in data \
                or "bot" in data \
                or "Bot" in data:
            return True


def check_subject(data):
    if data is not None:
        if "Business" in data \
                or "business" in data \
                or "robot" in data \
                or "Robot" in data \
                or " Earn" in data \
                or " earn" in data \
                or "#1" in data \
                or "# 1" in data \
                or "Financial" in data \
                or "financial" in data:
            return True


def check_email(data):
    if data is not None:
        if "no-reply" in data \
                or "noreply" in data:
            return True


def check_full_name(data):
    if data is not None:
        if "HenryGak" in data \
                or "Eric Jones" in data \
                or "BusinessLoans" in data:
            return True
