# homepage/models.py
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
