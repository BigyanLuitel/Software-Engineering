from django.db import models
from apps.students.models import Student
from apps.academics.models import Class


class FeeCategory(models.Model):
    """
    A billable topic -- Tuition, Transport, Exam Fee, Library Fee, etc.
    is_recurring distinguishes monthly charges (Tuition) from
    one-time charges (Admission Fee), which affects how invoices
    get generated (see services.py).
    """

    name = models.CharField(max_length=100, unique=True)
    is_recurring = models.BooleanField(
        default=True,
        help_text="True for monthly charges (Tuition). False for one-time charges (Admission).",
    )

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    """
    The rate for a given FeeCategory, per Class, per academic year.
    Same bridge-entity pattern as ClassSubject -- fee amounts vary by
    class, so this can't be a flat amount on FeeCategory alone.
    """

    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="fee_structures")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name="structures")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    academic_year = models.CharField(max_length=9)

    class Meta:
        unique_together = ("class_obj", "fee_category", "academic_year")

    def __str__(self):
        return f"{self.class_obj} \u2013 {self.fee_category}: {self.amount} ({self.academic_year})"


class FeeInvoice(models.Model):
    """
    One student's bill for one fee category, for one month.
    previous_due carries forward any unpaid balance from prior
    invoices in the SAME category -- generated automatically by
    services.generate_monthly_invoices(), never entered by hand.
    """

    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_invoices")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name="invoices")
    month = models.CharField(max_length=7, help_text='e.g. "2026-01"')

    amount_due = models.DecimalField(max_digits=10, decimal_places=2, help_text="This month's charge only.")
    previous_due = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Unpaid balance carried forward from prior months.")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)

    class Meta:
        unique_together = ("student", "fee_category", "month")

    @property
    def total_due(self):
        return self.amount_due + self.previous_due

    @property
    def outstanding(self):
        return self.total_due - self.amount_paid

    def __str__(self):
        return f"{self.student} \u2013 {self.fee_category} \u2013 {self.month}: {self.outstanding} outstanding"