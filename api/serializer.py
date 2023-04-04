from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.conf import settings
from drf_yasg import openapi
from rest_framework import serializers

from api.models import Artworks, Author, BookState, Feedback, Genre, Settings

from .models import CustomUser as User


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
        list_genres = [{'name': get_object_or_404(Genre, id=el).name, 'id': el} for el in data['genres']]
        data['genres'] = list_genres
        list_author = [{'name': get_object_or_404(Author, id=pk).name, 'id': pk} for pk in data['author']]
        data['author'] = list_author
        return data


class ArtworksWithoutAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artworks
        fields = ('id', 'name', 'date', 'file', 'info',)


class AuthorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

    def get_genres(self, instance):
        artworks = Artworks.objects.filter(author=instance).select_related('genres')
        genre_counts = artworks.values('genres__id', 'genres__name').annotate(count=Count('id'))
        result = {
            'all': artworks.count(),
            'genres': []
        }
        for genre_count in genre_counts:
            genre_id = genre_count['genres__id']
            genre_name = genre_count['genres__name']
            count = genre_count['count']
            result['genres'].append(
                {
                    'id': genre_id,
                    'name': genre_name,
                    'count': count
                }
            )
        return result

    def to_representation(self, instance):
        """
        :param instance:
        :return:
        """
        data = super().to_representation(instance)
        data.update(self.get_genres(instance=instance))
        return data


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ('percent', 'size')


class SettingsRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = '__all__'


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
        if User.objects.filter(email=attrs.get('email')).exists():
            raise serializers.ValidationError(
                {"email": "Пользователь с таким email уже создан"}
            )
        return attrs

    def create(self, validated_data):
        user = None
        try:
            user = self.perform_create(validated_data)
            serializer = SettingsRegisterSerializer(data={'user': user.id})
            if serializer.is_valid():
                serializer.save()
            else:
                user.delete()
                user = None
        except (IntegrityError, Exception):
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
        fields = ('user', 'epubcfi', 'percent', 'book')

    def validate(self, data):
        if BookState.objects.filter(user=data.get('user')).exists() and BookState.objects.filter(
                book=data.get('book')).exists():
            raise serializers.ValidationError("Книга уже в списке для чтения")
        return data


class UpdateBookStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookState
        fields = '__all__'

    def update(self, instance, validated_data):
        if validated_data.get('percent', 0) == 100:
            validated_data['show'] = False
        else:
            validated_data['show'] = True
        return super().update(instance, validated_data)


class ListBookStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookState
        fields = ('percent', 'book')

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


######
# Сериализация данных
######
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


class FirstLitterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=1, help_text='Первая буква')
    count = serializers.IntegerField(help_text='Кол-во')


class SearchSerializer(serializers.Serializer):
    author = ForSearchAuthorSerializer()
    artworks = ForSearchSerializer()


class AuthorForCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    id = serializers.IntegerField(read_only=True)


class GenreForCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    id = serializers.IntegerField(read_only=True)


class YearArtworksSerializer(serializers.ModelSerializer):
    read = serializers.IntegerField(allow_null=True, help_text='Возвращает проценты или null')
    author = AuthorForCategorySerializer(many=True)
    genres = GenreForCategorySerializer(many=True)

    class Meta:
        model = Artworks
        fields = '__all__'


class FeedBackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ('text',)


class NameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)


class BookSerializer(serializers.Serializer):
    percent = serializers.IntegerField(min_value=0, max_value=100)
    book = serializers.IntegerField(read_only=True, label='id книги')
    name = serializers.CharField(max_length=150)
    author = NameSerializer(many=True)


class BookGetSerializer(serializers.Serializer):
    file = serializers.FileField()
    epubcfi = serializers.CharField(max_length=150)
    percent = serializers.IntegerField(max_value=100, min_value=0)
