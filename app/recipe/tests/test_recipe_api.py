"""
Tests for the recipe API
"""
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer
from recipe.serializers import RecipeDetailSerializer

def create_recipe(user, **params):
    """Helper function to create a recipe"""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'link': 'https://www.example.com/recipe.pdf',
        'description': 'Sample recipe description',
    }
    defaults.update(params)
    recipe=Recipe.objects.create(user=user, **defaults)
    return recipe

def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        url=reverse('recipe:recipe-list')
        res=self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""
    def setUp(self):
        self.client = APIClient()
        self.user=create_user(
            email='user@example.com',
            password='testpass',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        url=reverse('recipe:recipe-list')
        res=self.client.get(url)
        recipes=Recipe.objects.all().order_by('-id')
        serializer=RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        user2=create_user(
            email='other@example.com',
            password='testpass',
        )
        create_recipe(user=user2)
        create_recipe(user=self.user)
        url=reverse('recipe:recipe-list')
        res=self.client.get(url)
        recipes=Recipe.objects.filter(user=self.user)
        serializer=RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe=create_recipe(user=self.user)
        #recipe.tags.add(create_tag(user=self.user))
        #recipe.ingredients.add(create_ingredient(user=self.user))
        url=detail_url(recipe.id)
        res=self.client.get(url)
        serializer=RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload={
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
        }
        url=reverse('recipe:recipe-list')
        res=self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe=Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        original_link='https://www.example.com/recipe.pdf'
        recipe=create_recipe(user=self.user,
                            title='Chicken tikka',
                            link=original_link,
                             )

        # recipe.tags.add(create_tag(user=self.user))
        # new_tag=create_tag(user=self.user, name='Curry')
        payload={'title': 'New Chicken tikka'}
        url=detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        # tags=recipe.tags.all()
        # self.assertEqual(len(tags), 1)
        # self.assertIn(new_tag, tags)
    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe=create_recipe(user=self.user)
        # recipe.tags.add(create_tag(user=self.user))
        payload={
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': Decimal('5.00'),
            'link': 'https://www.example.com/recipe.pdf',
            'description': 'This is a test description',
        }
        url=detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.title, payload['title'])
        # tags=recipe.tags.all()
        # self.assertEqual(len(tags), 0)
    def test_update_user_returns_error(self):
        """Test that updating user returns error"""
        user2=create_user(
            email='user2@example.com',
            password='testpass',
        )
        recipe=create_recipe(user=self.user)
        payload={'user': user2.id}
        url=detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe=create_recipe(user=self.user)
        url=detail_url(recipe.id)
        res=self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.filter(id=recipe.id).exists(), False)

    def test_delete_other_users_recipe_returns_error(self):
        """Test deleting another users recipe returns error"""
        user2=create_user(email='user2@example.com', password='testpass')
        recipe=create_recipe(user=user2)
        url=detail_url(recipe.id)
        res=self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


