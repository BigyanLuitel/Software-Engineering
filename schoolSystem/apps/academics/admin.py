from django.contrib import admin
from .models import Class, Subject, ClassSubject, Examination


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'section', 'teacher')
    search_fields = ('class_name', 'section')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'subject_name')
    search_fields = ('subject_name', 'subject_code')


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'subject')
    list_filter = ('class_obj', 'subject')


@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ('term', 'academic_year', 'is_final')
    list_filter = ('academic_year', 'is_final')