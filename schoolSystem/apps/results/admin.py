from django.contrib import admin
from .models import Result,ConductRating


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'subject', 'marks_obtained', 'full_marks', 'grade')
    list_filter = ('examination', 'subject')
    search_fields = ('student__user__email',)



@admin.register(ConductRating)
class ConductRatingAdmin(admin.ModelAdmin):
    list_display = ("student", "examination", "hygiene", "discipline", "attendance_percentage")