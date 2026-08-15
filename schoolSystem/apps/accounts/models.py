from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for TVSBS.

    Why not Django's default User: the default has no concept of
    'role', and we need every login (Admin, Teacher, Student) to
    carry one so the frontend knows which dashboard to route to and
    DRF permissions can gate endpoints by role.

    Why not three separate password fields (one per Student/Teacher/
    Admin), matching the ERD literally: Django's auth system (login,
    JWT, permissions) is built around exactly one User model. Splitting
    auth three ways means reimplementing login/permissions three times
    for no real benefit. Student and Teacher become PROFILE models
    (next piece) linked to this User via a one-to-one field, holding
    only their domain-specific attributes (class assigned, subject,
    etc.) -- not auth fields.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        help_text="Determines which dashboard and permissions this user gets.",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"