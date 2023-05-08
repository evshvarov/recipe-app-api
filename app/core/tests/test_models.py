"""
Tests for models in core app
"""
from decimal import Decimal


from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

def create_user(email='user@example.com', password='testpass'):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(email, password)

class ModelTests(TestCase):
    """Test Models"""
    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='testpass123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'testpass123')

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@example.com','testpass123')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'testpass123')


    def test_create_recipe(self):
        """Test creating a new recipe is successful"""
        user=get_user_model().objects.create_user(
                'test@example.com',
                'testpass123'
            )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=Decimal('5.50'),
        )

        self.assertEqual(str(recipe),recipe.title)

    def test_create_tag(self):
        """Test creating a new tag is successful"""
        user=create_user()
        tag=models.Tag.objects.create(user=user, name='Vegan')
        self.assertEqual(str(tag), tag.name)


    def test_create_ingredient(self):
        """Test creating a new ingredient is successful"""
        user=create_user()
        ingredient=models.Ingredient.objects.create(user=user, name='Cucumber')
        self.assertEqual(str(ingredient), ingredient.name)

