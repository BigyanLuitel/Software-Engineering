from django.db import models
from apps.students.models import Student
from apps.academics.models import Examination, Subject
from apps.academics.models import Class


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
    has_practical = models.BooleanField(default=False, help_text="Does this subject have a separate practical component?")
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_full_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=50)
    practical_grade = models.CharField(max_length=2, blank=True, editable=False)
    class Meta:
        unique_together = ("student", "examination", "subject")
    
    def save(self, *args, **kwargs):
        from .services import _grade_for_percentage
        percentage = (self.marks_obtained / self.full_marks) * 100
        self.grade, self.grade_point = _grade_for_percentage(percentage)
        self.passed = percentage >= 40

        if self.has_practical and self.practical_marks is not None and self.practical_full_marks:
            pr_percentage = (self.practical_marks / self.practical_full_marks) * 100
            self.practical_grade, _ = _grade_for_percentage(pr_percentage)

        super().save(*args, **kwargs)
    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{self.student} \u2013 {self.subject}: {self.marks_obtained}/{self.full_marks} ({self.grade}, {status})"

# apps/results/models.py, new small model
class ConductRating(models.Model):
    """
    Non-academic ratings shown on the marksheet's summary panel.
    Kept separate from Result since these aren't subject-based --
    one row per student per examination, not per subject.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="conduct_ratings")
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name="conduct_ratings")
    hygiene = models.CharField(max_length=20, blank=True, help_text="e.g. Excellent, Good, Satisfactory")
    discipline = models.CharField(max_length=20, blank=True)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("student", "examination")

from apps.academics.models import Class


class ResultPublication(models.Model):
    """
    Marks one (examination, class) combination as published -- i.e.
    visible to students in that class. Results are entered per
    student/subject, but released as a whole class+exam unit, since
    a teacher finishes a whole class's marks together and admin
    reviews/releases them as one action, not subject-by-subject.

    Existence of a row = published. Deleting it = unpublished.
    """
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name="publications")
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="result_publications")
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("examination", "class_obj")