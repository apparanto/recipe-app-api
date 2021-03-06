from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTest(TestCase):
    '''Test the publicly available recipe tags api'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that login is required for retrieving tags'''
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    '''Test the privately available recipe tags api'''

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@apparanto.com',
            'password 1234'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Test retrieving recipe tags'''
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test that tags returned are for the authenticated user'''
        user2 = get_user_model().objects.create_user(
            'other@apparanto.com',
            'Another password 1234'
        )
        Tag.objects.create(user=user2, name='Harty')
        tag = Tag.objects.create(user=self.user, name='Beefy')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successfully(self):
        '''Test that a tag is created succesfully'''
        payload = {
            'name': 'Potatoy'
        }
        res = self.client.post(TAGS_URL, payload)

        tag_exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(tag_exists)

    def test_create_tag_invalid(self):
        '''Test that a tag with an invalid payload is not created'''
        payload = {
            'name': ''
        }
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        tag_count = Tag.objects.count()
        self.assertEqual(tag_count, 0)

    def test_delete_tag(self):
        tag = Tag.objects.create(user=self.user, name='Test tag')

        tag_url = reverse('recipe:tag-detail', args=[tag.id])
        res = self.client.delete(tag_url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.all()
        self.assertEqual(tags.count(), 0)
