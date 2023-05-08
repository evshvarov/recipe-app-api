"""
Serializers for recipe app
"""
from rest_framework import serializers

from core.models import Recipe, Tag

class RecipeTagSerializer(serializers.ModelSerializer):
    """Serializer for recipe tag objects"""
    class Meta:
        model = Tag
        fields = ('id', 'name',)
        read_only_fields = ('id',)

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects"""

    tags=RecipeTagSerializer(many=True,required=False)

    def _get_or_create_tags(self, tags, instance):
        """Helper function to get or create tags"""
        for tag in tags:
            tag_obj, created=Tag.objects.get_or_create(
                user=self.context['request'].user,
                name=tag['name'],)
            instance.tags.add(tag_obj)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'time_minutes', 'price', 'link','tags',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Create a recipe"""
        tags=validated_data.pop('tags',[])
        recipe=Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags=validated_data.pop('tags',None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail objects"""
    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'time_minutes', 'price', 'link', 'description','tags',
        )
        read_only_fields = ('id',)



