# middleware.py
from django.conf import settings
from django.utils.cache import add_never_cache_headers, patch_cache_control


class CacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.DEBUG:
            add_never_cache_headers(response)
        else:
            if 'image' in response['Content-Type']:
                patch_cache_control(response, public=True, max_age=604800, must_revalidate=True)
        return response
