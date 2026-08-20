from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin
from apps.academics.models import Class
from .models import Report
from .serializers import ReportSerializer
from .services import generate_report


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related("generated_by", "class_obj").all()
    serializer_class = ReportSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "post", "delete", "head", "options"]  # no PUT/PATCH -- a report is a point-in-time snapshot, never edited after creation

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """
        POST /api/reports/generate/
        Body: {"report_type": "ATTENDANCE_SUMMARY", "class_id": 1,
               "date_from": "2026-01-01", "date_to": "2026-01-31"}
        (date_from/date_to only needed for ATTENDANCE_SUMMARY;
         academic_year only needed for ACADEMIC_SUMMARY)
        """
        report_type = request.data.get("report_type")
        class_id = request.data.get("class_id")
        class_obj = None
        if class_id:
            try:
                class_obj = Class.objects.get(id=class_id)
            except Class.DoesNotExist:
                return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            report = generate_report(
                report_type=report_type,
                generated_by=request.user,
                class_obj=class_obj,
                date_from=request.data.get("date_from"),
                date_to=request.data.get("date_to"),
                academic_year=request.data.get("academic_year"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)