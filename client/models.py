import os
from datetime import datetime
from io import BytesIO
from sqlite3 import IntegrityError

import PIL
from PIL import Image
from PIL.ExifTags import TAGS
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, PermissionsMixin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

DATABASE_UPDATE = os.getenv('LIST_OF_LOCAL_IPS')
TEST_EMAIL = os.getenv('TEST_EMAIL')

from crueltouch.productions import production_debug
from utils.crueltouch_utils import c_print, notify_admin_session_request_received_via_email, \
    send_session_request_received_email, get_estimated_response_time, get_today_date, status_change_email, \
    send_password_reset_email

phone_regex = RegexValidator(
    regex=r'^\d{10}$',
    message=_("Phone number must not contain spaces, letters, parentheses or dashes. It must contain 10 digits.")
)


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
        user_obj.is_active = is_active
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
    email = models.EmailField(max_length=255, unique=True, default="", help_text=_("A valid email address, please"))
    first_name = models.CharField(max_length=255, default=None)
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=True, null=True, default="",
                                    help_text=_("Phone number must not contain spaces, letters, parentheses or "
                                                "dashes. It must contain 10 digits."))
    address = models.CharField(max_length=255, blank=True, null=True, default="",
                               help_text=_("Does not have to be specific, just the city and the state"))

    is_active = models.BooleanField(default=True)  # can login
    admin = models.BooleanField(default=False)  # superuser
    staff = models.BooleanField(default=False)  # staff member

    start_date = models.DateTimeField(default=now)
    first_login = models.BooleanField(default=False)

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
    def user_active(self):
        """Is the user active / can he log in?"""
        return self.is_active


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
            img = img.resize((width_size, base_height), PIL.Image.ANTIALIAS)
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


