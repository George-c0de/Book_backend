from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import (GenericAPIView, ListAPIView,
                                     ListCreateAPIView, CreateAPIView, UpdateAPIView)
from rest_framework.mixins import (DestroyModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Artworks, Author, Genre, Settings, Feedback, BookState
from api.serializer import (ArtworksSerializer, AuthorDetailSerializer,
                            AuthorSerializer, SettingsSerializer, UserCreateSerializer, FeedbackSerializer,
                            BookStateSerializer, ListBookStateSerializer, UpdateBookStateSerializer)


def get_first_litters(model) -> dict:
    """
    Получение всех первым букв в названии у модели
    :param:
    model - Модель для поиска, обязательно имеет поле name
    :return: Словарь, ключ = буква, значение = кол-во
    """
    letters = defaultdict(int)
    for name in model.objects.values_list('name', flat=True):
        first_letter = name[0]
        letters[first_letter] += 1

    return letters


class Library(ListModelMixin, GenericAPIView):
    """
    Endpoints для библиотеки
    """
    queryset = Author.objects.all().order_by('name')
    serializer_class = AuthorSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        queryset = self.queryset()
        serializer = AuthorSerializer(queryset, many=True)
        return Response(serializer.data)


class Search(GenericAPIView):
    """
    Поиск среди авторов и произведений
    """

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('value', in_=openapi.IN_QUERY, description='Значение для поиска', type=openapi.TYPE_STRING)
    ])
    def get(self, request):
        value = request.GET.get('value', '')
        authors = Author.objects.filter(name__icontains=value)
        artworks = Artworks.objects.filter(name__icontains=value)
        results = {
            'authors': AuthorSerializer(authors, many=True).data,
            'artworks': ArtworksSerializer(artworks, many=True).data,
        }
        return Response(status=status.HTTP_200_OK, data=results)


class FilterArtworks(ListModelMixin, GenericAPIView):
    """Результат поиска по первой букве произведения"""
    queryset = Artworks.objects.all()
    serializer_class = ArtworksSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        return Response(
            data=self.serializer_class(
                self.queryset.filter(
                    name__startswith=request.GET.get('value', '')
                ), many=True).data,
            status=200
        )

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class FilterAuthor(ListModelMixin, GenericAPIView):
    """Результат поиска по перовой букве автора"""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        return Response(
            data=self.serializer_class(
                self.queryset.filter(
                    name__startswith=request.GET.get('value', '')
                ),
                many=True
            ).data,
            status=200
        )

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class GenreList(ListAPIView):
    """Список Жанров"""
    queryset = Genre.objects.all()
    serializer_class = Genre


class FirstLetterAuthor(APIView):
    """Получение списка букв для поиска авторов по первой букве"""

    def get(self, request):
        letters = get_first_litters(model=Author)
        return Response(status=200, data=letters)


class YearCategoryArtworks(GenericAPIView):
    """Вывод всех дат и кол-во произведений"""
    queryset = Artworks.objects.all().values_list('date', flat=True)

    def get(self, request, *args, **kwargs):
        years = {}
        for artwork in self.get_queryset():
            years[artwork] = years.get(artwork, 0) + 1
        return Response(status=status.HTTP_200_OK, data=years)


class GenreListCategory(ListModelMixin, GenericAPIView):
    queryset = Genre.objects.all().values_list('name', flat=True)

    def list(self, request, *args, **kwargs):
        names = []
        for name in self.get_queryset():
            names.append(
                {
                    'name': name,
                    'count': Artworks.objects.filter(genres__name=name).count(),

                }
            )
        return names

    def get(self, request):
        return Response(status=status.HTTP_200_OK, data=self.list(request))


class GetAuthor(RetrieveModelMixin, GenericAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorDetailSerializer

    def get(self, request, pk):
        return self.retrieve(request, pk=pk)


class GetBook(RetrieveModelMixin, GenericAPIView):
    queryset = Artworks.objects.all()
    serializer_class = ArtworksSerializer

    def get(self, request, pk):
        return self.retrieve(request, pk=pk)


class GetSettings(GenericAPIView):
    serializer_class = SettingsSerializer
    queryset = Settings.objects.all()
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        obj = get_object_or_404(self.get_queryset(), user_id=request.user.id)
        obj_ser = self.get_serializer(obj).data
        return Response(status=status.HTTP_200_OK, data=obj_ser)

    def post(self, request):
        obj = get_object_or_404(self.get_queryset(), user_id=request.user.id)
        obj_ser = self.get_serializer(obj, request.data, partial=True)
        if obj_ser.is_valid():
            obj_ser.save()
            return Response(status=status.HTTP_200_OK, data=obj_ser.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=obj_ser.errors)


class CustomRegistrationView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        Settings.objects.create(
            user=serializer.data.id
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get(self, request, *args, **kwargs):
        return self.create(request)


class CreateFeedBack(CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = {'user': request.user.id}
        data.update(request.data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CreateBookState(CreateAPIView):
    queryset = BookState.objects.all()
    serializer_class = BookStateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = {'user': request.user.id}
        data.update(request.data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ListBookState(ListModelMixin, GenericAPIView):
    queryset = BookState.objects.filter(show=True)
    serializer_class = ListBookStateSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user).order_by('-date_update')
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request):
        return self.list(request)


class DeleteBookState(GenericAPIView):
    queryset = BookState.objects.all()
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        book = get_object_or_404(
            self.get_queryset().filter(user=request.user),
            id=pk
        )
        book.show = False
        book.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateStateBook(UpdateAPIView):
    queryset = BookState.objects.all()
    serializer_class = UpdateBookStateSerializer


class FilterYearArtworks(GenericAPIView):
    serializer_class = ArtworksSerializer
    queryset = Artworks.objects.all()

    def get(self, request):
        year = request.GET.get('year', '')
        objs = self.get_serializer(self.get_queryset().filter(date=year), many=True).data
        return Response(status=status.HTTP_200_OK, data=objs)


class FilterGenreArtworks(GenericAPIView):
    serializer_class = ArtworksSerializer
    queryset = Artworks.objects.all()

    def get(self, request):
        genre = request.GET.get('genre', '')
        objs = self.get_serializer(self.get_queryset().filter(genres__name=genre), many=True).data
        return Response(status=status.HTTP_200_OK, data=objs)


class GetGenreAuthorBooks(GenericAPIView):
    queryset = Artworks.objects.all()
    serializer_class = ArtworksSerializer

    def get(self, request):
        author = request.GET.get('author')
        genre = request.GET.get('genre')
        if author is None or genre is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': 'Все поля должны быть заполнены'})

        objs = self.get_serializer(
            self.get_queryset().filter(author__id=int(author)).filter(genres__id=int(genre)),
            many=True
        )
        return Response(status=status.HTTP_200_OK, data=objs.data)
