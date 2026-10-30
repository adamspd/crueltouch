"""
Health checks for Kubernetes probes.

  /healthz  — the process is up. Liveness probe. Never touches the database,
              so a database outage doesn't get the web container restarted.
  /readyz   — the process can reach the database. Readiness probe. While it
              fails, Kubernetes stops sending visitors to this pod.

Must be the first middleware: the kubelet calls the pod by its IP over plain
HTTP, which ALLOWED_HOSTS and SECURE_SSL_REDIRECT would otherwise turn away.
"""
from django.db import connection
from django.http import HttpResponse


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/healthz':
            return HttpResponse('ok', content_type='text/plain')
        if request.path == '/readyz':
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 1')
            except Exception:
                return HttpResponse('database unavailable', status=503, content_type='text/plain')
            return HttpResponse('ok', content_type='text/plain')
        return self.get_response(request)
