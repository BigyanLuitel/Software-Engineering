from django.contrib import admin
from.models import Teacher
# Register your models here.
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
   list_display = ('user', 'subject', 'qualification', 'contact')
   search_fields = ('user__email', 'user__first_name', 'user__last_name', 'subject')