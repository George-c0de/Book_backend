from collections import defaultdict

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
        result = {
            'all': 0,
            'genres': []
        }
        for artwork in Artworks.objects.filter(author=instance).only('id', 'name', 'date'):
            for genre in artwork.genres.all().only('name'):
                result['all'] += 1
                for el in result['genres']:
                    if el['name'] == genre.name:
                        el['count'] += 1
                        el['values'].append({
                            'id': artwork.id,
                            'name': artwork.name,
                            'date': artwork.date
                        })
                        break
                else:
                    result['genres'].append({
                        'name': genre.name,
                        'count': 1,
                        'values': [{
                            'id': artwork.id,
                            'name': artwork.name,
                            'date': artwork.date
                        }]
                    })
        data.update(result)
        return data
