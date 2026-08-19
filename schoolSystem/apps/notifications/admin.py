
# apps/notifications/admin.py
from django.contrib import admin
from .models import Notification, NotificationRecipient

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient_role', 'class_obj', 'sender', 'created_at')

@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'read_at')
    list_filter = ('read_at',)