# static_pages_and_forms/tasks.py
from utils.crueltouch_utils import c_print
from utils.spam_defense import analyze_submission
from .models import ContactForm as Contact, Quarantine


def process_quarantined_contact(quarantine_id):
    """
    Django Q task: Checks a Quarantine record against DNS and Spam API.
    """
    try:
        submission = Quarantine.objects.get(id=quarantine_id)
    except Quarantine.DoesNotExist:
        c_print(f"Task Failed: Quarantine ID {quarantine_id} not found.")
        return

    # If it was already processed (race condition?), skip
    if submission.is_processed:
        return

    # 1. Run Analysis
    is_spam, reason = analyze_submission(
            email=submission.email,
            full_name=submission.full_name,
            message=submission.message,
            subject=submission.subject,
            user_agent=submission.user_agent,
            ip_address=submission.ip_address
    )

    # 2. Act on Verdict
    if is_spam:
        # Verdict: GUILTY.
        # Keep in Quarantine, mark why.
        submission.reason = reason
        submission.is_processed = True
        submission.save()
        c_print(f"Submission {submission.id} flagged as SPAM: {reason}")
    else:
        # Verdict: INNOCENT.
        # Promote to real Contact model.
        Contact.objects.create(
                full_name=submission.full_name,
                email=submission.email,
                subject=submission.subject,
                message=submission.message
        )

        # Cleanup: Remove from Quarantine since it's now a valid contact.
        # (Or keep it and mark 'Approved' if you want a full audit log)
        submission.delete()
        c_print(f"Submission for {submission.full_name} APPROVED. Moved to Contact.")
