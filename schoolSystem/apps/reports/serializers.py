from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    generated_by_email = serializers.EmailField(source="generated_by.email", read_only=True, allow_null=True)
    class_name = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source="get_report_type_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "report_type", "report_type_display", "generated_by", "generated_by_email",
            "class_obj", "class_name", "date_from", "date_to", "generated_at", "data",
        ]
        read_only_fields = ["generated_by", "generated_at", "data"]

    def get_class_name(self, obj):
        return str(obj.class_obj) if obj.class_obj else None