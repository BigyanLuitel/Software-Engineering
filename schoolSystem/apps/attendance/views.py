from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.academics.models import Class
from .models import Attendance
from .serializers import AttendanceSerializer, BulkMarkAttendanceSerializer
from .services import mark_class_attendance
from apps.accounts.permissions import IsAdminOrTeacher, IsStudent
from apps.students.models import Student


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related("student__user").all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrTeacher]

    @action(detail=False, methods=["post"], url_path="mark-class")
    def mark_class(self, request):
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

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[IsStudent])
    def me(self, request):
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"detail": "No student profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        records = Attendance.objects.filter(student=student).order_by("-date")
        return Response(AttendanceSerializer(records, many=True).data)