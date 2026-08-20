from rest_framework import serializers
from .models import Result


class ResultSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    subject_name = serializers.CharField(source="subject.subject_name", read_only=True)
    examination_display = serializers.CharField(source="examination.__str__", read_only=True)

    class Meta:
        model = Result
        fields = [
            "id", "student", "student_email", "examination", "examination_display",
            "subject", "subject_name", "marks_obtained", "full_marks",
            "grade", "grade_point", "passed",
        ]
        read_only_fields = ["grade", "grade_point", "passed"]  # these are auto-computed in Result.save()