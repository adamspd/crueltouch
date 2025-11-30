# client/models.py
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

# Assuming BasePhoto and utils are where you said they were
from core.models import BasePhoto
from utils.crueltouch_utils import c_print, send_password_reset_email


class UserManager(BaseUserManager):
    """
    Custom manager to handle email-based authentication.
    """

    def create_user(self, first_name, email, last_name=None, password=None, **extra_fields):
        if not email:
            raise ValueError(_('You must provide an email address'))
        if not first_name:
            raise ValueError(_('User must have a first name'))

        email = self.normalize_email(email)
        user = self.model(
                email=email,
                first_name=first_name,
                last_name=last_name,
                **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staff_user(self, first_name, email, password, last_name=None):
        """Creates and saves a staff user."""
        return self.create_user(
                first_name=first_name,
                email=email,
                last_name=last_name,
                password=password,
                is_staff=True,
                is_superuser=False
        )

    def create_superuser(self, first_name, email, password, last_name=None):
        """Creates and saves a superuser."""
        return self.create_user(
                first_name=first_name,
                email=email,
                last_name=last_name,
                password=password,
                is_staff=True,
                is_superuser=True
        )


class UserClient(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.
    Uses email as identifier. Includes client-specific logic (address, phone).
    """
    email = models.EmailField(
            max_length=255,
            unique=True,
            help_text=_("A valid email address. Used as login.")
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(
            default=True,
            help_text=_("Designates whether this user should be treated as active.")
    )
    is_staff = models.BooleanField(
            default=False,
            help_text=_("Designates whether the user can log into this admin site.")
    )

    # Contact Info
    phone_regex = RegexValidator(
            regex=r'^\d{15}$',
            message=_("Phone number must be exactly 15 digits. No spaces or dashes.")
    )
    phone_number = models.CharField(
            validators=[phone_regex],
            max_length=18,
            blank=True,
            null=True,
            default="",
            help_text=_("Format: 15 digits only.")
    )
    address = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            default="",
            help_text=_("City and State is sufficient.")
    )

    # App specific
    profile_photo = models.ForeignKey(
            'Photo',  # String reference allows circular imports if needed
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='user_clients'
    )
    start_date = models.DateTimeField(default=now)
    first_login = models.BooleanField(
            default=False,
            help_text=_("If True, user must change password on next login.")
    )

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return self.get_full_name() or self.email

    # --- Utility Methods (Restored) ---

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
        return self.first_name

    def has_perm(self, perm, obj=None):
        """Explicit superuser check overrides standard permissions."""
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """Explicit superuser check for app labels."""
        if self.is_superuser:
            return True
        return super().has_module_perms(app_label)

    # --- Password Management Utilities (Restored) ---

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
        return self.first_login

    def password_is_same(self, password):
        """Check if the provided password matches the user's current password."""
        return self.check_password(password)

    def send_password_email(self):
        """Send a password-reset email to the user."""
        send_password_reset_email(self.first_name, self.email)


class Photo(BasePhoto):
    """
    Client-specific photo logic.
    """
    file = models.ImageField(upload_to='Client', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='Client/thumbnails', null=True, blank=True)

    is_favorite = models.BooleanField(default=False)
    can_be_downloaded = models.BooleanField(default=False)

    # --- Restored Methods ---
    def set_favorite(self):
        self.is_favorite = True
        self.save(update_fields=['is_favorite'])

    def set_not_favorite(self):
        self.is_favorite = False
        self.save(update_fields=['is_favorite'])

    def set_can_be_downloaded(self):
        self.can_be_downloaded = True
        self.save(update_fields=['can_be_downloaded'])

    def set_can_not_be_downloaded(self):
        self.can_be_downloaded = False
        self.save(update_fields=['can_be_downloaded'])

    def get_is_favorite(self):
        """Returns CSS class string. Kept for template compatibility."""
        return "like is-active" if self.is_favorite else ""

    def _post_save_image_processing(self):
        """Only create thumbnail, don't convert to WebP"""
        self.create_thumbnail_if_needed(base_height=300)


class Album(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photos = models.ManyToManyField(Photo, verbose_name=_('Photos'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    was_viewed = models.BooleanField(default=False, verbose_name=_('Was viewed'))

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.owner)

    # --- Restored Methods ---
    def set_active(self):
        self.is_active = True
        self.save(update_fields=['is_active'])

    def set_inactive(self):
        self.is_active = False
        self.save(update_fields=['is_active'])

    def set_viewed(self):
        self.was_viewed = True
        self.save(update_fields=['was_viewed'])

    def set_not_viewed(self):
        self.was_viewed = False
        self.save(update_fields=['was_viewed'])

    def get_photos(self):
        return self.photos.all()

    def get_photos_count(self):
        # Kept the print because you likely use it for debugging logs
        c_print(f"photos count: {self.photos.count()}, photos: {self.photos.all()}")
        return self.photos.count()

    def get_photos_liked_count(self):
        return self.photos.filter(is_favorite=True).count()

    def get_photos_liked(self):
        return self.photos.filter(is_favorite=True)

    def get_photos_not_liked(self):
        return self.photos.filter(is_favorite=False)

    def delete_files(self, *args, **kwargs):
        """Manually delete photo files."""
        for photo in self.photos.all():
            photo.delete()
        super().delete(*args, **kwargs)


# Kept exactly as is
class OwnerProfilePhoto(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='RoosPP', null=True, blank=True)

    def __str__(self):
        return self.name
