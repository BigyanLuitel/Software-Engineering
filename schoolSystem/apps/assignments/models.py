from django.db import models
from django.conf import settings
from apps.academics.models import Class, Subject


class Assignment(models.Model):
    """
    An assignment posted by a Teacher to one specific Class, for one
    Subject. Visible read-only to Students in that class and to
    Admin for oversight -- no submission/grading workflow, per
    current scope (that's a possible future addition, not this one).
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="assignments")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments_posted",
        limit_choices_to={"role": "TEACHER"},
    )
    due_date = models.DateField()
    attachment = models.FileField(upload_to="assignment_attachments/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.class_obj}, due {self.due_date})"