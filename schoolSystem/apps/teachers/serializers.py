from django.db import transaction
from rest_framework import serializers
from apps.accounts.models import User
from .models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    password = serializers.CharField(write_only=True, required=False)
    subject_names = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            
            "id","user_id", "email", "first_name", "last_name", "password",
            "qualification", "contact", "subjects", "subject_names",
        ]

    def get_subject_names(self, obj):
        return [s.subject_name for s in obj.subjects.all()]

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Required when creating a new teacher."})

        if self.instance is None:
            email = attrs.get("user", {}).get("email")
            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({"email": "A user with this email already exists."})

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        password = validated_data.pop("password")
        subjects = validated_data.pop("subjects", [])

        with transaction.atomic():
            user = User.objects.create_user(
                email=user_data["email"],
                password=password,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                role=User.Role.TEACHER,
            )
            teacher = Teacher.objects.create(user=user, **validated_data)
            teacher.subjects.set(subjects)

        return teacher

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        validated_data.pop("password", None)
        subjects = validated_data.pop("subjects", None)

        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if subjects is not None:
            instance.subjects.set(subjects)

        return instance