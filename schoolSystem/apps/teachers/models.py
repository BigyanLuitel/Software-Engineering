from django.db import models
from django.conf import settings
from apps.academics.models import Subject


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        help_text='The login account this Teacher profile is linked to.'
    )

    qualification = models.CharField(max_length=200, null=True, blank=True, help_text="The Teacher's academic qualification.")
    contact = models.CharField(max_length=15, null=True, blank=True, help_text="The Teacher's contact number.")
    subjects = models.ManyToManyField(
        Subject,
        blank=True,
        related_name="teachers",
        help_text="The subject(s) this Teacher teaches.",
    )

    def __str__(self):
        return f"{self.user.email} - {self.user.first_name} {self.user.last_name}"