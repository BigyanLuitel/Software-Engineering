from django.db import models
from apps.students.models import Student
from apps.academics.models import Examination, Subject


class Result(models.Model):
    """
    One student's marks in one subject, for one examination (a real
    term OR the computed Final). Final rows are written by
    services.compute_final_result() -- never entered directly through
    a normal data-entry form.
    """

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results")

    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    full_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    # These three are ALWAYS derived from marks_obtained/full_marks in
    # save() below -- never entered manually. Kept as real DB columns
    # (rather than computed only on read) so they're fast to query/
    # filter/report on without recalculating every time.
    grade = models.CharField(max_length=2, blank=True, editable=False)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=0, editable=False)
    passed = models.BooleanField(default=True, editable=False)

    class Meta:
        unique_together = ("student", "examination", "subject")

    def save(self, *args, **kwargs):
        from .services import _grade_for_percentage  # avoids a circular import at module load time
        percentage = (self.marks_obtained / self.full_marks) * 100
        self.grade, self.grade_point = _grade_for_percentage(percentage)
        self.passed = percentage >= 40
        super().save(*args, **kwargs)

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{self.student} \u2013 {self.subject}: {self.marks_obtained}/{self.full_marks} ({self.grade}, {status})"