from rest_framework import serializers

from core.models import Tag


class RecipeTagSerializer(serializers.ModelSerializer):
    '''Serializer for recipe tag objects'''

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)