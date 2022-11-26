import os

from django.db import models
from django.utils.timezone import now

from utils.crueltouch_utils import c_print, change_img_format_to_webp


class Album(models.Model):
    album_title = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=now)

    def __str__(self):
        return self.album_title


def get_path(instance, filename):
    return '{0}/{1}'.format(instance.file.album_title, filename)


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='Portfolio', null=True, blank=True)
    date_uploaded = models.DateTimeField(default=now)

    def __str__(self):
        return str(self.album) + "ID.{:0>3}".format(self.id)

    def change_file_format(self):
        if os.path.exists(self.file.path):
            img = change_img_format_to_webp(self.file.path, media_sub_folder="Portfolio", delete_old_img=True,
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

    # delete all file formatted as webp in the media/Portfolio folder
    @staticmethod
    def delete_all_webp():
        for file in os.listdir("media/Portfolio"):
            if file.endswith(".webp"):
                os.remove(os.path.join("media/Portfolio", file))
        return True
