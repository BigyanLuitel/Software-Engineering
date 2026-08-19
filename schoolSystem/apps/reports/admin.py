# apps/reports/admin.py
from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'class_obj', 'generated_by', 'generated_at')
    list_filter = ('report_type', 'generated_at')

