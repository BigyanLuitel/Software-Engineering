from rest_framework import viewsets
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from .models import Class, Subject, ClassSubject, Examination
from .serializers import ClassSerializer, SubjectSerializer, ClassSubjectSerializer, ExaminationSerializer


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
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]


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