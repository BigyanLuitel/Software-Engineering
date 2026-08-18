from django.contrib import admin
from .models import FeeCategory, FeeStructure, FeeInvoice


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_recurring')


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('class_obj', 'fee_category', 'amount', 'academic_year')
    list_filter = ('academic_year', 'fee_category')


@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_category', 'month', 'amount_due', 'previous_due', 'amount_paid', 'status')
    list_filter = ('status', 'month', 'fee_category')
    search_fields = ('student__user__email',)