from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTest(TestCase):
    '''Test the publicly available recipe ingredients api'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that login is required for retrieving ingredients'''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    '''Test the privately available recipe ingredients api'''

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@apparanto.com',
            'password 1234'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        '''Test retrieving recipe ingredients'''
        Ingredient.objects.create(user=self.user, name='Rice')
        Ingredient.objects.create(user=self.user, name='Potatoes')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''Test that ingredients returned are for the authenticated user'''
        user2 = get_user_model().objects.create_user(
            'other@apparanto.com',
            'Another password 1234'
        )
        Ingredient.objects.create(user=user2, name='Sugar')
        ingredient = Ingredient.objects.create(user=self.user, name='Flour')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successfully(self):
        '''Test that a ingredient is created succesfully'''
        payload = {
            'name': 'Cauliflower'
        }
        res = self.client.post(INGREDIENTS_URL, payload)

        ingredient_exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ingredient_exists)

    def test_create_ingredient_invalid(self):
        '''Test that a ingredient with an invalid payload is not created'''
        payload = {
            'name': ''
        }
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        ingredient_count = Ingredient.objects.count()
        self.assertEqual(ingredient_count, 0)
