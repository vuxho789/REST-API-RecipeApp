"""
Views for the User API.
"""
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)
from drf_spectacular.utils import extend_schema_view, extend_schema


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create an authentication token for user."""
    serializer_class = AuthTokenSerializer

    # This is to enable a renderer, allowing the create token view
    # can be accessed using the browsable API.
    # The ObtainAuthToken class doesn't set a renderer by default.
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


@extend_schema_view(
    get=extend_schema(description="Retrieve the authenticated user."),
    put=extend_schema(
        description="Update information of the authenticated user."),
    patch=extend_schema(
        description="Partially update information of the authenticated user."),
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user
