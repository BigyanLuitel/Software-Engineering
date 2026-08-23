from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager because Django's default user creation assumes a
    username. Since we're using email as the login identifier instead,
    create_user/create_superuser need to be told explicitly how to
    build a user from an email + password instead.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hashes the password, never stored plain
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")  # superusers are always Admins here

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model, email-based login (no username field at all).

    AbstractBaseUser gives us: password (hashed), last_login.
    PermissionsMixin gives us: is_superuser, groups, user_permissions,
    and everything Django admin needs for permission checks.
    We add: email (the actual login identifier), first_name,
    last_name, role, is_active, is_staff -- fields AbstractUser would
    have given us for free, but which AbstractBaseUser does not.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # required for Django admin access

    objects = UserManager()

    USERNAME_FIELD = "email"   # <-- this is the actual switch: email is now the login identifier
    REQUIRED_FIELDS = []       # extra fields prompted for on `createsuperuser`, beyond email+password

    def __str__(self):
        return f"{self.email} ({self.role})"