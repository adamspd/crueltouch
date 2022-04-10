from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class UserManager(BaseUserManager):

    def create_user(self, first_name, email, password=None, is_admin=False, is_staff=False, is_active=True):
        if not email:
            raise ValueError(_('You must provide an email address'))
        if not first_name:
            raise ValueError(_("User must have a firstname"))
        user_obj = self.model(
            email=self.normalize_email(email)
        )
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.active = is_active
        user_obj.first_name = first_name
        user_obj.set_password(password)
        user_obj.save(using=self._db)
        return user_obj

    def create_staff_user(self, first_name, email, password):
        user = self.create_user(first_name, email, password=password, is_staff=True)
        return user

    def create_superuser(self, first_name, email, password):
        user = self.create_user(first_name, email, password=password, is_staff=True, is_admin=True)
        return user


class UserClient(AbstractBaseUser, PermissionsMixin, models.Model):
    email = models.EmailField(max_length=255, unique=True, default="", help_text="A valid email address, please")
    first_name = models.CharField(max_length=255, default=None)
    active = models.BooleanField(default=True)  # can login
    admin = models.BooleanField(default=False)  # superuser
    staff = models.BooleanField(default=False)  # staff member
    start_date = models.DateTimeField(default=now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', ]
    objects = UserManager()

    def __str__(self):
        return self.first_name

    def get_full_name(self):
        # The user is identified by their Username ;)
        return self.first_name

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

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        return self.staff

    @property
    def is_admin(self):
        """Is the user an admin member?"""
        return self.admin

    @property
    def is_active(self):
        """Is the user active / can he log in?"""
        return self.active


class Album(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.owner)


class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    file = models.ImageField(upload_to='Client', null=True, blank=True)
    is_favorite = models.BooleanField(default=False)
    can_be_downloaded = models.BooleanField(default=False)

    def __str__(self):
        return str(self.album.owner) + '-' + self.file.name


class BookMe(models.Model):
    SESSION_TYPE = (
        ('portrait', 'Portrait'),
        ('birthday', 'Birthday'),
        ('wOthers', 'Wedding and other events'),
    )
    WHERE = (
        ('studio', 'Studio'),
        ('outdoor', 'Outdoor'),
        ('others', 'Others'),
    )
    PACKAGE = (
        ('7', '7 photos'),
        ('15', '15 photos'),
        ('35', '35 photos'),
    )

    STATUS = (
        ('done', 'done'),
        ('pending', 'pending'),
        ('accepted', 'accepted'),
        ('canceled', 'canceled'),
    )

    # who = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                         on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=255, blank=False, null=False)
    email = models.EmailField(default="", null=False, blank=False, help_text="A valid email address, please !")
    session_type = models.CharField(max_length=200, null=True, choices=SESSION_TYPE)
    place = models.CharField(max_length=200, null=True, choices=WHERE)
    package = models.CharField(max_length=200, null=True, choices=PACKAGE)
    status = models.CharField(max_length=200, null=True, choices=STATUS, default="pending")
    time_book_taken = models.DateTimeField(default=now)

    def __str__(self):
        return self.full_name


class OwnerProfilePhoto(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='RoosPP', null=True, blank=True)

    def __str__(self):
        return self.name
