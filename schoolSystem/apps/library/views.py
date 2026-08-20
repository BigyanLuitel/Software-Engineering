from datetime import date, datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher
from apps.students.models import Student
from .models import Book, Circulation
from .serializers import BookSerializer, CirculationSerializer
from .services import issue_book, return_book


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdmin()]
        return [IsAdminOrTeacher()]


class CirculationViewSet(viewsets.ModelViewSet):
    queryset = Circulation.objects.select_related("book", "student__user").all()
    serializer_class = CirculationSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=["post"], url_path="issue")
    def issue(self, request):
        """
        POST /api/library/circulations/issue/
        Body: {"book_id": 1, "student_id": 1}
        Wraps issue_book() -- surfaces its ValueError (no copies
        available) as a clean 400, not a raw 500.
        """
        try:
            book = Book.objects.get(id=request.data.get("book_id"))
            student = Student.objects.get(id=request.data.get("student_id"))
        except (Book.DoesNotExist, Student.DoesNotExist):
            return Response({"detail": "Book or Student not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            circulation = issue_book(book, student)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(CirculationSerializer(circulation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="return")
    def return_book_action(self, request, pk=None):
        """
        POST /api/library/circulations/{id}/return/
        detail=True: this DOES act on one specific existing
        circulation record (identified by the URL), same pattern
        as Fees' pay action.
        """
        circulation = self.get_object()

        try:
            updated = return_book(circulation)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(CirculationSerializer(updated).data, status=status.HTTP_200_OK)