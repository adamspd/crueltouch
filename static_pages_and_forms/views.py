# static_pages_and_forms/views.py
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django_q.tasks import async_task

from utils.spam_defense import is_suspicious_pattern
from .form import Contact
from .models import Quarantine


def get_client_ip(request):
    """
    Extracts IP, preferring the X-Forwarded-For header (first entry).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (Client IP)
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR')


def contact(request):
    if request.method == 'POST':
        form = Contact(request.POST)
        if form.is_valid():
            # 1. Extract Raw Data
            data = form.cleaned_data
            ip = get_client_ip(request)
            ua = request.META.get('HTTP_USER_AGENT', '')

            # 2. Initial Local Check (Fast Fail)
            suspicious, reason = is_suspicious_pattern(data['email'], data['full_name'])

            # 3. Create Quarantine Record (The "Inbox")
            # We save EVERYTHING here first.
            submission = Quarantine.objects.create(
                    full_name=data['full_name'],
                    email=data['email'],
                    subject=data['subject'],
                    message=data['message'],
                    ip_address=ip,
                    user_agent=ua,
                    reason=reason if suspicious else "Pending Analysis",
                    is_processed=False
            )

            # 4. Queue Processing
            if suspicious:
                # If local checks failed, we mark it processed immediately so the worker doesn't waste time.
                submission.is_processed = True
                submission.save()
            else:
                # Local checks passed -> Queue the Heavy Logic
                async_task('static_pages_and_forms.tasks.process_quarantined_contact', submission.id)

            # 5. User Feedback (Shadow Ban strategy: Always say success)
            messages.success(request, _("Thank you for your message, it will be processed as soon as possible"))
            return redirect('flatpages:success')
    else:
        form = Contact()

    return render(request, 'static_pages_and_forms/contact.html', {'form': form})


# ... keep your success/privacy/terms views as they were ...
def success(request):
    return render(request, 'static_pages_and_forms/success.html')


def privacy_policy(request):
    context = {'page_title': _("Privacy Policy"), 'page_description': _("Privacy Policy page")}
    return render(request, 'legal/privacy_policy.html', context=context)


def terms_and_conditions(request):
    context = {'page_title': _("Terms and Conditions"), 'page_description': _("Terms and Conditions page")}
    return render(request, 'legal/terms_and_conditions.html', context=context)
