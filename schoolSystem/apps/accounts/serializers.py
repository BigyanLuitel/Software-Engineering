from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RoleAwareTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Standard JWT login, extended to carry the user's role.

    Why this exists: the frontend needs to know WHICH dashboard to
    redirect to immediately after login, without a second API call.
    Putting 'role' both in the token claims (so every future request
    can be permission-checked without a DB lookup) and directly in
    the login response body (so the frontend can redirect instantly)
    covers both needs with one extra field.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role  # embedded in the JWT itself
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role  # also returned directly in the login response
        data['username'] = self.user.email  # also returned directly in the login response
        return data