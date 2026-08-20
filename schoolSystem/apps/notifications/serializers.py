from rest_framework import serializers
from .models import Notification, NotificationRecipient


class NotificationSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source="sender.email", read_only=True, allow_null=True)
    class_name = serializers.CharField(source="class_obj.__str__", read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = ["id", "title", "message", "recipient_role", "class_obj", "class_name", "sender", "sender_email", "created_at"]
        read_only_fields = ["sender", "created_at"]


class NotificationRecipientSerializer(serializers.ModelSerializer):
    notification_title = serializers.CharField(source="notification.title", read_only=True)
    notification_message = serializers.CharField(source="notification.message", read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = ["id", "notification", "notification_title", "notification_message", "read_at"]
        read_only_fields = ["notification", "read_at"]  # read_at only ever set via mark-read action, never directly