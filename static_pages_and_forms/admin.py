from django.contrib import admin

from .models import *


class QuarantineAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'created_at', 'reason')
    search_fields = ('full_name', 'email', 'message')
    list_filter = ('created_at',)
    actions = ['approve_message']

    def approve_message(self, request, queryset):
        count = 0
        for message in queryset:
            # Move the message to your Contact model
            ContactForm.objects.create(
                full_name=message.full_name,
                email=message.email,
                message=message.message
            )
            message.delete()  # Optionally delete the message from Quarantine after approval
            count += 1
        self.message_user(request, f"{count} messages approved and moved to Contact.")

    approve_message.short_description = "Approve selected messages and move to Contact"


admin.site.register(ContactForm)
admin.site.register(Quarantine, QuarantineAdmin)
