from django.db import models
from django.utils.timezone import now


class Album(models.Model):
    album_title = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=now)

    def __str__(self):
        return self.album_title


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='Homepage', null=True, blank=True)
    date_uploaded = models.DateTimeField(default=now)

    def __str__(self):
        return str(self.album) + "ID.{:0>3}".format(self.id)


class Logo(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='Logo', null=True, blank=True)

    def __str__(self):
        return self.name
