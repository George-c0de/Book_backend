from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api.models import Author, Artworks, Genre


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class ArtworksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artworks
        fields = '__all__'

    def to_representation(self, instance):
        """
        Дополнение жанрами
        :param instance:
        :return:
        """
        data = super().to_representation(instance)
        list_genres = [get_object_or_404(Genre, id=el).name for el in data['genres']]
        data['genres'] = list_genres

        return data


class AuthorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

    def to_representation(self, instance):
        """
        :param instance:
        :return:
        """
        data = super().to_representation(instance)
        data['artworks'] = {}
        for artwork in Artworks.objects.all():
            data['artworks'][artwork] = data['artworks'].get(artwork, 0) + 1
        return data
