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
    grade = models.CharField(max_length=2, blank=True)

    class Meta:
        unique_together = ("student", "examination", "subject")

    def __str__(self):
        return f"{self.student} \u2013 {self.examination} \u2013 {self.subject}: {self.marks_obtained}/{self.full_marks}"