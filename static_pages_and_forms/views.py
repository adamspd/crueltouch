# static_pages_and_forms/views.py

import requests
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from utils.crueltouch_utils import c_print, check
from .form import Contact
from .models import Quarantine


# from validate_email import validate_email


def get_client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[-1].strip()
    else:
        ip = request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR')
    return ip


def contact(request):
    if request.method == 'POST':
        form = Contact(request.POST)
        if form.is_valid():
            email_ = form.cleaned_data['email']
            message_ = form.cleaned_data['message']
            full_name = form.cleaned_data['full_name']
            subject = form.cleaned_data['subject']
            user_agent = request.META.get('HTTP_USER_AGENT', '')  # Optional
            ip = get_client_ip(request)  # Get the IP address of the sender

            human = True
            # Call the spam detection API
            c_print(f"Captcha valid ? {human}, calling API")
            response = requests.post(
                    "https://spam-detection-api.adamspierredavid.com/v2/check-spam/",
                    json={'text': message_, 'name': full_name, 'email': email_, 'subject': subject,
                          'user_agent': user_agent, 'ip': ip},
                    timeout=10  # Adding timeout to handle potential hanging requests
            )

            # Check if the API request was successful
            if response.status_code == 200:
                # Parse the JSON response
                json_response = response.json()
                is_spam = json_response.get('is_spam')

                # If message is spam or if it contains specific strings, return an error message
                if is_spam or check_email(email_) or check(full_name):
                    messages.success(request, _("Thank you for your message, it will be processed as soon as possible"))
                    Quarantine.objects.create(full_name=full_name, email=email_, message=message_,
                                              reason="Flagged as spam")
                    return redirect("flatpages:contact")
                # If everything is fine, save the form and redirect
                form.save()
                return redirect('flatpages:success')
            else:
                Quarantine.objects.create(full_name=full_name, email=email_, message=message_,
                                          reason="Flagged as spam")
                # If API request failed, log the error (you might want to handle this differently)
                messages.error(request, _("Something went wrong. Please try again later."))
                return redirect("flatpages:contact")
    else:
        form = Contact()

    context = {'form': form}
    return render(request, 'static_pages_and_forms/contact.html', context)


def success(request):
    return render(request, 'static_pages_and_forms/success.html')


def check_email(data):
    # is_valid = validate_email(data)
    is_valid = True
    if data is not None:
        if not is_valid:
            c_print(f"Email is not valid: {is_valid}")
            return True
        if "no-reply" in data \
                or "+" in data \
                or "noreply" in data:
            c_print(f"Email is not valid: {data}")
            return True


def privacy_policy(request):
    page_title = _("Privacy Policy")
    page_description = _("Privacy Policy page")
    context = {'page_title': page_title, 'page_description': page_description}
    return render(request, 'legal/privacy_policy.html', context=context)


def terms_and_conditions(request):
    page_title = _("Terms and Conditions")
    page_description = _("Terms and Conditions page")
    context = {'page_title': page_title, 'page_description': page_description}
    return render(request, 'legal/terms_and_conditions.html', context=context)
