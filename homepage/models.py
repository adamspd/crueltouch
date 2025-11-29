# homepage/models.py
import os

from django.db import models
from django.utils.timezone import now

from utils.crueltouch_utils import change_img_format_to_webp, c_print


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

    def change_file_format(self):
        if os.path.exists(self.file.path):
            img = change_img_format_to_webp(self.file.path, media_sub_folder="Homepage", delete_old_img=True,
                                            lossless=False)
            if img != "":
                self.file = img
                self.save()
                c_print("Image format changed to webp", "success")
        return self.file

    def save(self, *args, **kwargs):
        # if creating a new object
        if not self.id:
            # call the original save method
            super(Photo, self).save(*args, **kwargs)
            # change the file format to webp
            self.change_file_format()
        else:
            # call the original save method
            super(Photo, self).save(*args, **kwargs)


class Logo(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='Logo', null=True, blank=True)

    def __str__(self):
        return self.name
