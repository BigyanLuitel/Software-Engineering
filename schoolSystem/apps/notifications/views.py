from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin
from .models import Notification, NotificationRecipient
from .serializers import NotificationSerializer, NotificationRecipientSerializer
from .services import send_notification, mark_read, unread_count


class NotificationViewSet(viewsets.ModelViewSet):
    """
    Admin-only: creating/broadcasting notifications. Students/Teachers
    interact with their OWN inbox via NotificationRecipientViewSet
    below, not this one.
    """
    queryset = Notification.objects.select_related("sender", "class_obj").all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        """
        Overrides the default create -- a Notification isn't just a
        plain row insert, it must fan out to NotificationRecipient
        for every matching user. send_notification() already does
        both atomically, so we call it directly instead of using
        the default ModelSerializer.save() flow, which only knows
        how to create the one Notification row, not the fan-out.
        """
        title = request.data.get("title")
        message = request.data.get("message")
        recipient_role = request.data.get("recipient_role")
        class_id = request.data.get("class_obj")

        class_obj = None
        if class_id:
            from apps.academics.models import Class
            try:
                class_obj = Class.objects.get(id=class_id)
            except Class.DoesNotExist:
                return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)

        notification = send_notification(request.user, title, message, recipient_role, class_obj)
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)


class NotificationRecipientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A user's OWN received notifications -- read-only (list/retrieve),
    plus the mark-read action. get_queryset() filters to request.user
    only, so nobody can see another user's inbox by guessing IDs.
    """
    serializer_class = NotificationRecipientSerializer

    def get_queryset(self):
        return NotificationRecipient.objects.filter(user=self.request.user).select_related("notification")

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read_action(self, request, pk=None):
        recipient = self.get_object()
        updated = mark_read(recipient)
        return Response(NotificationRecipientSerializer(updated).data)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count_action(self, request):
        count = unread_count(request.user)
        return Response({"unread_count": count})