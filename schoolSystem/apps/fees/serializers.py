from rest_framework import serializers
from .models import FeeCategory, FeeStructure, FeeInvoice


class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = ["id", "name", "is_recurring"]


class FeeStructureSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="class_obj.__str__", read_only=True)
    category_name = serializers.CharField(source="fee_category.name", read_only=True)

    class Meta:
        model = FeeStructure
        fields = ["id", "class_obj", "class_name", "fee_category", "category_name", "amount", "academic_year"]


class FeeInvoiceSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    category_name = serializers.CharField(source="fee_category.name", read_only=True)
    total_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    outstanding = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = FeeInvoice
        fields = [
            "id", "student", "student_email", "fee_category", "category_name", "month",
            "amount_due", "previous_due", "amount_paid", "due_date", "status",
            "total_due", "outstanding",
        ]
        read_only_fields = ["status"]  # status is derived by record_payment(), never set directly by a client