"""
Views for Recipe APIs.
"""
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Recipe, Tag, Ingredient
from recipe import serializers
from drf_spectacular.utils import extend_schema_view, extend_schema


@extend_schema_view(
    list=extend_schema(description="Retrieve a list of recipes."),
    create=extend_schema(description="Create a new recipe."),
    retrieve=extend_schema(description="Retrieve a recipe by `ID`."),
    update=extend_schema(description="Update a recipe by `ID`."),
    partial_update=extend_schema(
        description="Partially update a recipe by `ID`."),
    destroy=extend_schema(description="Delete a recipe by `ID`."),
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for an authenticated user."""
        return self.queryset.filter(
            created_by=self.request.user
        ).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save(created_by=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to the recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for Recipe Attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipe's attributes for an authenticated user."""
        return self.queryset.filter(
            created_by=self.request.user
        ).order_by('-name')


@extend_schema_view(
    list=extend_schema(description="Retrieve a list of tags."),
    update=extend_schema(description="Update a tag by `ID`."),
    partial_update=extend_schema(
        description="Partially update a tag by `ID`."),
    destroy=extend_schema(description="Delete a tag by `ID`."),
)
class TagViewSet(BaseRecipeAttrViewSet):
    """View for manage tags APIs."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


@extend_schema_view(
    list=extend_schema(description="Retrieve a list of ingredients."),
    update=extend_schema(description="Update an ingredient by `ID`."),
    partial_update=extend_schema(
        description="Partially update an ingredient by `ID`."),
    destroy=extend_schema(description="Delete an ingredient by `ID`."),
)
class IngredientViewSet(BaseRecipeAttrViewSet):
    """View for manage ingedients APIs."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
