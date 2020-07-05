from django.test import TestCase
from django.contrib.auth import get_user_model

from unittest.mock import patch

from core import models


def test_user(email='test@apparanto.com', password='testpwd123'):
    '''Create a test user'''
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_succesful(self):
        '''Test creating a new user with an e-mail is succesful'''

        email = 'test@apparanto.com'
        password = 'some password'

        user = get_user_model().objects.create_user(
            email=email,
            password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_with_normalized_email(self):
        '''Test the e-mail of a new user is normalized'''

        email = 'test@APPARANTO.COM'

        user = get_user_model().objects.create_user(
            email=email,
            password='Another password'
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        '''Test creating user with no valid email raises error'''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='abc', password='1234'
                )

    def test_create_new_super_user(self):
        '''Test creating a new super user'''

        user = get_user_model().objects.create_superuser(
            'test@apparanto.com',
            'pwd123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        '''Test the tag string representation'''
        tag = models.Tag.objects.create(
            user=test_user(),
            name='Vegan'
        )
        self.assertEqual(str(tag), tag.name)

    def test_ingredient(self):
        '''Test the ingredient string representation'''
        ingredient = models.Ingredient.objects.create(
            user=test_user(),
            name='Rice'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        '''Test the recipe string representation'''
        recipe = models.Recipe.objects.create(
            user=test_user(),
            title='Nasi goreng',
            time_minutes=30,
            price=6.50
        )
        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_image_is_saved_with_unique_name(self, mock_uuid):
        '''Test that image is save in the correct location'''
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid

        file_path = models.recipe_image_file_path(None, 'some_image.jpg')
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
