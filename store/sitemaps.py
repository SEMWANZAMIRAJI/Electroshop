from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return [
            'product_list',  # homepage or product list
            'cart',
            'checkout',
            'success',
            'product_create',
        ]

    def location(self, item):
        return reverse(item)
