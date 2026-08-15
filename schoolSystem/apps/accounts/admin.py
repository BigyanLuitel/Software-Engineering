from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "role", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser"),
        }),
    )
    search_fields = ("email",)


admin.site.register(User, UserAdmin)