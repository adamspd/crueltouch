# tchiiz.com image. The same image runs the web server (default command),
# the django-q worker (manage.py qcluster) and one-off jobs.

# ---- Stage 1: install the Python packages -----------------------------------
FROM python:3.13-slim-trixie AS build

# git: one package is installed straight from its git repository.
# The rest is for building PDF/graphics packages (xhtml2pdf) if no wheel exists.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential pkg-config libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---- Stage 2: the image that runs --------------------------------------------
FROM python:3.13-slim-trixie

# libcairo2: runtime library for the PDF packages.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# DEBUG_VALUE=False here because local work uses a .env file instead.
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=crueltouch.settings \
    DEBUG_VALUE=False

RUN useradd --uid 10001 --user-group --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=build /opt/venv /opt/venv
COPY . .

# django-appointment and django-payment-manager ship no migrations. The first ones
# are kept in appointment_migrations/ and payment_migrations/; this generates
# whatever the installed versions need on top (nothing, if those are up to date).
# The sqlite file it creates as a side effect is removed again.
RUN SECRET_KEY_VALUE=build-only CACHE_DIR=/tmp/cache python manage.py makemigrations appointment payment --noinput \
    && rm -f /app/db.sqlite3

# Gather static files (admin, captcha) into static/ and precompile Python now,
# while the filesystem is still writable. The key is only for this step.
RUN SECRET_KEY_VALUE=build-only python manage.py collectstatic --noinput \
    && python -m compileall -q /app

USER 10001:10001

EXPOSE 8000

# 8 threads: Django also serves the photos (no nginx), and each download holds one.
CMD ["gunicorn", "crueltouch.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", "--worker-class", "gthread", "--threads", "8", \
     "--worker-tmp-dir", "/dev/shm", \
     "--no-control-socket", \
     "--access-logfile", "-", \
     "--forwarded-allow-ips", "*"]
