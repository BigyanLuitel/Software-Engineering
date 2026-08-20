from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from apps.students.models import Student
from .models import Result
from .serializers import ResultSerializer
from .services import compute_final_result, compute_gpa


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.select_related("student__user", "subject", "examination").all()
    serializer_class = ResultSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrTeacher()]  # teachers enter term marks
        return [IsAdminOrTeacher()]

    @action(detail=False, methods=["post"], url_path="compute-final")
    def compute_final(self, request):
        """
        POST /api/results/compute-final/
        Body: {"student_id": 1, "academic_year": "2025-2026"}
        Wraps compute_final_result() -- surfaces its ValueError
        (e.g. incomplete term data) as a clean 400, not a raw 500 crash.
        """
        student_id = request.data.get("student_id")
        academic_year = request.data.get("academic_year")

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            results = compute_final_result(student, academic_year)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ResultSerializer(results, many=True).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="gpa")
    def gpa(self, request):
        """
        GET /api/results/gpa/?student_id=1&academic_year=2025-2026
        A GET, not POST, since this only READS existing Final results
        -- it doesn't compute or change anything, matching HTTP
        semantics (GET = safe, read-only).
        """
        student_id = request.query_params.get("student_id")
        academic_year = request.query_params.get("academic_year")

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            gpa_value = compute_gpa(student, academic_year)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"student_id": student.id, "academic_year": academic_year, "gpa": float(gpa_value)})