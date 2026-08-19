# apps/notifications/services.py
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from apps.students.models import Student
from apps.teachers.models import Teacher
from .models import Notification, NotificationRecipient


@transaction.atomic
def send_notification(sender, title, message, recipient_role, class_obj=None):
    User = settings.AUTH_USER_MODEL
    notification = Notification.objects.create(
        sender=sender, title=title, message=message,
        recipient_role=recipient_role, class_obj=class_obj,
    )

    if recipient_role == "STUDENT":
        qs = Student.objects.filter(student_class=class_obj) if class_obj else Student.objects.all()
        user_ids = qs.values_list("user_id", flat=True)
    elif recipient_role == "TEACHER":
        user_ids = Teacher.objects.values_list("user_id", flat=True)
    else:  # ALL
        user_ids = Student.objects.values_list("user_id", flat=True).union(
            Teacher.objects.values_list("user_id", flat=True)
        )

    NotificationRecipient.objects.bulk_create([
        NotificationRecipient(notification=notification, user_id=uid) for uid in user_ids
    ])
    return notification


def mark_read(notification_recipient: NotificationRecipient):
    if notification_recipient.read_at is None:
        notification_recipient.read_at = timezone.now()
        notification_recipient.save()
    return notification_recipient


def unread_count(user) -> int:
    return NotificationRecipient.objects.filter(user=user, read_at__isnull=True).count()