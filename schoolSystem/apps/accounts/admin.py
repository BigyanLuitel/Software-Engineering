from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    """
    Extends Django's default UserAdmin so 'role' actually shows up
    in the admin panel -- without this, the admin only knows about
    the default User fields and hides 'role' entirely.
    """
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')


admin.site.register(User, UserAdmin)