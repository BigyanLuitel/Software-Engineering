from django.contrib import admin
from .models import Book, Circulation


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'total_copies', 'available_copies')
    search_fields = ('title', 'author', 'isbn')


@admin.register(Circulation)
class CirculationAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'issue_date', 'due_date', 'return_date', 'is_overdue')
    list_filter = ('return_date',)
    search_fields = ('book__title', 'student__user__email')