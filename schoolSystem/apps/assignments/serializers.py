from rest_framework import serializers
from .models import Assignment


class AssignmentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="class_obj.__str__", read_only=True)
    subject_name = serializers.CharField(source="subject.subject_name", read_only=True)
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id", "title", "description", "class_obj", "class_name",
            "subject", "subject_name", "teacher", "teacher_name",
            "due_date", "attachment", "created_at",
        ]
        read_only_fields = ["teacher"]

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}".strip() or obj.teacher.email