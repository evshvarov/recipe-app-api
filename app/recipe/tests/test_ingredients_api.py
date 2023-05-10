"""
tests for the ingredients api
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status # HTTP status codes
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

# URL for the ingredient list
INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    """Return ingredient detail URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='testpass'):
    """Helper function to create a user"""
    return get_user_model().objects.create_user(email, password)

class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientsApiTests(TestCase):
    """ Test for unauthenticated requests"""

    def setUp(self):
        self.user=create_user()
        self.client=APIClient()
        self.client.force_authenticate(self.user)

    def test_retreive_ingredients(self):
        """Test retreiving a list of ingredients"""

        Ingredient.objects.create(user=self.user,name='Kale')
        Ingredient.objects.create(user=self.user,name='Vanilla')

        res=self.client.get(INGREDIENTS_URL)

        ingredients=Ingredient.objects.all().order_by('-name')
        serializer=IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)

    def test_ingredients_limited_to_user(self):
        """ Test list of ingredients is limited to authenticated user"""
        user2=create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2,name='Salt')
        ingredient=Ingredient.objects.create(user=self.user,name='Pepper')

        res=self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'],ingredient.name)
        self.assertEqual(res.data[0]['id'],ingredient.id)

    def test_update_ingredient_successful(self):
        """Test update ingredient"""
        ingredient=Ingredient.objects.create(user=self.user,name='Pepper')
        payload={'name':'Cabbage'}
        url=detail_url(ingredient.id)
        res=self.client.patch(url,payload)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name,payload['name'])

    def test_delete_ingredient_successful(self):
        """Test delete ingredient"""
        ingredient=Ingredient.objects.create(user=self.user,name='Pepper')
        url=detail_url(ingredient.id)
        res=self.client.delete(url)

        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        self.assertEqual(Ingredient.objects.filter(id=ingredient.id).count(),0)

