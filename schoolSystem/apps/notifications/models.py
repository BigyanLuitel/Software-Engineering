# apps/notifications/models.py
from django.db import models
from django.conf import settings
from apps.academics.models import Class


class Notification(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_notifications")
    title = models.CharField(max_length=150)
    message = models.TextField()
    recipient_role = models.CharField(max_length=10, choices=[("ALL", "All"), ("TEACHER", "Teacher"), ("STUDENT", "Student")])
    class_obj = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: restrict to one class")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} \u2192 {self.recipient_role}"


class NotificationRecipient(models.Model):
    """
    Materialized per-user delivery + read status. Created upfront by
    send_notification() for every matching user at send time, rather
    than computed on the fly -- this is what makes "unread count for
    this user" a fast, simple query instead of recalculating who
    matches the broadcast criteria every time someone checks.
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="recipients")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_notifications")
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("notification", "user")