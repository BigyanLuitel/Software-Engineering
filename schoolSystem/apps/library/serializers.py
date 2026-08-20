from rest_framework import serializers
from .models import Book, Circulation


class BookSerializer(serializers.ModelSerializer):
    available_copies = serializers.IntegerField(read_only=True)

    class Meta:
        model = Book
        fields = ["id", "title", "author", "isbn", "total_copies", "available_copies"]


class CirculationSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    student_email = serializers.EmailField(source="student.user.email", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Circulation
        fields = [
            "id", "book", "book_title", "student", "student_email",
            "issue_date", "due_date", "return_date", "is_overdue",
        ]
        read_only_fields = ["due_date"]  # calculated by issue_book(), not client-supplied