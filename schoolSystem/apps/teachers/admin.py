from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_subjects', 'qualification', 'contact')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'subjects__subject_name')

    def get_subjects(self, obj):
        return ", ".join(s.subject_name for s in obj.subjects.all())
    get_subjects.short_description = "Subjects"