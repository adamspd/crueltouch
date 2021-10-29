from django.db import models
from django.utils.timezone import now
from homepage.models import Album


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='Portfolio', null=True, blank=True)
    date_uploaded = models.DateTimeField(default=now)

    def __str__(self):
        return str(self.album) + "ID.{:0>3}".format(self.id)

    def album_name(self):
        return str(self.album.album_title)
