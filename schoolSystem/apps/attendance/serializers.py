from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.user.email", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "student", "student_email", "date", "status"]


class BulkMarkAttendanceSerializer(serializers.Serializer):
    """
    NOT a ModelSerializer -- this doesn't map to one Attendance row,
    it's the input shape for marking a WHOLE CLASS at once. class_id
    and date identify which day/class; status_map is {student_id: status}.
    """
    class_id = serializers.IntegerField()
    date = serializers.DateField()
    status_map = serializers.DictField(child=serializers.CharField())