class BookMe(models.Model):
    SESSION_TYPE = (
        ('portrait', 'Portrait'),
        ('birthday', 'Birthday'),
        ('wOthers', 'Wedding and other events'),
    )
    WHERE = (
        ('studio', 'Studio'),
        ('outdoor', 'Outdoor'),
        ('orlando', 'Orlando'),
        ('others', 'Others'),
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
    email = models.EmailField(default="", null=False, blank=False, help_text=_("A valid email address, please"))
    session_type = models.CharField(max_length=200, null=True, choices=SESSION_TYPE)
    place = models.CharField(max_length=200, null=True, choices=WHERE)
    phone_number = models.CharField(validators=[phone_regex], max_length=10, blank=False, null=False, default="",
                                    help_text=_("Phone number must not contain spaces, letters, parentheses or "
                                                "dashes. It must contain 10 digits."))
    desired_date = models.DateField(null=True, blank=False, default="1999-12-31")
    address = models.CharField(max_length=255, blank=False, null=False, default="",
                               help_text=_("Does not have to be specific, just the city and the state"))
    package = models.CharField(max_length=2, null=True, blank=False)
    status = models.CharField(max_length=200, null=True, choices=STATUS, default=_("pending"))
    old_status = models.CharField(max_length=200, null=True, choices=STATUS, default=_("pending"))
    time_book_taken = models.DateTimeField(default=now)
    time_book_accepted = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    estimated_total = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return self.full_name

    def send_late_booking_confirmation_email(self) -> bool:
        if not self.email_sent:
            # send email to user
            sent = send_session_request_received_email(
                email_address=self.email, full_name=self.full_name,
                session_type=self.session_type, place=self.place, package=self.get_package_display,
                status=self.status, total=self.estimated_total,
                estimated_response_time=get_estimated_response_time(),
                subject=_("Thank you for your booking!"), late=True)
            self.email_sent = True
            self.save()
            # send email to admin
            notify_admin_session_request_received_via_email(
                today=get_today_date(), client_name=self.full_name,
                client_email=self.email, session_type=self.session_type,
                place=self.place, package=self.get_package_display, status=self.status,
                total=self.estimated_total, phone=self.phone_number,
                address=self.address, desired_date=self.get_desired_date,
                estimated_response_time=get_estimated_response_time(), subject=_("New booking request received"))
            return sent

    def get_if_email_was_sent_string(self):
        if self.email_sent:
            return _("Yes")
        else:
            return _("No")

    def get_if_email_was_sent_boolean(self):
        return self.email_sent

    def get_estimated_total(self):
        return self.estimated_total

    def save(self, *args, **kwargs):
        if not self.estimated_total:
            self.estimated_total = get_estimated_total(self.session_type, self.package, self.place)
        # if existing object
        if self.pk:
            if self.status != self.old_status and self.email_sent and self.status != _("pending"):
                status_change_email(
                    book_me=self, subject=_("Your booking request status has changed!")
                )
                self.old_status = self.status
        return super().save(*args, **kwargs)

    @property
    def status_changed(self):
        if self.status != "pending":
            return True
        else:
            return False

    @property
    def is_phone(self):
        if self.phone_number:
            return True
        else:
            return False

    @property
    def get_phone_number(self):
        if self.phone_number:
            return self.phone_number
        return _("No data")

    @property
    def get_address(self):
        if self.address:
            return self.address
        return _("No data")

    @property
    def get_desired_date(self):
        date_book = datetime.strptime('1999-12-31', '%Y-%m-%d')
        if self.desired_date == date_book.date():
            return _("No data")
        else:
            # return a string value
            return self.desired_date.strftime('%Y-%m-%d')

    @property
    def get_package_display(self):
        if self.package == "3":
            return _("3 photos")
        elif self.package == "7":
            return _("7 photos")
        elif self.package == "15":
            return _("15 photos")
        elif self.package == "30":
            return _("30 photos")
        else:
            return _("No data")


class OwnerProfilePhoto(models.Model):
    name = models.CharField(null=True, max_length=150)
    file = models.ImageField(upload_to='RoosPP', null=True, blank=True)

    def __str__(self):
        return self.name


def get_estimated_total(session_type, package, place):
    basic = "$220"
    medium = "$325"
    premium = "$460"
    if session_type != "wOthers":
        if place == "studio":
            if package == "7":
                return "$260"
            elif package == "15":
                return "$365"
            elif package == "30":
                return "$500"
        if place == "outdoor":
            if package == "7":
                return basic
            elif package == "15":
                return medium
            elif package == "30":
                return premium
        if place == "orlando":
            if package == "3":
                return "$130 +$40 if studio"
            elif package == "7":
                return basic + " +$40 if studio"
            elif package == "15":
                return medium + " +$40 if studio"
            elif package == "30":
                return premium + " +$40 if studio"
    else:
        return _("Contact us for more information")


def create_client(client_name: str, client_email: str):
    client_password = "Crueltouch2022"
    try:
        client = UserClient.objects.create_user(first_name=client_name, email=client_email,
                                                password=client_password)
    except IntegrityError:
        return False
    client.save()
    client.set_first_login()
    client.send_password_email()
    return True


@receiver(post_save, sender=BookMe)
def account_authorization_status_handler(sender, instance, created, *args, **kwargs):
    if created:
        if production_debug or DATABASE_UPDATE:
            client_email = TEST_EMAIL
        else:
            client_email = instance.email
        create_client(instance.full_name, client_email)
        c_print("client.models:235 | Sending email to admin to notify of a session request")
        notify_admin_session_request_received_via_email(
            today=get_today_date(),
            client_name=instance.full_name,
            client_email=client_email,
            phone=instance.phone_number,
            session_type=instance.session_type,
            place=instance.place,
            package=instance.get_package_display,
            status=instance.status,
            total=instance.estimated_total,
            estimated_response_time=get_estimated_response_time(),
            address=instance.address,
            desired_date=instance.get_desired_date,
            subject=_("New booking request received")
        )

        c_print("client.models:249 | Sending email to user to thank them for their request")
        sent = send_session_request_received_email(
            full_name=instance.full_name,
            email_address=client_email,
            session_type=instance.session_type,
            place=instance.place,
            package=instance.get_package_display,
            status=instance.status,
            total=instance.estimated_total,
            estimated_response_time=get_estimated_response_time(),
            subject=_("Thank you for your booking!"),
            late=False
        )
        if sent:  # if email was sent
            c_print("client.models:263 | Email sent to user")
            instance.email_sent = True
            instance.save()
