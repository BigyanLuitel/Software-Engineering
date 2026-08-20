from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    generated_by_email = serializers.EmailField(source="generated_by.email", read_only=True, allow_null=True)
    class_name = serializers.CharField(source="class_obj.__str__", read_only=True, allow_null=True)
    report_type_display = serializers.CharField(source="get_report_type_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "report_type", "report_type_display", "generated_by", "generated_by_email",
            "class_obj", "class_name", "date_from", "date_to", "generated_at", "data",
        ]
        read_only_fields = ["generated_by", "generated_at", "data"]  # all set by the service function, never by the client directly