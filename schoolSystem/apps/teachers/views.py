from rest_framework import viewsets, permissions
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from .models import  Teacher
from .serializers import  TeacherSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Teacher records.
    - Admin: full access (create/update/delete/list/retrieve)
    - Teacher: read-only (list/retrieve), needed for their class rosters
    - Student: NOT given access here -- a student viewing their OWN
      profile is a different, narrower endpoint we'll build separately,
      not this general-purpose admin/teacher management API.
    """
    queryset = Teacher.objects.select_related("user").all()
    serializer_class = TeacherSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]