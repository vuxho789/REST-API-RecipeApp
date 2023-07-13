"""
Tests for Recipe APIs.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


# The param for the reverse() function is constructed as follows:
# reverse('<app_name>:<queryset_model_in_lowercase>-<action>')
RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {'title': 'Sample Recipe Title',
                'time_minutes': 22,
                'price': Decimal('5.25'),
                'description': 'Sample description',
                'link': 'http://example.com/recipe.pdf'}

    # This to allow overiding default values if required
    defaults.update(params)

    recipe = Recipe.objects.create(created_by=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com',
                                password='testpass123',)
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test list of recipes limited to an authenticated user."""
        other_user = create_user(email='other@example.com',
                                 password='otherpass123',)
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(created_by=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipe_details(self):
        """Test retrieving details of a recipe."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a new recipe."""
        payload = {'title': 'Sample Recipe Title',
                   'time_minutes': 30,
                   'price': Decimal('5.99')}
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.created_by, self.user)

    def test_partial_update_recipe(self):
        """Test partial update of a recipe."""
        original_link = 'https://example.comn/recipe.pdf'
        recipe = create_recipe(user=self.user,
                               title='Original Recipe Title',
                               link=original_link,)
        payload = {'title': 'New Recipe Title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.created_by, self.user)

    def test_full_update_recipe(self):
        """Test full update of a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {'title': 'New Recipe Title',
                   'time_minutes': 10,
                   'price': Decimal('2.50'),
                   'description': 'New recipe description',
                   'link': 'https://example.com/new-recipe.pdf'}
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.created_by, self.user)

    def test_reassign_recipe_user_error(self):
        """Test user unable to change the original recipe's user."""
        new_user = create_user(email='new_user@example.com',
                               password='testpass123',)
        recipe = create_recipe(user=self.user)

        # Note that the created_by is not defined in the serializer
        # thus it will be ignored even though the response is still 200
        payload = {'created_by': new_user}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.created_by, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe succesful."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """
        Test error is returned when trying to delete another user's recipe.
        """
        new_user = create_user(email='new_user@example.com',
                               password='testpass123')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {'title': 'Thai Prawn Curry',
                   'time_minutes': 30,
                   'price': Decimal('5.50'),
                   'tags': [{'name': 'Thai'},
                            {'name': 'Seafood'},
                            {'name': 'Spicy'}]}
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(created_by=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 3)

        for tag in payload['tags']:
            self.assertTrue(recipes[0].tags.filter(
                name=tag['name'],
                created_by=self.user
            ).exists())

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""
        existing_tag = Tag.objects.create(created_by=self.user,
                                          name='Indian')
        payload = {'title': 'Butter Chicken',
                   'time_minutes': 60,
                   'price': Decimal('7.50'),
                   'tags': [{'name': 'Indian'},
                            {'name': 'Lunch'}]}
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(created_by=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), 2)
        self.assertIn(existing_tag, recipes[0].tags.all())

        for tag in payload['tags']:
            self.assertTrue(recipes[0].tags.filter(
                name=tag['name'],
                created_by=self.user
            ).exists())

    def test_create_tag_on_update_recipe(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Picnic'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(created_by=self.user, name='Picnic')
        self.assertIn(new_tag, recipe.tags.all())

    def test_assign_tag_on_update_recipe(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_1 = Tag.objects.create(created_by=self.user,
                                   name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_1)

        tag_2 = Tag.objects.create(created_by=self.user,
                                   name='Lunch')

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_2, recipe.tags.all())
        self.assertNotIn(tag_1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing all tags of a recipe."""
        tag = Tag.objects.create(created_by=self.user,
                                 name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {'title': 'Prawn Tacos',
                   'time_minutes': 60,
                   'price': Decimal('9.50'),
                   'ingredients': [{'name': 'Prawns'},
                                   {'name': 'Taco shells'},
                                   {'name': 'Seasonings'}]}
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(created_by=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].ingredients.count(), 3)

        for ingredient in payload['ingredients']:
            self.assertTrue(recipes[0].ingredients.filter(
                name=ingredient['name'],
                created_by=self.user
            ).exists())

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients."""
        existing_ingredient = Ingredient.objects.create(
            created_by=self.user,
            name='Lemons'
        )
        payload = {'title': 'Lemonade',
                   'time_minutes': 15,
                   'price': Decimal('1.50'),
                   'ingredients': [{'name': 'Lemons'},
                                   {'name': 'Sugar'}]}
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(created_by=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].ingredients.count(), 2)
        self.assertIn(existing_ingredient, recipes[0].ingredients.all())

        for ingredient in payload['ingredients']:
            self.assertTrue(recipes[0].ingredients.filter(
                name=ingredient['name'],
                created_by=self.user
            ).exists())

    def test_create_ingredient_on_update_recipe(self):
        """Test creating ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Limes'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(created_by=self.user,
                                                name='Limes')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_assign_ingredient_on_update_recipe(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ingredient_1 = Ingredient.objects.create(created_by=self.user,
                                                 name='Limes')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_1)

        ingredient_2 = Ingredient.objects.create(created_by=self.user,
                                                 name='Chillies')

        payload = {'ingredients': [{'name': 'Chillies'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_2, recipe.ingredients.all())
        self.assertNotIn(ingredient_1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing all ingredients of a recipe."""
        ingredient = Ingredient.objects.create(created_by=self.user,
                                               name='Apples')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
