from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RoleAwareTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    """
    Single login endpoint for every role. There is no role selector
    on the frontend -- the same username/password form is used by
    Admin, Teacher, and Student alike, and the response tells the
    frontend where to send the user next.
    """
    serializer_class = RoleAwareTokenObtainPairSerializer