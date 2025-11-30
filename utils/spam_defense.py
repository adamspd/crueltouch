# utils/spam_defense.py
import requests
from requests.exceptions import RequestException
from validate_email import validate_email
from utils.crueltouch_utils import c_print, check

SPAM_API_URL = "https://spam-detection-api.adamspierredavid.com/v2/check-spam/"


def is_suspicious_pattern(email, name):
    """
    Fast, local heuristic checks.
    Returns (bool, str): (is_suspicious, reason)
    """
    # 1. Utility check (invalid chars/names)
    if check(name):
        return True, f"Suspicious name detected locally: {name}"

    # 2. Email patterns (e.g., 'no-reply' or generic bot names)
    if email:
        if "no-reply" in email or "noreply" in email:
            return True, f"Suspicious email pattern: {email}"

    return False, ""


def analyze_submission(email, full_name, message, subject, user_agent, ip_address):
    """
    Slow, deep inspection (DNS & External API).
    Intended for background workers.
    Returns (bool, str): (is_spam, reason)
    """
    c_print(f"Analyzing submission for {email} via Background Worker...")

    # 1. DNS Check
    # Safe to enable check_dns=True here because we are in a background task.
    # If it hangs for 5 seconds, the user doesn't care.
    is_valid_dns = validate_email(
            email_address=email,
            check_format=True,
            check_blacklist=True,
            check_dns=True,  # ENABLED
            check_smtp=False  # STILL DISABLED (Too risky)
    )

    if not is_valid_dns:
        return True, "Email DNS/Format validation failed"

    # 2. Remote API Check
    try:
        payload = {
            'text': message,
            'name': full_name,
            'email': email,
            'subject': subject,
            'user_agent': user_agent,
            'ip': ip_address
        }

        response = requests.post(SPAM_API_URL, json=payload, timeout=10)

        if response.status_code == 200:
            json_response = response.json()
            if json_response.get('is_spam', False):
                return True, "Flagged as spam by API"
        else:
            # API Error -> We treat API failures as 'suspicious' or just log it.
            # Returning True here means "Quarantine it just in case".
            c_print(f"Spam API Error: {response.status_code}")
            return True, f"API returned status {response.status_code}"

    except RequestException as e:
        c_print(f"Spam API Connection Failure: {e}")
        return True, f"API Connection Failed: {str(e)}"

    return False, "Clean"
