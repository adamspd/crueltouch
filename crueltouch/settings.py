"""
Django settings for crueltouch project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

from django.conf import global_settings
# Add custom languages not provided by Django
from django.conf import locale
from django.utils.translation import gettext_lazy as _

from crueltouch.productions import production_debug, production_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = production_secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = production_debug

ALLOWED_HOSTS = ["*"] if DEBUG else ['144.217.7.48', 'crueltouch.com', 'www.crueltouch.com']

AUTH_USER_MODEL = 'client.UserClient'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'homepage',
    'client',
    'static_pages_and_forms',
    'portfolio'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = 'static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = 'media/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Message storage
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Number of seconds of inactivity before a user is marked offline
USER_ONLINE_TIMEOUT = 300

# Number of seconds that we will keep track of inactive users for before
# their last seen is removed from the cache
USER_LAST_SEEN_TIMEOUT = 60 * 60 * 24 * 7

# Caches settings
CACHES_LOCATION = os.path.join(BASE_DIR, '.cache') if DEBUG else "/home/debian/.cache/crueltouch"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': CACHES_LOCATION,
    }
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'adamspd.webmaster@gmail.com'
EMAIL_HOST_PASSWORD = 'jjeimwqqoszjqasf'
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = ""
EMAIL_USE_LOCALTIME = True

ADMINS = [
    ('Adams', 'adamspd.developer@gmail.com'),
]
if not DEBUG:
    ADMINS.append(('Roos', 'roos.laurore5@gmail.com '))

MANAGERS = [
    ('Adams', 'adamspd.developer@gmail.com'),
]

if not DEBUG:
    MANAGERS.append(('Roos', 'crueltouchphoto@gmail.com '))

ADMIN_EMAIL = 'adamspd.developer@gmail.com'

# Language translation settings

EXTRA_LANG_INFO = {
    'cr-ht': {
        'bidi': False,  # right-to-left
        'code': 'cr-ht',
        'name': 'Haitian Creole',
        'name_local': "Kreyòl",
    },
}

LANG_INFO = dict(locale.LANG_INFO, **EXTRA_LANG_INFO)
locale.LANG_INFO = LANG_INFO

LANGUAGES = (
    ('en', _('English')),
    # ('fr', _('Français')),
    # ('cr-ht', _('Kreyòl')),
)

# Languages using BiDi (right-to-left) layout
LANGUAGES_BIDI = global_settings.LANGUAGES_BIDI + ["cr-ht"]

LOCALE_PATHS = (
    os.path.join(BASE_DIR / 'locale'),
)

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

USE_L10N = True

# Extra deployment parameters
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 60
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_AGE = 900  # 15 minutes

LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = LOGIN_URL

# The number of seconds a password reset link is valid for (in second)
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour
