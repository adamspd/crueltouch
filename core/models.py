# core/models.py
from django.db import models
from django.utils.timezone import now

from core.utils.image_processing import convert_to_webp, create_thumbnail


class BaseAlbum(models.Model):
    """
    Abstract base for all Album models.
    Provides common fields and behavior.
    """
    album_title = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=now)

    class Meta:
        abstract = True

    def __str__(self):
        return self.album_title


class BasePhoto(models.Model):
    """
    Abstract base for all Photo models.
    Handles thumbnail generation and WebP conversion automatically.
    """
    file = models.ImageField(upload_to='photos')  # Concrete models override this
    thumbnail = models.ImageField(upload_to='thumbnails', null=True, blank=True)
    date_uploaded = models.DateTimeField(default=now)

    class Meta:
        abstract = True

    def __str__(self):
        album_info = getattr(self, 'album', 'No Album')
        return f"{album_info} ID.{self.id:03d}" if self.id else str(album_info)

    def create_thumbnail_if_needed(self, base_height=300):
        """
        Creates a thumbnail if it doesn't exist.
        Called automatically on save.
        """
        if self.file and not self.thumbnail:
            thumbnail_path = create_thumbnail(
                    image_path=self.file.path,
                    base_height=base_height
            )
            if thumbnail_path:
                self.thumbnail = thumbnail_path
                self.save(update_fields=['thumbnail'])

    def convert_to_webp_if_needed(self, media_subfolder):
        """
        Converts image to WebP format if not already.
        Called automatically on save for homepage/portfolio photos.
        """
        if self.file:
            webp_path = convert_to_webp(
                    image_path=self.file.path,
                    media_subfolder=media_subfolder,
                    delete_original=True
            )
            if webp_path:
                self.file = webp_path
                self.save(update_fields=['file'])

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)

        # Only process images on creation
        if is_new and self.file:
            # Subclasses can override this behavior
            self._post_save_image_processing()

    def _post_save_image_processing(self):
        """
        Override this in subclasses to customize image processing.
        Default: do nothing (client photos don't auto-convert to webp)
        """
        pass
