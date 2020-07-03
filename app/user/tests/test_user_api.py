from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''Test the users public API'''

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        '''Test creating a user with valid payload is succesful'''
        payload = {
            'email': 'test@apparanto.com',
            'password': 'test1234',
            'name': 'Test name'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        '''Test creating a user that already exists fails'''
        payload = {'email': 'test@apparanto.com', 'password': 'Test1234'}
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''Test that the password must be more than 5 characters'''
        payload = {
            'email': 'test@apparanto.com',
            'name': 'Test 1234',
            'password': 'Tst'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email'])
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''Test that a token is created for the user'''
        payload = {
            'email': 'test@apparanto.com',
            'name': 'Test 1234',
            'password': 'Tstasdf'
        }
        create_user(**payload)

        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_no_token_for_invalid_user_credentials(self):
        '''Test that no token is created for invalid credentials'''

        payload = {
            'email': 'test@apparanto.com',
            'name': 'Test 1234',
            'password': 'Wrong password'
        }
        create_user(
            email=payload['email'],
            name=payload['name'],
            password='Correct password')

        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        '''Test that no token is created if user doesn't exist'''
        payload = {
            'email': 'test@apparanto.com',
            'name': 'Test 1234',
            'password': 'Tstasdf'
        }

        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_input(self):
        '''
        Test that no token is created when no email or password is provided
        '''
        res = self.client.post(TOKEN_URL, {
            'email': 'test@apparanto.com',
            'name': 'Test 1234',
            'password': ''
        })
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthorized_user_access(self):
        '''Test if the access to me requires authentication'''
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('email', res.data)


class PrivateUserApiTest(TestCase):
    '''Test API requests that require authentication'''

    def setUp(self):
        self.user = create_user(
            email='test@apparanto.com',
            password='Pass12345',
            name='test user'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        '''Test retrieving profile for logged in user'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_is_not_allowed(self):
        '''Test that POST is not allowed on the me URL'''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''Test updating the profile for an authenticated user'''
        payload = {
            'name': 'New name',
            'password': 'New Password 123'
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.user.check_password(payload['password'])
