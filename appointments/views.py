import base64
import datetime
import json
from datetime import date
from datetime import timedelta

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext as _, to_locale, get_language
from django.views.decorators.csrf import csrf_exempt

from appointments.forms import AppointmentRequestForm
from appointments.models import Service, Appointment, AppointmentRequest
from appointments.utils import get_available_slots, is_ajax, printing
from client.models import UserClient
from crueltouch import secrets
from utils.crueltouch_utils import email_check


# In the complete version the annotations are not included

@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def appointment_request(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    page_title = service.name + ' - ' + _('CruelTouch')
    page_description = "Book an appointment for " + service.name + " at CruelTouch."

    # get available slots for the day
    appointments = Appointment.objects.filter(appointment_request__service=service,
                                              appointment_request__date=date.today())
    available_slots = get_available_slots(date.today(), appointments)
    date_chosen = date.today().strftime("%A, %B %d, %Y")
    get_locale = to_locale(get_language())
    context = {
        'service': service,
        'page_title': page_title,
        'page_description': page_description,
        'available_slots': available_slots,
        'date_chosen': date_chosen,
        'locale': get_locale
    }
    return render(request, 'appointments/appointments.html', context=context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def get_available_slots_ajax(request):
    if is_ajax(request=request):
        # Get the selected date from the AJAX request
        today = date.today()
        selected_date = request.GET.get('selected_date')

        # Convert the selected date string to a datetime object
        selected_date = datetime.datetime.strptime(selected_date, '%Y-%m-%d').date()

        # Get the appointments for the selected date
        if selected_date < today:
            return JsonResponse(
                {
                    'available_slots': [],
                    'date_chosen': '',
                    'error': True,
                    'message': 'Date is in the past',
                })
        appointments = Appointment.objects.filter(appointment_request__date=selected_date)

        # Get the available slots for the selected date
        available_slots = get_available_slots(selected_date, appointments)
        date_chosen = selected_date.strftime("%A, %B %d, %Y")
        # Return the available slots as a JSON response
        if len(available_slots) == 0:
            return JsonResponse(
                {'available_slots': available_slots, 'date_chosen': date_chosen, 'message': 'No availability',
                 'error': False})
        return JsonResponse(
            {'available_slots': available_slots, 'date_chosen': date_chosen, 'message': '', 'error': False})


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def get_next_available_date(request, service_id):
    if is_ajax(request=request):
        # Get the service and the current date
        service = get_object_or_404(Service, pk=service_id)
        current_date = date.today()

        # Find the next date with available slots
        next_available_date = None
        day_offset = 0
        while next_available_date is None:
            potential_date = current_date + timedelta(days=day_offset)
            appointments = Appointment.objects.filter(appointment_request__service=service,
                                                      appointment_request__date=potential_date)
            available_slots = get_available_slots(potential_date, appointments)
            if available_slots:
                next_available_date = potential_date
            day_offset += 1

        # Return the next available date as a JSON response
        return JsonResponse({'next_available_date': next_available_date.isoformat()})


def appointment_request_submit(request):
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        date_f = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        service = request.POST.get('service')

        printing("date_f: ", date_f, " start_time: ", start_time, " end_time: ", end_time, " service: ", service)
        if form.is_valid():
            ar = form.save()

            # Redirect the user to the account creation page
            return redirect('appointment:appointment_client_information', appointment_request_id=ar.id,
                            id_request=ar.id_request)
    else:
        printing("else")
        form = AppointmentRequestForm()

    return render(request, 'appointments/appointments.html', {'form': form})


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def appointment_client_information(request, appointment_request_id, id_request):
    ar = get_object_or_404(AppointmentRequest, pk=appointment_request_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        want_reminder = request.POST.get('want_reminder')
        if want_reminder == 'on':
            want_reminder = True
        else:
            want_reminder = False
        address = request.POST.get('address')
        additional_info = request.POST.get('additional_info')
        printing("name: ", name, " email: ", email, " phone: ", phone, " want_reminder: ", want_reminder, " address: ",
                 address, " additional_info: ", additional_info)

        # check if email is already in the database
        is_email_in_db = UserClient.objects.filter(email__exact=email).exists()
        if is_email_in_db:
            messages.error(request, "Email '" + email + "' already exists. Login to your account.")
            return redirect('appointment:appointment_client_information', appointment_request_id=ar.id,
                            id_request=id_request)

        # create a new user
        user = UserClient.objects.create_user(first_name=name, email=email)
        user.password = make_password("CruelTouch2023")
        user.set_first_login()
        user.phone_number = phone
        user.address = address
        user.save()
        messages.success(request, "An account was created for you.")
        appointment = Appointment.objects.create(client=user, appointment_request=ar, want_reminder=want_reminder,
                                                 additional_info=additional_info)
        appointment.save()
        printing("Redirecting to appointment payment with appointment_id", appointment.id, "and id_request", id_request)
        return redirect('appointment:appointment_payment', appointment_id=appointment.id, id_request=id_request)
    return render(request, 'appointments/appointment_client_information.html',
                  {'appointment': ar})


def get_paypal_access_token(client_id, client_secret, endpoint_url):
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth}",
    }
    response = requests.post(f"{endpoint_url}/v1/oauth2/token", data="grant_type=client_credentials", headers=headers)
    data = response.json()
    return data["access_token"]


def generate_client_token(access_token, endpoint_url):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept-Language": "en_US",
        "Content-Type": "application/json",
    }
    response = requests.post(f"{endpoint_url}/v1/identity/generate-token", headers=headers)
    data = response.json()
    return data["client_token"]


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
@csrf_exempt
def create_order(request, appointment_id):
    if request.method == 'POST':
        ar = get_object_or_404(Appointment, pk=appointment_id)
        environment = secrets.ENVIRONMENT
        ENDPOINT_URL = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"
        # Prepare the payload
        payload = {
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": "5.00"
                    },
                    "reference_id": f"{ar.id_request}",
                }
            ],
            "intent": "CAPTURE",
        }

        access_token = get_paypal_access_token(secrets.CLIENT_ID, secrets.CLIENT_SECRET, ENDPOINT_URL)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        # Send the create order request to PayPal
        response = requests.post(f"{ENDPOINT_URL}/v2/checkout/orders", data=json.dumps(payload), headers=headers)

        if response.status_code == 201:
            order_data = response.json()
            order_id = order_data["id"]
            return JsonResponse({"id": order_id})
        else:
            return JsonResponse({"error": "Failed to create order"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
@csrf_exempt
def capture_order(request, order_id):
    if request.method == 'POST':
        # Implement your logic for capturing an order here.
        # For now, let's assume the order was captured successfully.
        order_data = {"order_id": order_id,
                      "status": "COMPLETED"}  # Replace this with the actual order data from your order capturing logic.
        return JsonResponse(order_data)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def appointment_payment(request, appointment_id, id_request):
    printing("appointment_id", appointment_id, "id_request", id_request)
    ar = get_object_or_404(Appointment, pk=appointment_id)
    environment = secrets.ENVIRONMENT
    endpoint_url = "https://api-m.sandbox.paypal.com" if environment == "sandbox" else "https://api-m.paypal.com"
    client_id = secrets.CLIENT_ID
    client_secret = secrets.CLIENT_SECRET

    access_token = get_paypal_access_token(client_id, client_secret, endpoint_url)
    client_token = generate_client_token(access_token, endpoint_url)
    context = {
        "client_token": client_token,
        "appointment": ar,
        "id_request": id_request,
        "client_id": client_id,
    }
    return render(request, 'appointments/appointment_payment.html', context=context)


@login_required(login_url='/administration/login/')
@user_passes_test(email_check, login_url='/administration/login/')
def payment_success(request, appointment_id, order_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    context = {
        "appointment": appointment,
        "order_id": order_id,
    }
    return render(request, 'appointments/payment_success.html', context=context)
