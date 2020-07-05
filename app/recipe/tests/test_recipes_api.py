from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


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
        price = recipe.price
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
