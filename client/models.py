# client/models.py

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin, User
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from core.models import BasePhoto
from utils.crueltouch_utils import c_print, send_password_reset_email

phone_regex = RegexValidator(
        regex=r'^\d{15}$',
        message=_("Phone number must not contain spaces, letters, parentheses or dashes. It must contain 15 digits.")
)


class Photo(BasePhoto):
    """
    Client photos - for client selection/favorites.
    Different from homepage/portfolio - has favorite/download tracking.
    """
    file = models.ImageField(upload_to='Client', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='Client/thumbnails', null=True, blank=True)

    # Client-specific fields
    is_favorite = models.BooleanField(default=False)
    can_be_downloaded = models.BooleanField(default=False)

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

    def get_is_favorite(self):
        return "like is-active" if self.is_favorite else ""

    def _post_save_image_processing(self):
        """Only create thumbnail, don't convert to WebP (client may want originals)"""
        self.create_thumbnail_if_needed(base_height=300)


class UserManager(BaseUserManager):
    """
    Custom user manager for UserClient model.
    Uses email as the unique identifier instead of username.
    """

    def create_user(self, first_name, email, last_name=None, password=None,
                    is_superuser=False, is_staff=False, is_active=True):
        """
        Creates and saves a regular User with the given email and password.
        """
        if not email:
            raise ValueError(_('You must provide an email address'))
        if not first_name:
            raise ValueError(_("User must have a first name"))

        user_obj = self.model(email=self.normalize_email(email))
        user_obj.first_name = first_name
        user_obj.last_name = last_name
        user_obj.is_staff = is_staff
        user_obj.is_superuser = is_superuser
        user_obj.is_active = is_active
        user_obj.set_password(password)
        user_obj.save(using=self._db)
        return user_obj

    def create_staff_user(self, first_name, email, password, last_name=None):
        """
        Creates and saves a staff user.
        """
        user = self.create_user(
                first_name=first_name,
                email=email,
                last_name=last_name,
                password=password,
                is_staff=True,
                is_superuser=False
        )
        return user

    def create_superuser(self, first_name, email, password, last_name=None):
        """
        Creates and saves a superuser with full admin access.
        """
        user = self.create_user(
                first_name=first_name,
                email=email,
                last_name=last_name,
                password=password,
                is_staff=True,
                is_superuser=True
        )
        return user


class UserClient(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the crueltouch/tchiiz.
    Uses email as the unique identifier instead of username.

    Inherits from:
    - AbstractBaseUser: Provides password hashing, last_login, is_active
    - PermissionsMixin: Provides is_superuser, is_staff, groups, user_permissions
    """
    # Core user fields
    email = models.EmailField(
            max_length=255,
            unique=True,
            help_text=_("A valid email address")
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    # Contact information
    phone_number = models.CharField(
            max_length=18,
            blank=True,
            null=True,
            default="",
            help_text=_("Phone number must not contain spaces, letters, parentheses or dashes. "
                        "It must contain 15 digits.")
    )
    address = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            default="",
            help_text=_("Does not have to be specific, just the city and the state")
    )

    # App-specific fields
    profile_photo = models.ForeignKey(
            Photo,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='user_clients'
    )
    start_date = models.DateTimeField(default=now)
    first_login = models.BooleanField(
            default=False,
            help_text=_("If True, user must change password on next login")
    )

    # Required for a custom user model
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']
    objects = UserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        """Returns the user's full name if possible, otherwise first name, last name, or email."""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        return self.email

    def get_short_name(self):
        """Returns the user's first name."""
        return self.first_name

    def has_perm(self, perm, obj=None):
        """
        Does the user have a specific permission?
        Superusers automatically have all permissions.
        """
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """
        Does the user have permissions to view the app `app_label`?
        Superusers can view all apps.
        """
        if self.is_superuser:
            return True
        return super().has_module_perms(app_label)

    # Password management
    def set_first_login(self):
        """Mark that the user needs to change password on next login."""
        self.first_login = True
        self.save(update_fields=['first_login'])

    def set_not_first_login(self):
        """Mark that the user has completed his first login password change."""
        self.first_login = False
        self.save(update_fields=['first_login'])

    @property
    def has_to_change_password(self):
        """Returns True if user must change password before accessing the site."""
        return self.first_login

    def password_is_same(self, password):
        """Check if the provided password matches the user's current password."""
        return self.password == make_password(password)

    def send_password_email(self):
        """Send a password-reset email to the user."""
        send_password_reset_email(self.first_name, self.email)


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
