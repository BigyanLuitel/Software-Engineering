from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only Admin role can access. Used on endpoints like fee structure
    management, report generation -- things only an administrator does."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "TEACHER")


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "STUDENT")


class IsAdminOrTeacher(BasePermission):
    """For endpoints both roles can touch -- e.g. marking attendance,
    entering results -- but Students cannot."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ("ADMIN", "TEACHER"))