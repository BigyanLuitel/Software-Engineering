from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdminOrTeacher
from apps.academics.models import Class
from .models import Attendance
from .serializers import AttendanceSerializer, BulkMarkAttendanceSerializer
from .services import mark_class_attendance


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("student__user").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrTeacher]  # Students don't get general attendance CRUD -- their own-record view is a separate, narrower endpoint (future piece)

    @action(detail=False, methods=["post"], url_path="mark-class")
    def mark_class(self, request):
        """
        POST /api/attendance/mark-class/
        Body: {"class_id": 1, "date": "2026-01-05", "status_map": {"1": "PRESENT", "2": "ABSENT"}}

        Wraps the existing mark_class_attendance() SERVICE function --
        this view does NOT reimplement the bulk-marking logic, it just
        validates input and calls the already-tested function.
        """
        serializer = BulkMarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            class_obj = Class.objects.get(id=serializer.validated_data["class_id"])
        except Class.DoesNotExist:
            return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)

        records = mark_class_attendance(
            class_obj,
            serializer.validated_data["date"],
            serializer.validated_data["status_map"],
        )
        return Response(AttendanceSerializer(records, many=True).data, status=status.HTTP_200_OK)