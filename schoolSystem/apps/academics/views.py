from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from .models import Class, Subject, ClassSubject, Examination
from .serializers import ClassSerializer, SubjectSerializer, ClassSubjectSerializer, ExaminationSerializer
from apps.accounts.permissions import IsStudent
from apps.students.models import Student
from .models import ClassSubject

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.select_related("teacher").all()
    serializer_class = ClassSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def get_permissions(self):
        if self.action == "my_subjects":
            return [IsStudent()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]

    @action(detail=False, methods=["get"], url_path="my-subjects")
    def my_subjects(self, request):
        """
        GET /api/academics/subjects/my-subjects/
        Only the subjects actually offered for the logged-in
        student's own class -- via the ClassSubject bridge table --
        not every subject in the whole school.
        """
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"detail": "No student profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        if not student.student_class:
            return Response([])

        class_subjects = ClassSubject.objects.filter(class_obj=student.student_class).select_related("subject")
        subjects = [cs.subject for cs in class_subjects]
        return Response(SubjectSerializer(subjects, many=True).data)


class ClassSubjectViewSet(viewsets.ModelViewSet):
    queryset = ClassSubject.objects.select_related("class_obj", "subject").all()
    serializer_class = ClassSubjectSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]


class ExaminationViewSet(viewsets.ModelViewSet):
    queryset = Examination.objects.all()
    serializer_class = ExaminationSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]