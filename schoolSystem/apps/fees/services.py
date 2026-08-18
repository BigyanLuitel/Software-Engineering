from datetime import date
from decimal import Decimal
from django.db import transaction
from apps.students.models import Student
from .models import FeeCategory, FeeStructure, FeeInvoice
from django.db.models import Sum


@transaction.atomic
def generate_monthly_invoices(month: str, due_date: date, academic_year: str):
    """
    Generates this month's FeeInvoice for every Student, for every
    RECURRING FeeCategory (Tuition, etc.) -- one-time categories
    (Admission) are never auto-generated here, they're created
    manually once when actually charged.

    Carries forward unpaid balance: if a student has an outstanding
    invoice from ANY prior month in the same category, that
    outstanding amount becomes this month's previous_due. This is
    what makes "previous dues roll into next month" actually happen,
    rather than being a manual step someone has to remember.
    """

    recurring_categories = FeeCategory.objects.filter(is_recurring=True)
    created = []

    for student in Student.objects.select_related("student_class"):
        if not student.student_class:
            continue  # can't bill a student with no class assigned -- no fee structure to look up

        for category in recurring_categories:
            structure = FeeStructure.objects.filter(
                class_obj=student.student_class,
                fee_category=category,
                academic_year=academic_year,
            ).first()

            if not structure:
                continue  # this class has no defined rate for this category -- skip rather than guess

            if FeeInvoice.objects.filter(student=student, fee_category=category, month=month).exists():
                continue  # already generated -- safe to re-run this function without creating duplicates

            previous_outstanding = _sum_prior_outstanding(student, category, before_month=month)

            invoice = FeeInvoice.objects.create(
                student=student,
                fee_category=category,
                month=month,
                amount_due=structure.amount,
                previous_due=previous_outstanding,
                due_date=due_date,
                status=FeeInvoice.Status.UNPAID,
            )
            created.append(invoice)

    return created


def _sum_prior_outstanding(student, category, before_month: str) -> Decimal:
    """
    Computes true outstanding balance as (total ever charged) minus
    (total ever paid), across all prior invoices in this category.

    This must NOT sum each prior invoice's .outstanding property --
    that value already includes THAT invoice's own previous_due,
    so chaining them across months double-counts old debt every
    time it gets carried forward again. Summing raw amount_due and
    amount_paid avoids any compounding, because each is only ever
    counted once, at its original source.
    """
    prior = FeeInvoice.objects.filter(
        student=student, fee_category=category, month__lt=before_month,
    )
    total_charged = prior.aggregate(t=Sum("amount_due"))["t"] or Decimal("0")
    total_paid = prior.aggregate(t=Sum("amount_paid"))["t"] or Decimal("0")

    return max(total_charged - total_paid, Decimal("0"))

@transaction.atomic
def record_payment(invoice: FeeInvoice, amount: Decimal):
    """
    Applies a payment to an invoice and updates status correctly,
    including partial payments. This is the ONLY function that
    should ever modify amount_paid directly -- keeps payment logic
    in one place rather than scattered across views.
    """

    if amount <= 0:
        raise ValueError("Payment amount must be positive.")

    invoice.amount_paid += amount

    if invoice.amount_paid >= invoice.total_due:
        invoice.status = FeeInvoice.Status.PAID
    elif invoice.amount_paid > 0:
        invoice.status = FeeInvoice.Status.PARTIALLY_PAID
    else:
        invoice.status = FeeInvoice.Status.UNPAID

    invoice.save()
    return invoice