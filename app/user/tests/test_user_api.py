"""
Tests for the User API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


REGISTER_USER_URL = reverse('user:register')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserTests(TestCase):
    """Test the public features of the User API"""

    def setUp(self):
        self.client = APIClient()

    def test_register_new_user_success(self):
        """Test new user registration successful"""
        payload = {'email': 'user@example.com',
                   'password': 'testpass123',
                   'name': 'Test Name'}
        res = self.client.post(REGISTER_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Check if user is added to the database and
        # the hashed password is not included in the response
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_existing_email_error(self):
        """
        Test an error is returned when user registers with an existing email.
        """
        payload = {'email': 'user@example.com',
                   'password': 'testpass123',
                   'name': 'Test Name'}
        create_user(**payload)
        res = self.client.post(REGISTER_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned when password is less than 5 chars."""
        payload = {'email': 'user@example.com',
                   'password': 'pw',
                   'name': 'Test Name'}
        res = self.client.post(REGISTER_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Check to ensure user is not added to the database
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test token generated for valid credentials."""
        user_details = {'name': 'Test Name',
                        'email': 'user@example.com',
                        'password': 'test-password-123'}
        create_user(**user_details)

        payload = {'email': user_details['email'],
                   'password': user_details['password']}
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials_error(self):
        """Test an error is returned when redentials is invalid."""
        create_user(email='user@example.com',
                    password='goodpass')
        payload = {'email': 'user@example.com',
                   'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test an error is returned when receiving a blank password."""
        payload = {'email': 'user@example.com',
                   'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(email='user@example.com',
                                password='testpass123',
                                name='Test Name',)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {'name': self.user.name,
                                    'email': self.user.email})

    def test_post_me_not_allowed(self):
        """Test POST method is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for logged in user."""
        payload = {'name': 'Updated Name',
                   'password': 'NewPass123'}
        res = self.client.patch(ME_URL, payload)

        # To get updated values for the user object
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
