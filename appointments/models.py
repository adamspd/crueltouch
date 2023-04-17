# Create your models here.
import datetime

from django.db import models

from appointments.utils import generate_random_id, get_timestamp
from client.models import UserClient


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration = models.DurationField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_duration(self):
        # return H
        return self.duration.seconds // 3600


class AppointmentRequest(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    id_request = models.CharField(max_length=100, blank=True, null=True)

    # meta data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.start_time} to {self.end_time} - {self.service.name}"

    def save(self, *args, **kwargs):
        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{self.service.id}{generate_random_id()}"
        return super().save(*args, **kwargs)


class Appointment(models.Model):
    client = models.ForeignKey(UserClient, on_delete=models.CASCADE)
    appointment_request = models.OneToOneField(AppointmentRequest, on_delete=models.CASCADE)
    want_reminder = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    id_request = models.CharField(max_length=100, blank=True, null=True)

    # meta datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} - " \
               f"{self.appointment_request.start_time.strftime('%Y-%m-%d %H:%M')} to " \
               f"{self.appointment_request.end_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if self.id_request is None:
            self.id_request = f"{get_timestamp()}{self.appointment_request.id}{generate_random_id()}"
        return super().save(*args, **kwargs)

    def get_start_time(self):
        return datetime.datetime.combine(self.appointment_request.date, self.appointment_request.start_time)

    def get_end_time(self):
        return datetime.datetime.combine(self.appointment_request.date, self.appointment_request.end_time)

    def get_service_name(self):
        return self.appointment_request.service.name

    def get_service_price(self):
        return self.appointment_request.service.price

    def get_service_img(self):
        return self.appointment_request.service.image

