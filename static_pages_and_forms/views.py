from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _

from utils.crueltouch_utils import check, c_print
from .form import Contact
# from validate_email import validate_email


# Create your views here.


def contact(request):
    if request.method == 'POST':
        form = Contact(request.POST)
        if form.is_valid():
            if check_email(form.cleaned_data['email']) or check(form.cleaned_data['message']) or check_full_name(
                    form.cleaned_data['full_name']):
                messages.error(request, _("Thank you for your message, but it didn't went through !"))
                return redirect("flatpages:contact")
            else:
                form.save()
                return redirect('flatpages:success')
    else:
        form = Contact()
    context = {'form': form}
    return render(request, 'static_pages_and_forms/contact.html', context)


def success(request):
    return render(request, 'static_pages_and_forms/success.html')


def check_email(data):
    # is_valid = validate_email(data)
    if data is not None:
        if not is_valid:
            c_print(f"Email is not valid: {is_valid}")
            return True
        if "no-reply" in data \
                or "+" in data \
                or "noreply" in data:
            c_print(f"Email is not valid: {data}")
            return True


def check_full_name(data):
    if data is not None:
        if "HenryGak" in data \
                or "Eric Jones" in data \
                or "BusinessLoans" in data:
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
