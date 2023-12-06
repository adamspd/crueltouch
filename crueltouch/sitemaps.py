# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class ImportantStaticViewSitemap(Sitemap):
    priority = 1
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return [
            'homepage:index',
            'homepage:about',
            'flatpages:contact',
            'pf:index_portfolio',
            'homepage:services_offered',
            'homepage:promotions',
        ]

    def location(self, item):
        return reverse(item)


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'yearly'
    protocol = 'https'

    def items(self):
        return [
            'client:login',
            'client:register',
            'homepage:privacy_policy',
            'homepage:terms_and_conditions',
        ]

    def location(self, item):
        return reverse(item)
