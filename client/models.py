# client/models.py
import os
from io import BytesIO

import PIL
from PIL import Image
from PIL.ExifTags import TAGS
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin, User
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from utils.crueltouch_utils import c_print, send_password_reset_email

phone_regex = RegexValidator(
        regex=r'^\d{15}$',
        message=_("Phone number must not contain spaces, letters, parentheses or dashes. It must contain 15 digits.")
)


class Photo(models.Model):
    file = models.ImageField(upload_to='Client', null=True, blank=True)
    is_favorite = models.BooleanField(default=False)
    can_be_downloaded = models.BooleanField(default=False)
    thumbnail = models.FileField(upload_to='Client/thumbnails', null=True, blank=True)

    def __str__(self):
        return self.file.name

    def set_favorite(self):
        self.is_favorite = True
        self.save()

    def set_not_favorite(self):
        self.is_favorite = False
        self.save()

    def set_can_be_downloaded(self):
        self.can_be_downloaded = True
        self.save()

    def set_can_not_be_downloaded(self):
        self.can_be_downloaded = False
        self.save()

    def create_thumbnail(self, base_height=300):
        if not self.thumbnail:
            img = Image.open(self.file)
            # get image's name without path and extension
            name = os.path.basename(self.file.name)
            name, extension = os.path.splitext(name)[0], os.path.splitext(name)[1]
            name = name + '_thumbnail' + extension
            # extract orientation information from image's metadata
            try:
                for orientation in TAGS.keys():
                    if TAGS[orientation] == 'Orientation':
                        break
                exif = dict(img._getexif().items())
                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(-90, expand=True)
                elif exif[orientation] == 8:
                    img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                # no EXIF information found
                pass
            # resize image
            height_percent = (base_height / float(img.size[1]))
            width_size = int((float(img.size[0]) * float(height_percent)))
            img = img.resize((width_size, base_height), PIL.Image.Resampling.LANCZOS)
            # convert RGBA image to RGB
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            # save thumbnail in self.thumbnail_url field
            thumbnail_io = BytesIO()
            img.save(thumbnail_io, format='JPEG')
            thumbnail_file = ContentFile(thumbnail_io.getvalue())
            self.thumbnail.save(name, thumbnail_file, save=False)
            self.save()

    def get_thumbnail_url(self):
        if self.file:
            if self.thumbnail:
                return self.thumbnail.url
            else:
                self.create_thumbnail()
                return self.thumbnail.url if self.thumbnail else ''
        else:
            return ''

    def get_name(self):
        name = os.path.basename(self.file.name)
        return name

    def get_is_favorite(self):
        if self.is_favorite:
            return "like is-active"
        else:
            return ""

    def delete(self, *args, **kwargs):
        # Delete the files from the file system.
        if self.file:
            default_storage.delete(self.file.name)
        if self.thumbnail:
            default_storage.delete(self.thumbnail.name)

        # Call the superclass delete() method.
        super(Photo, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.create_thumbnail()

    def get_url(self):
        return self.file.url if self.file else ''


class UserManager(BaseUserManager):

    def create_user(self, first_name, email, last_name=None, password=None, is_admin=False, is_staff=False,
                    is_active=True):
        if not email:
            raise ValueError(_('You must provide an email address'))
        if not first_name:
            raise ValueError(_("User must have a firstname"))
        user_obj = self.model(
                email=self.normalize_email(email)
        )
        user_obj.last_name = last_name
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.is_active = is_active
        user_obj.first_name = first_name
        user_obj.set_password(password)
        user_obj.save(using=self._db)
        return user_obj

    def create_staff_user(self, first_name, email, password, last_name=None):
        user = self.create_user(first_name, email, last_name=last_name, password=password, is_staff=True)
        return user

    def create_superuser(self, first_name, email, password, last_name=None):
        user = self.create_user(first_name, email, last_name=last_name, password=password, is_staff=True, is_admin=True)
        return user


class UserClient(AbstractBaseUser, PermissionsMixin, models.Model):
    email = models.EmailField(max_length=255, unique=True, default="", help_text=_("A valid email address, please"))
    first_name = models.CharField(max_length=255, default=None)
    last_name = models.CharField(max_length=255, default=None, null=True, blank=True)
    phone_number = models.CharField(max_length=18, blank=True, null=True, default="",
                                    help_text=_("Phone number must not contain spaces, letters, parentheses or "
                                                "dashes. It must contain 15 digits."))
    address = models.CharField(max_length=255, blank=True, null=True, default="",
                               help_text=_("Does not have to be specific, just the city and the state"))

    is_active = models.BooleanField(default=True)  # can login
    admin = models.BooleanField(default=False)  # superuser
    staff = models.BooleanField(default=False)  # staff member
    profile_photo = models.ForeignKey(Photo, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='user_clients')
    start_date = models.DateTimeField(default=now)
    first_login = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', ]
    objects = UserManager()

    def __str__(self):
        return self.first_name

    def get_full_name(self):
        # The user is identified by their Username ;)
        return self.first_name if self.last_name is None else self.first_name + " " + self.last_name

    def get_short_name(self):
        # The user is identified by their Username address
        return self.first_name

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True

    def set_first_login(self):
        self.first_login = True
        self.save()

    def set_not_first_login(self):
        self.first_login = False
        self.save()

    @property
    def has_to_change_password(self):
        return self.first_login

    def password_is_same(self, password):
        # check if password is same as the one set
        if self.password == make_password(password):
            return True
        return False

    def send_password_email(self):
        send_password_reset_email(self.first_name, self.email)

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        return self.staff

    @property
    def is_admin(self):
        """Is the user an admin member?"""
        return self.admin

    @property
    def is_superuser(self):
        """Is the user a superuser?"""
        return self.admin

    @property
    def user_active(self):
        """Is the user active / can he log in?"""
        return self.is_active


class Album(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photos = models.ManyToManyField(Photo, verbose_name=_('Photos'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    was_viewed = models.BooleanField(default=False, verbose_name=_('Was viewed'))

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.owner)

    def set_active(self):
        self.is_active = True
        self.save()

    def set_inactive(self):
        self.is_active = False
        self.save()

    def set_viewed(self):
        self.was_viewed = True
        self.save()

    def set_not_viewed(self):
        self.was_viewed = False
        self.save()

    def get_photos(self):
        return self.photos.all()

    def get_photos_count(self):
        c_print(f"photos count: {self.photos.count()}, photos: {self.photos.all()}")
        return self.photos.count()

    def get_photos_liked_count(self):
        return self.photos.filter(is_favorite=True).count()

    def get_photos_liked(self):
        # return thumbnails of photos that are liked
        return self.photos.filter(is_favorite=True)

    def get_photos_not_liked(self):
        return self.photos.filter(is_favorite=False)

    # delete files on the disk when deleting the object
    def delete_files(self, *args, **kwargs):
        for photo in self.photos.all():
            photo.delete()
        super().delete(*args, **kwargs)


class OwnerProfilePhoto(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='RoosPP', null=True, blank=True)

    def __str__(self):
        return self.name
