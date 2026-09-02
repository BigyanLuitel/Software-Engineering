from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher, IsStudent
from apps.students.models import Student
from .models import Result, ResultPublication
from .serializers import ResultSerializer
from .services import compute_final_result, compute_gpa, generate_admit_cards, generate_marksheets
from django.http import HttpResponse
from apps.academics.models import Class, Examination


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.select_related("student__user", "subject", "examination").all()
    serializer_class = ResultSerializer

    def get_permissions(self):
        if self.action == "me":
            return [IsStudent()]
        if self.action in ["publish", "unpublish", "publication_status"]:
            return [IsAdmin()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminOrTeacher()]
        return [IsAdminOrTeacher()]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """
        GET /api/results/me/
        A student's own results, but ONLY for examinations that have
        been published for their class -- never another student's,
        and never an unpublished exam's marks.
        """
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"detail": "No student profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        published_exam_ids = ResultPublication.objects.filter(
            class_obj=student.student_class
        ).values_list("examination_id", flat=True)

        results = Result.objects.filter(
            student=student, examination_id__in=published_exam_ids
        ).select_related("subject", "examination")
        return Response(ResultSerializer(results, many=True).data)

    @action(detail=False, methods=["get"], url_path="publication-status")
    def publication_status(self, request):
        """GET /api/results/publication-status/?examination_id=1&class_id=1"""
        is_published = ResultPublication.objects.filter(
            examination_id=request.query_params.get("examination_id"),
            class_obj_id=request.query_params.get("class_id"),
        ).exists()
        return Response({"published": is_published})

    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, request):
        """POST /api/results/publish/ -- body: {"examination_id": 1, "class_id": 1}"""
        try:
            examination = Examination.objects.get(id=request.data.get("examination_id"))
            class_obj = Class.objects.get(id=request.data.get("class_id"))
        except (Examination.DoesNotExist, Class.DoesNotExist):
            return Response({"detail": "Examination or Class not found."}, status=status.HTTP_404_NOT_FOUND)

        ResultPublication.objects.get_or_create(examination=examination, class_obj=class_obj)
        return Response({"published": True})

    @action(detail=False, methods=["post"], url_path="unpublish")
    def unpublish(self, request):
        """POST /api/results/unpublish/ -- body: {"examination_id": 1, "class_id": 1}"""
        ResultPublication.objects.filter(
            examination_id=request.data.get("examination_id"),
            class_obj_id=request.data.get("class_id"),
        ).delete()
        return Response({"published": False})

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