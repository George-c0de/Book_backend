from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from api.models import Artworks, Author, Genre, Settings, Feedback, BookState
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import IntegrityError, transaction
from rest_framework import serializers
from djoser.conf import settings


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
        list_author = [get_object_or_404(Author, id=pk).name for pk in data['author']]
        data['author'] = list_author
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
                        'id': genre.id,
                        'count': 1,
                        'values': [{
                            'id': artwork.id,
                            'name': artwork.name,
                            'date': artwork.date
                        }]
                    })
        data.update(result)
        return data


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ('percent', 'size')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    default_error_messages = {
        "cannot_create_user": settings.CONSTANTS.messages.CANNOT_CREATE_USER_ERROR
    }

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.LOGIN_FIELD,
            settings.USER_ID_FIELD,
            "password",
        )

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error["non_field_errors"]}
            )

        return attrs

    def create(self, validated_data):
        user = None
        try:
            user = self.perform_create(validated_data)
            Settings.objects.create(
                user=user
            )
        except IntegrityError:
            self.fail("cannot_create_user")
        except Exception:
            self.fail("cannot_create_user")
        return user

    def perform_create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            if settings.SEND_ACTIVATION_EMAIL:
                user.is_active = False
                user.save(update_fields=["is_active"])
        return user


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('text', 'user')


class BookStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookState
        fields = '__all__'

    def validate(self, data):
        if BookState.objects.filter(user=data.get('user')).exists() and BookState.objects.filter(
                book=data.get('book')).exists():
            raise serializers.ValidationError("Книга уже в списке для чтения")
        return data


class UpdateBookStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookState
        fields = '__all__'

    def validate(self, data):
        if data.get('percent', 0) == 100:
            data.get['show'] = False
        return data


class ListBookStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookState
        fields = ('id', 'percent', 'book')

    def to_representation(self, instance):
        """
        Дополнение жанрами
        :param instance:
        :return:
        """
        data = super().to_representation(instance)
        artworks = get_object_or_404(Artworks, id=data.get('book'))
        data['name'] = artworks.name
        data['author'] = artworks.author.all().values_list('name', flat=True)
        return data
