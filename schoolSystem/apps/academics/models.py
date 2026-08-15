from django.db import models
from django.conf import settings

# Create your models here.
class Class(models.Model):
    """
    A class/grade (e.g., "Grade 5", Section "A").
    """

    class_name = models.CharField(max_length=50, help_text='e.g. "Grade 5", "Nursery"')
    section = models.CharField(max_length=10, blank=True, help_text='e.g. "A", "B"')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_taught",
        limit_choices_to={"role": "TEACHER"},
        help_text="The class (homeroom) teacher, if assigned.",
    )

    class Meta:
        unique_together = ("class_name", "section")

    def __str__(self):
        return f"{self.class_name} {self.section}".strip()


class Subject(models.Model):
    """
    A subject (e.g., "Mathematics"). Exists once, reused across
    every class that offers it -- see ClassSubject below.
    """

    subject_name = models.CharField(max_length=100, unique=True)
    subject_code = models.CharField(
        max_length=10,
        unique=True,
        help_text='Short code for quick reference, e.g. "MATH", "ENG", "SCI"',
    )

    def __str__(self):
        return f"{self.subject_code} \u2013 {self.subject_name}"

class ClassSubject(models.Model):
    """
    Bridge entity resolving the many-to-many relationship between
    Class and Subject. A row here means "this Subject is offered
    for this Class" -- e.g. (Grade 5, Mathematics).

    This is what lets the AI Question Paper Generator (and the
    Teacher UI in general) validate that a selected subject is
    actually valid for a selected class, instead of allowing any
    class+subject combination regardless of whether it makes sense.
    """

    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="classes")

    class Meta:
        unique_together = ("class_obj", "subject")
        verbose_name = "Class-Subject Mapping"
        verbose_name_plural = "Class-Subject Mappings"
    
    def __str__(self):
        return f"{self.class_obj} \u2013 {self.subject}"