from rest_framework import serializers
from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "email", "first_name", "last_name",
            "student_class", "date_of_birth", "gender",
            "parent_name", "parent_contact", "photo",
        ]