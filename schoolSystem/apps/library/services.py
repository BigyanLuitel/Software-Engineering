from datetime import date, timedelta
from django.db import transaction
from .models import Book, Circulation


LOAN_PERIOD_DAYS = 14


@transaction.atomic
def issue_book(book: Book, student, issue_date: date = None):
    """
    Issues a book to a student. Refuses if no copies are available --
    this is the actual business rule enforcement point; without this
    check here, nothing stops issuing a book that's already fully
    checked out.
    """
    issue_date = issue_date or date.today()

    if book.available_copies <= 0:
        raise ValueError(f"No available copies of '{book.title}' to issue.")

    return Circulation.objects.create(
        book=book,
        student=student,
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=LOAN_PERIOD_DAYS),
    )


@transaction.atomic
def return_book(circulation: Circulation, return_date: date = None):
    """
    Marks a circulation record as returned. Refuses to "return" an
    already-returned record -- prevents accidentally resetting the
    return_date on a transaction that's already closed.
    """
    if circulation.return_date is not None:
        raise ValueError("This book has already been returned.")

    circulation.return_date = return_date or date.today()
    circulation.save()
    return circulation