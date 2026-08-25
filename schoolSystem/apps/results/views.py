from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from apps.students.models import Student
from .models import Result
from .serializers import ResultSerializer
from .services import compute_final_result, compute_gpa, generate_admit_cards, generate_marksheets
from django.http import HttpResponse, request, response
from apps.academics.models import Class, Examination
from .services import generate_marksheets

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.select_related("student__user", "subject", "examination").all()
    serializer_class = ResultSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrTeacher()]
        return [IsAdminOrTeacher()]

    @action(detail=False, methods=["get"], url_path="admit-cards")
    def admit_cards(self, request):
        """
        GET /api/results/admit-cards/?examination_id=1&class_id=1
        Returns a PDF file directly, not JSON.
        """
        try:
            examination = Examination.objects.get(id=request.query_params.get("examination_id"))
            class_obj = Class.objects.get(id=request.query_params.get("class_id"))
        except (Examination.DoesNotExist, Class.DoesNotExist):
            return Response({"detail": "Examination or Class not found."}, status=status.HTTP_404_NOT_FOUND)

        pdf_bytes = generate_admit_cards(examination, class_obj)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="admit_cards_{class_obj}_{examination}.pdf"'
        return response

    @action(detail=False, methods=["post"], url_path="compute-final")
    def compute_final(self, request):
        """
        POST /api/results/compute-final/
        Body: {"student_id": 1, "academic_year": "2025-2026"}
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
    
    # add this method inside your existing ResultViewSet class, alongside admit_cards
    @action(detail=False, methods=["get"], url_path="marksheets")
    def marksheets(self, request):
        """
        GET /api/results/marksheets/?examination_id=1&class_id=1&academic_year=2025-2026
        Returns a PDF file directly, not JSON.
        """
        try:
            examination = Examination.objects.get(id=request.query_params.get("examination_id"))
            class_obj = Class.objects.get(id=request.query_params.get("class_id"))
        except (Examination.DoesNotExist, Class.DoesNotExist):
            return Response({"detail": "Examination or Class not found."}, status=status.HTTP_404_NOT_FOUND)

        academic_year = request.query_params.get("academic_year", "")
        pdf_bytes = generate_marksheets(class_obj, examination, academic_year)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="marksheets_{class_obj}_{examination}.pdf"'
        return response