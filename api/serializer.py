from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from djoser.conf import settings
from rest_framework import serializers

from api.models import Artworks, Author, BookState, Feedback, Genre, Settings
from drf_yasg import openapi


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


class SelectSearch(serializers.Serializer):
    author = serializers.IntegerField()
    artworks = serializers.IntegerField()


class ForSearchSerializer(serializers.JSONField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Artworks",
            "properties": {
                "name": openapi.Schema(
                    title="name",
                    type=openapi.TYPE_STRING,
                    description='Название книги'
                ),
                "id": openapi.Schema(
                    title="id",
                    type=openapi.TYPE_INTEGER,
                    description='Id книги',
                    read_only=True,
                ),
                "author": openapi.Schema(
                    title="author",
                    type=openapi.TYPE_STRING,
                    description='ФИО автора'
                ),
                "read": openapi.Schema(
                    title="read",
                    type=openapi.TYPE_OBJECT,
                    nullable=True,
                    properties={
                        "percent": openapi.Schema(
                            title="percent",
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_INT32,
                            description='Процент прочтения'
                        ),
                    }
                ),
                "type": openapi.Schema(
                    title="type",
                    type=openapi.TYPE_STRING,
                    description='Тип переменной',
                    example='author or artworks'
                ),
            },

        }


class ForSearchAuthorSerializer(serializers.JSONField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_OBJECT,
            "title": "Авторы",
            "properties": {
                "id": openapi.Schema(
                    title="id",
                    type=openapi.TYPE_INTEGER,
                    description='Id',
                    read_only=True,
                ),
                "name": openapi.Schema(
                    title="name",
                    type=openapi.TYPE_STRING,
                    description='ФИО',
                    maxLength=300,
                    minLength=1,
                ),
                "date_birth": openapi.Schema(
                    title="date_birth",
                    type=openapi.TYPE_STRING,
                    description='Дата рождения',
                    format=openapi.FORMAT_DATE
                ),
                "date_death": openapi.Schema(
                    title="date_death",
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATE,
                    description='Дата смерти',
                    nullable=True
                ),
                "info": openapi.Schema(
                    title="info",
                    type=openapi.TYPE_STRING,
                    description='Информация',
                ),
            },

        }


class SearchSerializer(serializers.Serializer):
    author = ForSearchAuthorSerializer()
    artworks = ForSearchSerializer()
