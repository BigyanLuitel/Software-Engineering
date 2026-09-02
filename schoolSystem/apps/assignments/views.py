from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher, IsStudent, IsTeacher
from apps.students.models import Student
from .models import Assignment
from .serializers import AssignmentSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related("class_obj", "subject", "teacher").all()
    serializer_class = AssignmentSerializer

    def get_permissions(self):
        if self.action == "me":
            return [IsStudent()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsTeacher()]
        return [IsAdminOrTeacher()]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    def get_queryset(self):
        """
        A teacher only sees/manages their OWN posted assignments in
        the general list/CRUD endpoints -- not every teacher's.
        Admin still sees everything via this same endpoint since
        IsAdminOrTeacher covers both roles here.
        """
        queryset = super().get_queryset()
        if self.request.user.role == "TEACHER":
            return queryset.filter(teacher=self.request.user)
        return queryset

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """GET /api/assignments/me/ -- assignments for the student's own class."""
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"detail": "No student profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        if not student.student_class:
            return Response([])

        assignments = Assignment.objects.filter(class_obj=student.student_class).select_related("subject", "teacher")
        return Response(AssignmentSerializer(assignments, many=True).data)