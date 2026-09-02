from django.contrib.admin import action
from httpx import Response
from rest_framework import viewsets, permissions
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from .models import Student
from .serializers import StudentSerializer
from django.http import HttpResponse, request, response
from apps.academics.models import Class
from .services import generate_id_cards
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher, IsStudent


class StudentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Student records.
    - Admin: full access (create/update/delete/list/retrieve)
    - Teacher: read-only (list/retrieve), needed for their class rosters
    - Student: NOT given access here -- a student viewing their OWN
      profile is a different, narrower endpoint we'll build separately,
      not this general-purpose admin/teacher management API.
    """
    queryset = Student.objects.select_related("user", "student_class").all()
    serializer_class = StudentSerializer


    def get_permissions(self):
        if self.action == "me":
            return [IsStudent()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """GET /api/students/me/ -- the logged-in student's own profile."""
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"detail": "No student profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        return Response(StudentSerializer(student, context={"request": request}).data)
    @action(detail=False, methods=["get"], url_path="id-cards")
    def id_cards(self, request):
        """
    GET /api/students/id-cards/?class_id=1&academic_year=2025-2026
    Returns a PDF file directly, not JSON.
        """
        try:
            class_obj = Class.objects.get(id=request.query_params.get("class_id"))
        except Class.DoesNotExist:
            return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)

        academic_year = request.query_params.get("academic_year", "")
        pdf_bytes = generate_id_cards(class_obj, academic_year)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="id_cards_{class_obj}_{academic_year}.pdf"'
        return response