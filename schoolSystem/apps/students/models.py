from django.db import models
from django.conf import settings
from apps.academics.models import Class
# Create your models here.
class Student(models.Model):
    """Profile data for a Student, linked one-to-one to a User.

    Why one-to-one and not just fields on User: a Student's data
    (class, parent contact, photo) has no meaning for a Teacher or
    Admin login. Keeping it separate means User stays a pure auth
    model, and Student can evolve (add fields, add relations to
    Attendance/Result/Fee later) without touching auth at all.
    """
    user = models.OneToOneField(
settings.AUTH_USER_MODEL, 
on_delete=models.CASCADE,
related_name='student_profile',
help_text='The Login account this Student profile is linked to.'
    )
    student_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text='The class/grade this Student is enrolled in.'
    )
    
    date_of_birth = models.DateField(null=True, blank=True, help_text='The Student\'s date of birth.')
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], null=True, blank=True, help_text='The Student\'s gender.')
    parent_name = models.CharField(max_length=100, null=True, blank=True, help_text='The name of the Student\'s parent or guardian.')
    roll_number = models.CharField(max_length=20, blank=True, help_text="Class roll number, e.g. '14'")
    parent_contact = models.CharField(max_length=15, null=True, blank=True, help_text='The contact number of the Student\'s parent or guardian.')
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True, help_text="The Student's photo, uploaded from device.")
    
    def __str__(self):
        return f"{self.user.email} - {self.user.first_name} {self.user.last_name}"
