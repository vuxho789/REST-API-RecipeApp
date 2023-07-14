"""
Tests for Ingredient APIs.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer
from decimal import Decimal


# The param for the reverse() function is constructed as follows:
# reverse('<app_name>:<queryset_model_in_lowercase>-<action>')
INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicTagApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required to call API."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com',
                                password='testpass123',)
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(created_by=self.user, name='Kale')
        Ingredient.objects.create(created_by=self.user, name='Vanilla')

        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to an authenticated user."""
        other_user = create_user(email='other@example.com',
                                 password='otherpass123')
        Ingredient.objects.create(created_by=other_user, name='Salt')

        ingredient = Ingredient.objects.create(
            created_by=self.user,
            name='Pepper'
        )
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(created_by=self.user,
                                               name='Orange')
        payload = {'name': 'Grape Fruit'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(created_by=self.user,
                                               name='Lettuce')
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(created_by=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingedients by those assigned to recipes."""
        ingredient_1 = Ingredient.objects.create(created_by=self.user,
                                                 name='Apples')
        ingredient_2 = Ingredient.objects.create(created_by=self.user,
                                                 name='Turkey')
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            created_by=self.user,
        )
        recipe.ingredients.add(ingredient_1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serialized_data_1 = IngredientSerializer(ingredient_1)
        serialized_data_2 = IngredientSerializer(ingredient_2)
        self.assertIn(serialized_data_1.data, res.data)
        self.assertNotIn(serialized_data_2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """
        Test filtering assigned ingredients returns a unique list.
        """
        ingredient = Ingredient.objects.create(created_by=self.user,
                                               name='Eggs')
        Ingredient.objects.create(created_by=self.user,
                                  name='Lentils')
        recipe_1 = Recipe.objects.create(
            title='Eggs Benedict',
            time_minutes=60,
            price=Decimal('7.00'),
            created_by=self.user,
        )
        recipe_2 = Recipe.objects.create(
            title='Herb Eggs',
            time_minutes=20,
            price=Decimal('4.00'),
            created_by=self.user,
        )

        recipe_1.ingredients.add(ingredient)
        recipe_2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
