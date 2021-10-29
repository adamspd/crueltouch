from django.db import models
from django.utils.timezone import now


# Create your models here.


class Album(models.Model):
    album_title = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=now)

    def __str__(self):
        return self.album_title


def get_path(instance, filename):
    return '{0}/{1}'.format(instance.file.album_title, filename)


class Logo(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='Logo', null=True, blank=True)

    def __str__(self):
        return self.name
