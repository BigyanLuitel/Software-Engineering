from rest_framework import serializers
from .models import Class, Subject, ClassSubject, Examination


class ClassSerializer(serializers.ModelSerializer):
    teacher_email = serializers.EmailField(source="teacher.email", read_only=True, allow_null=True)

    class Meta:
        model = Class
        fields = ["id", "class_name", "section", "teacher", "teacher_email"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "subject_name", "subject_code"]


class ClassSubjectSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="class_obj.__str__", read_only=True)
    subject_name = serializers.CharField(source="subject.subject_name", read_only=True)

    class Meta:
        model = ClassSubject
        fields = ["id", "class_obj", "class_name", "subject", "subject_name"]


class ExaminationSerializer(serializers.ModelSerializer):
    term_display = serializers.CharField(source="get_term_display", read_only=True)

    class Meta:
        model = Examination
        fields = ["id", "term", "term_display", "academic_year", "is_final"]