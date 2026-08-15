from django.contrib import admin
from .models import Student
# Register your models here.
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'gender', 'parent_name', 'parent_contact', 'photo')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'parent_name', 'parent_contact')
    