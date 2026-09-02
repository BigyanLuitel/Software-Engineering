from django.db import transaction
from rest_framework import serializers
from apps.accounts.models import User
from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = [
            "id", "email", "first_name", "last_name", "password",
            "student_class", "date_of_birth", "gender", "roll_number",
            "parent_name", "parent_contact", "photo",
        ]

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Required when creating a new student."})

        if self.instance is None:
            email = attrs.get("user", {}).get("email")
            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email": "A user with this email already exists."})

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = validated_data.pop("password")

        with transaction.atomic():
            user = User.objects.create_user(
                email=user_data["email"],
                password=password,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                role=User.Role.STUDENT,
            )
            student = Student.objects.create(user=user, **validated_data)

        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        validated_data.pop("password", None)

        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance