# portfolio/models.py
from django.db import models
from core.models import BaseAlbum, BasePhoto


class Album(BaseAlbum):
    """
    Portfolio albums - unlimited, for gallery display.
    """
    pass


class Photo(BasePhoto):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='Portfolio', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='Portfolio/thumbnails', null=True, blank=True)

    def _post_save_image_processing(self):
        """Convert to WebP and create a thumbnail on upload"""
        self.convert_to_webp_if_needed(media_subfolder='Portfolio')
        self.create_thumbnail_if_needed(base_height=500)
