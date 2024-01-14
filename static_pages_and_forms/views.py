import requests
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _

from utils.crueltouch_utils import check, c_print
from .form import Contact


# from validate_email import validate_email


def contact(request):
    if request.method == 'POST':
        form = Contact(request.POST)
        if form.is_valid():
            email_ = form.cleaned_data['email']
            message_ = form.cleaned_data['message']
            full_name = form.cleaned_data['full_name']
            subject = form.cleaned_data['subject']

            # Concatenate subject and message
            message_with_subject = f'subject: {subject}. {message_}'
            human = True
            # Call the spam detection API
            c_print(f"Captcha valid ? {human}, calling API")
            response = requests.post(
                "https://spam-detection-api.adamspierredavid.com/v1/check-spam/",
                json={'message': message_with_subject}  # Use json parameter instead of data
            )

            # Check if the API request was successful
            if response.status_code == 200:
                # Parse the JSON response
                json_response = response.json()
                is_spam = json_response.get('is_spam')

                # If message is spam or if it contains specific strings, return an error message
                if is_spam or check_email(email_) or check(full_name):
                    messages.error(request, _("Thank you for your message, but it didn't went through!"))
                    return redirect("flatpages:contact")
                # If everything is fine, save the form and redirect
                form.save()
                return redirect('flatpages:success')
            else:
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
    c_print("this was called")
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
