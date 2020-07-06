from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

import tempfile
import os

from PIL import Image

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    '''Return url for recipe image upload'''
    return reverse('recipe:recipe-upload_image', args=[recipe_id])


def test_tag(user, name='Test tag'):
    '''Create a test tag'''
    return Tag.objects.create(user=user, name=name)


def test_ingredient(user, name='Test ingredient'):
    '''Create a test ingredient'''
    return Ingredient.objects.create(user=user, name=name)


def recipe_detail_url(recipe_id):
    '''Return recipe detail url'''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def test_recipe(user, **kwargs):
    '''Create and return a test recipe'''
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(kwargs)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTest(TestCase):
    '''Test the public recipe api'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that login is required to access the recipe api'''
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTest(TestCase):
    '''Test the private recipe api'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@apparanto.com',
            'password 1234'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test that an authenticated user can retrieve recipes'''

        test_recipe(user=self.user,
                    title='Nasi goreng',
                    time_minutes=15,
                    price=8.50)
        test_recipe(user=self.user,
                    title='Bami goreng',
                    time_minutes=15,
                    price=9.50)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipes_limited_to_user(self):
        '''Test that only recipes of the user can be retrieved'''

        test_recipe(user=self.user,
                    title='Nasi goreng',
                    time_minutes=15,
                    price=8.50)
        test_recipe(user=self.user,
                    title='Bami goreng',
                    time_minutes=15,
                    price=9.50)

        another_user = get_user_model().objects.create_user(
            '_another@apparanto.com',
            'pass1234xxx'
        )

        test_recipe(user=another_user,
                    title='Bami goreng',
                    time_minutes=15,
                    price=9.50)

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.filter(user=self.user).order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipe_detail(self):
        '''Test retrieving a recipe detail'''
        recipe = test_recipe(user=self.user)

        recipe.tags.add(test_tag(user=self.user))
        recipe.tags.add(test_tag(user=self.user))

        recipe.ingredients.add(test_ingredient(user=self.user))
        recipe.ingredients.add(test_ingredient(user=self.user))

        url = recipe_detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        '''Test creating a basic recipe'''
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 3.50
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        '''Test creating a recipe with tags'''
        tag1 = test_tag(user=self.user)
        tag2 = test_tag(user=self.user)

        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 30,
            'price': 4.00,
            'tags': [tag1.id, tag2.id]
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        '''Test creating a recipe with ingredients'''
        ingredient1 = test_ingredient(user=self.user)
        ingredient2 = test_ingredient(user=self.user)

        payload = {
            'title': 'Thai prawn red curry',
            'time_minutes': 20,
            'price': 6.50,
            'ingredients': [ingredient1.id, ingredient2.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_update_recipe_partial(self):
        '''Test updating a recipe with PATCH'''
        recipe = test_recipe(user=self.user)

        ingredient1 = test_ingredient(user=self.user, name="Salt")
        ingredient2 = test_ingredient(user=self.user, name="Pepper")
        tag1 = test_tag(user=self.user, name="Hot")
        tag2 = test_tag(user=self.user, name="Spicy")

        recipe.ingredients.add(ingredient1)
        recipe.tags.add(tag1)
        price = recipe.price
        payload = {
            'title': 'Chicken pizza',
            'ingredients': [ingredient2.id],
            'tags': [tag2.id]
        }

        res = self.client.patch(recipe_detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        ingredients = recipe.ingredients
        self.assertEqual(ingredients.count(), 1)
        self.assertEqual(ingredients.all()[0], ingredient2)
        tags = recipe.tags
        self.assertEqual(tags.count(), 1)
        self.assertEqual(tags.all()[0], tag2)
        self.assertEqual(recipe.price, price)

    def test_update_recipe_full(self):
        '''Test a full update to a recipe'''
        recipe = test_recipe(user=self.user)

        ingredient1 = test_ingredient(user=self.user, name="Salt")
        ingredient2 = test_ingredient(user=self.user, name="Pepper")
        tag1 = test_tag(user=self.user, name="Hot")
        tag2 = test_tag(user=self.user, name="Spicy")

        recipe.ingredients.add(ingredient1)
        recipe.tags.add(tag1)
        payload = {
            'title': 'Chicken pizza',
            'time_minutes': 12,
            'price': 8.00,
            'ingredients': [ingredient2.id],
            'tags': [tag2.id]
        }

        res = self.client.put(recipe_detail_url(recipe.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        ingredients = recipe.ingredients
        self.assertEqual(ingredients.count(), 1)
        self.assertEqual(ingredients.all()[0], ingredient2)
        tags = recipe.tags
        self.assertEqual(tags.count(), 1)
        self.assertEqual(tags.all()[0], tag2)
        self.assertEqual(recipe.price, payload['price'])

    def test_filter_recipes_by_tag(self):
        '''Test that only recipes matching filter on tag are returned'''
        recipe1 = test_recipe(user=self.user, title="Veggie curry")
        recipe2 = test_recipe(user=self.user, title="Soja burger")
        recipe3 = test_recipe(user=self.user, title='Pulled pork sandwich')
        tag1 = test_tag(user=self.user, name='Vegan')
        tag2 = test_tag(user=self.user, name="Curry")
        recipe1.tags.add(tag1)
        recipe1.tags.add(tag2)
        recipe2.tags.add(tag1)

        res = self.client.get(RECIPES_URL, {
            'tags': f'{tag1.id},{tag2.id}'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_filter(self):
        '''Test that only recipes matching ingredients are returned'''
        recipe1 = test_recipe(user=self.user, title="Veggie curry")
        recipe2 = test_recipe(user=self.user, title="Soja burger")
        recipe3 = test_recipe(user=self.user, title='Pulled pork sandwich')

        ingredient1 = test_ingredient(user=self.user, name='Curry')
        ingredient2 = test_ingredient(user=self.user, name="Tofu")
        ingredient3 = test_ingredient(user=self.user, name="Pork")

        recipe1.ingredients.add(ingredient1)
        recipe1.ingredients.add(ingredient2)
        recipe2.ingredients.add(ingredient2)
        recipe3.ingredients.add(ingredient3)

        res = self.client.get(RECIPES_URL, {
            'ingredients': f'{ingredient1.id},{ingredient2.id}'
        })

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class RecipeImageUploadTests(TestCase):
    '''Tests for the recipe image upload feature'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@apparanto.com',
            'test12345'
        )
        self.client.force_authenticate(self.user)
        self.recipe = test_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        '''Test upload an image to recipe'''
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (20, 20))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.post(url, {'image': ntf}, format='multipart')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('image', res.data)

            self.recipe.refresh_from_db()
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        '''Test uploading an invalid image'''
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
