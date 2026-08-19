from rest_framework import viewsets, permissions
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from .models import Student
from .serializers import StudentSerializer


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
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]