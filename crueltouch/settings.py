"""
Django settings for Tchiiz' project.
Refactored for strict environment variable handling.
"""
import os
import sys
from pathlib import Path

from django.conf import global_settings, locale
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

# --- PATH CONFIGURATION ---
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)


# --- UTILITY: Strict Boolean Parsing ---
def get_env_bool(var_name, default=False):
    """
    Parses a string environment variable to a boolean.
    'True', 'true', '1', 'yes' -> True
    Anything else -> False
    """
    value = os.getenv(var_name, str(default))
    return value.lower() in ('true', '1', 't', 'y', 'yes')


# --- CORE SETTINGS ---

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to FALSE if not found.
DEBUG = get_env_bool('DEBUG_VALUE', False)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY_VALUE')
if not SECRET_KEY:
    # Fail fast if no key is present. Don't fallback to weak defaults.
    raise ValueError("FATAL: SECRET_KEY_VALUE is missing from .env")

allowed_hosts_env = os.getenv('LIST_OF_ALLOWED_HOSTS', default="")
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]
else:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Admin & Email Config
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', default="")
ADMIN_NAME = os.getenv('ADMIN_NAME', default="Admin")
OTHER_ADMIN_EMAIL = os.getenv('OTHER_ADMIN_EMAIL', default="")

# Email Server
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_LOCALTIME = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', "")
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', "")
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_SUBJECT_PREFIX = ""

ADMINS = [('Main Admin', ADMIN_EMAIL)]
if not DEBUG and OTHER_ADMIN_EMAIL:
    ADMINS.append(('Support', OTHER_ADMIN_EMAIL))

MANAGERS = ADMINS

# Payment Config
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', "")
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', "")
PAYPAL_ENVIRONMENT = os.getenv('PAYPAL_ENVIRONMENT', "sandbox")

# --- APPS & MIDDLEWARE ---

AUTH_USER_MODEL = 'client.UserClient'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    # Third Party
    'captcha',
    'django_q',
    # Local Apps
    'core',
    'homepage',
    'client',
    'portfolio',
    'static_pages_and_forms',
    'administration',
    'appointment',
    'payment',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'homepage.middleware.CacheControlMiddleware'
]

ROOT_URLCONF = 'crueltouch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'crueltouch.wsgi.application'

# --- DATABASE ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- AUTH ---

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'client/login/'
LOGIN_REDIRECT_URL = 'client/'
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

# --- STATIC & MEDIA ---

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]
    STATIC_ROOT = BASE_DIR / 'staticfiles_collected'
else:
    STATIC_ROOT = BASE_DIR / 'static'

# --- INTERNATIONALIZATION ---

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True
USE_L10N = True

# Custom Language Support
EXTRA_LANG_INFO = {
    'cr-ht': {
        'bidi': False,
        'code': 'cr-ht',
        'name': 'Haitian Creole',
        'name_local': "Kreyòl",
    },
}
LANG_INFO = dict(locale.LANG_INFO, **EXTRA_LANG_INFO)
locale.LANG_INFO = LANG_INFO

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
)
LANGUAGES_BIDI = global_settings.LANGUAGES_BIDI + ["cr-ht"]
LOCALE_PATHS = [str(BASE_DIR / 'locale')]

# --- LOGGING & CACHE ---

# Use relative paths so this works on dev AND prod without changing code
LOGS_DIR = BASE_DIR / 'logs' / 'django'
if not LOGS_DIR.exists():
    # Make sure log dir exists to prevent startup crash
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
    except OSError:
        pass  # Handle permission errors gracefully if needed

CACHES_LOCATION = BASE_DIR / '.cache'

if not DEBUG:
    # Production Logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        "handlers": {
            "file": {
                "level": "INFO",  # Changed from DEBUG to reduce noise in prod
                "class": "logging.FileHandler",
                "filename": str(LOGS_DIR / "django.log"),
            },
        },
        'loggers': {
            "django": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": True,
            },
        },
    }
else:
    # Dev Logging (Console)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(CACHES_LOCATION),
    }
}

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
USER_ONLINE_TIMEOUT = 300
USER_LAST_SEEN_TIMEOUT = 60 * 60 * 24 * 7

# --- SECURITY (PRODUCTION) ---

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_AGE = 3600

# --- APP CONFIGURATION ---

# Appointment
APPOINTMENT_SLOT_DURATION = 30
APPOINTMENT_LEAD_TIME = (9, 0)
APPOINTMENT_FINISH_TIME = (16, 30)
APPOINTMENT_CLIENT_MODEL = AUTH_USER_MODEL
APPOINTMENT_BASE_TEMPLATE = 'homepage/base.html'
APPOINTMENT_ADMIN_BASE_TEMPLATE = 'administration/base.html'
APPOINTMENT_WEBSITE_NAME = 'CruelTouch'
APPOINTMENT_THANK_YOU_URL = None

# Payment
PAYMENT_PAYPAL_ENVIRONMENT = PAYPAL_ENVIRONMENT
PAYMENT_PAYPAL_CLIENT_ID = PAYPAL_CLIENT_ID
PAYMENT_PAYPAL_CLIENT_SECRET = PAYPAL_CLIENT_SECRET
PAYMENT_BASE_TEMPLATE = 'homepage/base.html'
PAYMENT_WEBSITE_NAME = 'CruelTouch'
PAYMENT_MODEL = 'appointment.PaymentInfo'
PAYMENT_REDIRECT_SUCCESS_URL = 'homepage:index'
PAYMENT_APPLY_PAYPAL_FEES = True
PAYMENT_FEES = 0.03 if not PAYMENT_APPLY_PAYPAL_FEES else 0.00

# Secrets
SECRETS_DIR = BASE_DIR / 'crueltouch' / 'secrets'
PDF_CERTIFICATE_PATH = str(SECRETS_DIR / 'pdf_certificate.pfx')
CERTIFICATE_PATH = str(SECRETS_DIR / 'pdf_certificate.crt')
PRIVATE_KEY_PATH = str(SECRETS_DIR / 'pdfkey.key')

# Django Q
Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}
