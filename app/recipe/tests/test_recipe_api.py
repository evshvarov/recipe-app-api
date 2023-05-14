"""
Tests for the recipe API
"""
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer
from recipe.serializers import RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-image-upload', args=[recipe_id])

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

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag on update."""
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'Indian'}],
        }
        url = detail_url(recipe.id)
        res=self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name='Indian')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test updating a recipe with existing tag."""
        tag_breakfast=Tag.objects.create(user=self.user, name='Breakfast')
        recipe=create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch=Tag.objects.create(user=self.user, name='Lunch')
        payload={'tags': [{'name': 'Lunch'}]}
        url=detail_url(recipe.id)
        res=self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing recipe tags."""
        tag=Tag.objects.create(user=self.user, name='Dessert')
        recipe=create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload={'tags': []}
        url=detail_url(recipe.id)
        res=self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating recipe with new ingredients."""
        payload={
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'ingredients': [{'name': 'Chocolate'}, {'name': 'Cheese'}],
        }
        res=self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes=Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe=recipes[0]
        ingredients=recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists=ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating recipe with existing ingredients."""
        ingredient_chocolate=Ingredient.objects.create(
            user=self.user,
            name='Chocolate',
        )

        payload={
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': '5.00',
            'ingredients': [{'name': 'Chocolate'}, {'name': 'Cheese'}],
        }
        res=self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes=Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe=recipes[0]
        ingredients=recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_chocolate, ingredients)
        for ingredient in payload['ingredients']:
            exists=ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test create ingredient on update"""
        recipe=create_recipe(user=self.user)
        payload={'ingredients': [{'name': 'Chocolate'}]}
        url=detail_url(recipe.id)
        res=self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient=Ingredient.objects.get(user=self.user,name='Chocolate')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        """Test updating a recipe with existing ingredients."""
        ingredient_chocolate=Ingredient.objects.create(
            user=self.user,
            name='Chocolate',
        )
        recipe=create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_chocolate)

        ingredient_cheese=Ingredient.objects.create(
            user=self.user,
            name='Cheese',
        )
        payload={'ingredients': [{'name': 'Cheese'}]}
        url=detail_url(recipe.id)
        res=self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_cheese, recipe.ingredients.all())
        self.assertNotIn(ingredient_chocolate, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing recipe ingredients."""
        ingredient_chocolate=Ingredient.objects.create(
            user=self.user,
            name='Chocolate',
        )
        recipe=create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_chocolate)

        payload={'ingredients': []}
        url=detail_url(recipe.id)
        res=self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

class RecipeImageUploadTests(TestCase):
    """Test image upload for recipes."""

    def setUp(self):
            self.client=APIClient()
            self.user=create_user(
                email='user@example.com',
                password='testpass',
            )
            self.client.force_authenticate(self.user)
            self.recipe=create_recipe(user=self.user)

    def tearDown(self):
            self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
            """Test uploading an image to recipe."""
            url=image_upload_url(self.recipe.id)
            with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
                img=Image.new('RGB', (10, 10))
                img.save(ntf, format='JPEG')
                ntf.seek(0)
                res=self.client.post(url, {'image': ntf}, format='multipart')
            self.recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('image', res.data)
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
            """Test uploading an invalid image."""
            url=image_upload_url(self.recipe.id)
            res=self.client.post(url, {'image': 'notimage'}, format='multipart')
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

