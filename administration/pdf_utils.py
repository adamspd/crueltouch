# administration/pdf_utils.py
import datetime
import os
import tempfile

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.template.loader import get_template
from pypdf.constants import UserAccessPermissions
from xhtml2pdf import pisa


# Helper to find images for the PDF engine
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those files.
    """
    # 1. HANDLE ABSOLUTE PATHS (The Fix)
    # If the generate_invoice_pdf logic already gave us a full path, use it.
    if os.path.isabs(uri) and os.path.isfile(uri):
        return uri

    # 2. Handle Media Files (Dynamic uploads)
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))

    # 3. Handle Static Files (CSS, Logos)
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))

    # 4. Fallback: Search Static Finders (Only for relative paths)
    else:
        try:
            # finders.find() crashes on absolute paths, so we only try if relative
            result = finders.find(uri)
            if result:
                return result
        except (SuspiciousFileOperation, ValueError):
            # We explicitly ignore these because we have a fallback below.
            # SuspiciousFileOperation = Absolute path passed to finder
            # ValueError = Malformed path
            pass
        path = uri

    # 5. Final Validity Check
    if not os.path.isfile(path):
        # Return None prevents xhtml2pdf from crashing, it just won't render the image
        return None

    return path


def generate_invoice_pdf(request, invoice):
    """
    Generates the PDF in a temporary location with full data mapping.
    """
    template_path = 'administration/add/invoice.html'

    # --- 1. RESOLVE PATHS (With Null Checks) ---

    # Header/Footer: Hardcoded paths usually work, but verify they exist in your project
    header_path = os.path.join(settings.MEDIA_ROOT, 'Logo', 'header_tchiiz.webp')
    footer_path = os.path.join(settings.MEDIA_ROOT, 'Logo', 'footer_tchiiz.webp')

    # Handle Stamps: CHECK FOR NONE FIRST
    stamp_url = invoice.get_stamp_link()
    stamp_path = ""

    if stamp_url:  # <--- The Fix: Verify existence before touching it
        if stamp_url.startswith(settings.MEDIA_URL):
            stamp_path = os.path.join(settings.MEDIA_ROOT, stamp_url.replace(settings.MEDIA_URL, ""))
        else:
            stamp_path = stamp_url

            # Math Logic
    if invoice.discount > 0:
        discount_percent = round(invoice.discount, 1)
        discount_value = round(invoice.get_discount(invoice.get_base_amount()), 1)
    else:
        discount_percent = None
        discount_value = None

    if invoice.tax_rate > 0:
        tax_percent = round(invoice.tax_rate, 1)
        tax_value = round(invoice.get_tax(invoice.get_net_amount()), 1)
    else:
        tax_percent = None
        tax_value = None

    # Handle N/A Phone
    client_phone = invoice.client.phone_number
    if not client_phone:
        client_phone = "N/A"

    # --- 2. THE CONTEXT MAPPING ---
    context = {
        'invoice_number': invoice.invoice_number,
        'url': request.build_absolute_uri(invoice.get_absolute_url()),
        'invoice_date': invoice.created_at,
        'due_date': invoice.due_date,
        'details': invoice.details,
        'payment_method': invoice.payment_method if invoice.payment_method != "_" else "none",

        'client_name': invoice.client.get_full_name(),
        'client_email': invoice.client.email,
        'client_phone': client_phone,

        'services': invoice.invoice_services.all(),

        'total': invoice.get_base_amount(),
        'amount_paid': invoice.amount_paid,
        'balance_due': invoice.balance_due(),
        'discount_percent': discount_percent,
        'discount_value': discount_value,
        'tax_percent': tax_percent,
        'tax_value': tax_value,

        # Images
        'header': header_path,
        'footer': footer_path,
        'stamps': stamp_path,  # Now safely passes an empty string if None
    }

    # --- 3. RENDERING & SAVING ---
    template = get_template(template_path)
    html = template.render(context)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pisa_status = pisa.CreatePDF(
                html,
                dest=tmp_file,
                link_callback=link_callback
        )
        raw_path = tmp_file.name

    if pisa_status.err:
        os.remove(raw_path)
        raise Exception(f"PDF Generation Error: {pisa_status.err}")

    return raw_path


def secure_pdf(input_pdf_path, output_pdf_path, owner_password, invoice):
    """
    Locks the PDF so clients can't edit it.
    """
    from pypdf import PdfWriter, PdfReader

    with open(input_pdf_path, "rb") as input_stream:
        reader = PdfReader(input_stream)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # Metadata
        metadata = {
            '/Author': 'Tchiiz Studio',
            '/Title': f'Invoice {invoice.invoice_number}',
            '/Creator': 'Tchiiz System',
            '/CreationDate': f"D:{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        }
        writer.add_metadata(metadata)

        # Encrypt: if the user pwd empty (can open), Owner pwd set (cannot edit)
        writer.encrypt(
                user_password='',
                owner_password=owner_password,
                algorithm="AES-256",
                permissions_flag=UserAccessPermissions.PRINT
        )

        with open(output_pdf_path, "wb") as output_stream:
            writer.write(output_stream)


def perform_invoice_generation(invoice, request):
    """
    Pure logic: Generates the PDF and secures it.
    Raises exceptions if it fails so the caller knows.
    Returns: final_path (str)
    """
    # 1. Generate Raw PDF
    # We pass 'request' because the context needs 'protocol' and 'domain'
    raw_path = generate_invoice_pdf(request, invoice)

    # 2. Determine Final Path
    final_path = invoice.get_path()

    # 3. Secure/Move
    # If raw_path and final_path are the same, secure_pdf needs to handle
    # temp files, or we risk truncating the file we are reading.
    try:
        secure_pdf(raw_path, final_path, settings.SECRET_KEY, invoice)
    except Exception as e:
        # If security fails, we must know!
        raise RuntimeError(f"Securing PDF failed: {e}")

    # 4. Cleanup
    if raw_path != final_path and os.path.exists(raw_path):
        os.remove(raw_path)

    # 5. Final Verification (Trust but Verify)
    if not os.path.exists(final_path):
        raise FileNotFoundError(f"Generation finished but {final_path} is missing.")

    return final_path
