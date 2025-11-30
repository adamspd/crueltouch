# homepage/models.py
from appointment.models import Service
from django.db import models

from core.models import BaseAlbum, BasePhoto


class Album(BaseAlbum):
    """
    Homepage albums - limited to exactly 2 (first row, second row).
    """
    pass


class Photo(BasePhoto):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='Homepage', null=True, blank=True)

    # No thumbnail field - homepage doesn't use thumbnails

    def _post_save_image_processing(self):
        """Convert to WebP on upload"""
        self.convert_to_webp_if_needed(media_subfolder='Homepage')


class Logo(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='Logo', null=True, blank=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_order = models.IntegerField(default=0)

    # Special pricing zones
    is_economy_zone = models.BooleanField(
            default=False,
            help_text="Naples and Fort Myers get $150 package"
    )

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name


class ServiceCityAvailability(models.Model):
    """
    Junction table: which services are available in which cities
    """
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='city_availability')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='available_services')

    # Override the base price for this city if needed
    custom_price = models.DecimalField(
            max_digits=10,
            decimal_places=2,
            null=True,
            blank=True,
            help_text="Leave empty to use service's default price"
    )

    class Meta:
        unique_together = ['service', 'city']
        verbose_name_plural = "Service City Availabilities"

    def get_price(self):
        return self.custom_price if self.custom_price else self.service.price
