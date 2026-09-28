"""Django settings for the Tchiiz project."""
import os
from django.conf import global_settings, locale
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')


def get_env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ('true', '1', 't', 'y', 'yes')


# --- Core ---

DEBUG = get_env_bool('DEBUG_VALUE', False)

SECRET_KEY = os.getenv('SECRET_KEY_VALUE')
if not SECRET_KEY:
    raise ValueError("FATAL: SECRET_KEY_VALUE is missing from .env")

allowed_hosts = os.getenv('LIST_OF_ALLOWED_HOSTS', "")
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(',')] if allowed_hosts else ["127.0.0.1", "localhost"]

ROOT_URLCONF = 'crueltouch.urls'
WSGI_APPLICATION = 'crueltouch.wsgi.application'
SITE_ID = 1
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Apps ---

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
    # Third party
    'captcha',
    'django_q',
    # Local
    'core',
    'homepage',
    'client',
    'portfolio',
    'static_pages_and_forms',
    'administration',
    # Third party, after local apps so local templates take priority
    'appointment',
    'payment',
]

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
    'homepage.middleware.CacheControlMiddleware',
]

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

# --- Database & cache ---

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(BASE_DIR / '.cache'),
    }
}

# --- Auth & sessions ---

AUTH_USER_MODEL = 'client.UserClient'
LOGIN_URL = 'client/login/'
LOGIN_REDIRECT_URL = 'client/'
PASSWORD_RESET_TIMEOUT = 60 * 60

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
USER_ONLINE_TIMEOUT = 5 * 60
USER_LAST_SEEN_TIMEOUT = 60 * 60 * 24 * 7

# --- Security (production) ---

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_AGE = 60 * 60

# --- Email ---

email_user = os.getenv('EMAIL_HOST_USER', "")

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'username': email_user,
            'password': os.getenv('EMAIL_HOST_PASSWORD', ""),
        },
    },
}
SERVER_EMAIL = email_user
EMAIL_SUBJECT_PREFIX = ""
EMAIL_USE_LOCALTIME = True

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', "")
OTHER_ADMIN_EMAIL = os.getenv('OTHER_ADMIN_EMAIL', "")
ADMINS = [ADMIN_EMAIL]
if not DEBUG and OTHER_ADMIN_EMAIL:
    ADMINS.append(OTHER_ADMIN_EMAIL)
MANAGERS = ADMINS

# --- Static & media ---

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'static']
    STATIC_ROOT = BASE_DIR / 'staticfiles_collected'
else:
    STATIC_ROOT = BASE_DIR / 'static'

# --- Internationalization ---

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
    ('fr', _('French')),
)
LOCALE_PATHS = [str(BASE_DIR / 'locale')]

# Haitian Creole
locale.LANG_INFO = {
    **locale.LANG_INFO,
    'cr-ht': {'bidi': False, 'code': 'cr-ht', 'name': 'Haitian Creole', 'name_local': "Kreyòl"},
}
LANGUAGES_BIDI = global_settings.LANGUAGES_BIDI + ["cr-ht"]

# --- Logging ---

logs_dir = BASE_DIR / 'logs' / 'django'
try:
    logs_dir.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {'class': 'logging.StreamHandler'},
        },
        'root': {'handlers': ['console'], 'level': 'INFO'},
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': str(logs_dir / 'django.log'),
            },
        },
        'loggers': {
            'django': {'handlers': ['file'], 'level': 'INFO', 'propagate': True},
        },
    }

# --- Django Q ---

Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 4,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}

# --- Appointment ---

APPOINTMENT_SLOT_DURATION = 30
APPOINTMENT_LEAD_TIME = (9, 0)
APPOINTMENT_FINISH_TIME = (16, 30)
APPOINTMENT_CLIENT_MODEL = AUTH_USER_MODEL
APPOINTMENT_BASE_TEMPLATE = 'homepage/base.html'
APPOINTMENT_ADMIN_BASE_TEMPLATE = 'administration/base.html'
APPOINTMENT_WEBSITE_NAME = 'CruelTouch'
APPOINTMENT_THANK_YOU_URL = None

# --- Payment ---

PAYMENT_PAYPAL_ENVIRONMENT = os.getenv('PAYPAL_ENVIRONMENT', "sandbox")
PAYMENT_PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', "")
PAYMENT_PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', "")
PAYMENT_BASE_TEMPLATE = 'homepage/base.html'
PAYMENT_WEBSITE_NAME = 'CruelTouch'
PAYMENT_MODEL = 'appointment.PaymentInfo'
PAYMENT_REDIRECT_SUCCESS_URL = 'homepage:index'
PAYMENT_APPLY_PAYPAL_FEES = True
PAYMENT_FEES = 0.00 if PAYMENT_APPLY_PAYPAL_FEES else 0.03

# --- PDF signing ---

secrets_dir = BASE_DIR / 'crueltouch' / 'secrets'
PDF_CERTIFICATE_PATH = str(secrets_dir / 'pdf_certificate.pfx')
CERTIFICATE_PATH = str(secrets_dir / 'pdf_certificate.crt')
PRIVATE_KEY_PATH = str(secrets_dir / 'pdfkey.key')
