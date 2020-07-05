from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient, Recipe
from recipe import serializers


class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.DestroyModelMixin):
    '''Base viewset for model recipe attribute class'''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        '''Retrieve all the recipe attributes belonging to the user'''
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        '''Create a new recipe attribute object'''
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    '''Manage tags in the database'''

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    '''Manage ingredients in the database'''

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    '''Manage recipes in the database'''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()

    def get_queryset(self):
        '''Retrieve all the recipe objects belonging to the user'''
        return self.queryset.filter(user=self.request.user).order_by('-title')

    def get_serializer_class(self):
        '''Return the the serializer appropriate for the request'''
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        '''Create a new recipe'''
        serializer.save(user=self.request.user)
