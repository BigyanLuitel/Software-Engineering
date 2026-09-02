from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher, IsTeacher
from .models import Teacher
from .serializers import TeacherSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.select_related("user").all()
    serializer_class = TeacherSerializer

    def get_permissions(self):
        if self.action == "me":
            return [IsTeacher()]
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """GET /api/teachers/me/ -- the logged-in teacher's own profile."""
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            return Response({"detail": "No teacher profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        return Response(TeacherSerializer(teacher, context={"request": request}).data)