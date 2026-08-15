from django.db import models
from django.conf import settings


class Teacher(models.Model):
    """Profile data for a Teacher, linked one-to-one to a User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        help_text='The login account this Teacher profile is linked to.'
    )

    qualification = models.CharField(max_length=200, null=True, blank=True, help_text="The Teacher's academic qualification.")
    contact = models.CharField(max_length=15, null=True, blank=True, help_text="The Teacher's contact number.")
    subject = models.CharField(max_length=100, null=True, blank=True, help_text="The subject the Teacher primarily teaches.")

    def __str__(self):
        return f"{self.user.email} - {self.user.first_name} {self.user.last_name}"