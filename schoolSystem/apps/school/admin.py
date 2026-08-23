from django.contrib import admin
from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("school_name", "contact_email", "established_year", "school_contact_number", "school_quote")