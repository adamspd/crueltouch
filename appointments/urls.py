from django.urls import path

from appointments.views import appointment_request, get_available_slots_ajax, get_next_available_date, \
    appointment_request_submit, appointment_client_information, appointment_payment

app_name = 'appointment'

urlpatterns = [
    # homepage
    path('request/<int:service_id>/', appointment_request, name='appointment_request'),
    path('available_slots/', get_available_slots_ajax, name='available_slots_ajax'),
    path('request_next_available_slot/<int:service_id>/', get_next_available_date, name='request_next_available_slot'),
    path('request-submit/', appointment_request_submit, name='appointment_request_submit'),
    path('client-information/<int:appointment_request_id>/<str:id_request>/', appointment_client_information,
         name='appointment_client_information'),
    path('payment/<int:appointment_id>/<str:id_request>/', appointment_payment, name='appointment_payment')
]
