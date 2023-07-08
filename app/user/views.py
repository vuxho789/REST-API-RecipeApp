"""
Views for the User API.
"""
from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
)


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
