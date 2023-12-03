import os
from io import BytesIO

from PIL import Image, ImageOps
from django.contrib.auth.base_user import AbstractBaseUser, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, PermissionsMixin, User, User
from django.core.files.base import ContentFile
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
    thumbnail = models.ImageField(upload_to='Portfolio/thumbnails', null=True, blank=True)
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

    def create_thumbnail(self, base_height=500):
        if not os.path.exists(self.thumbnail.path):
            img = Image.open(self.file)
            # Get image's name without a path and extension
            name = os.path.basename(self.file.name)
            name, _ = os.path.splitext(name)
            thumbnail_name = f'{name}_thumbnail.webp'

            # Handle image orientation based on EXIF data
            img = ImageOps.exif_transpose(img)

            # Resize image
            height_percent = (base_height / float(img.size[1]))
            width_size = int((float(img.size[0]) * float(height_percent)))
            img = img.resize((width_size, base_height), Image.Resampling.LANCZOS)

            # Convert RGBA image to RGB
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Save thumbnail in memory
            thumbnail_io = BytesIO()
            img.save(thumbnail_io, format='WEBP', quality=100, optimize=True)
            thumbnail_file = ContentFile(thumbnail_io.getvalue())

            # Save thumbnail to the ImageField
            self.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
            self.save()

    def save(self, *args, **kwargs):
        # if creating a new object
        if not self.id:
            # call the original save method
            super(Photo, self).save(*args, **kwargs)
            # change the file format to webp
            self.change_file_format()
            self.create_thumbnail()
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

    @staticmethod
    def delete_all_thumbnails():
        for file in os.listdir("media/Portfolio/thumbnails"):
            if file.endswith(".webp"):
                os.remove(os.path.join("media/Portfolio/thumbnails", file))
        return True
