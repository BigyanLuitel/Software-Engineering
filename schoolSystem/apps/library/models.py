from django.db import models
from apps.students.models import Student


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150)
    isbn = models.CharField(max_length=20, unique=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def available_copies(self):
        """
        Copies currently NOT checked out. Computed, not stored --
        storing this separately would risk it drifting out of sync
        with actual Circulation records every time a book is
        issued/returned. Always derive it from the source of truth.
        """
        checked_out = self.circulations.filter(return_date__isnull=True).count()
        return max(self.total_copies - checked_out, 0)


class Circulation(models.Model):
    """
    One borrow transaction. return_date=None means the book is
    currently checked out; a real date means it's been returned.
    This is the bridge entity resolving Student<->Book, same pattern
    as ClassSubject for Class<->Subject.
    """

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="circulations")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="circulations")
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        status = "Returned" if self.return_date else "Checked Out"
        return f"{self.book} \u2013 {self.student} ({status})"

    @property
    def is_overdue(self):
        from datetime import date
        if self.return_date:
            return False  # already returned, can't be overdue
        return date.today() > self.due_date