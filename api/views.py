from rest_framework import status
from rest_framework.generics import ListCreateAPIView, GenericAPIView, ListAPIView
from rest_framework.mixins import ListModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import Author, Artworks, Genre
from api.serializer import AuthorSerializer, ArtworksSerializer, AuthorDetailSerializer
from collections import defaultdict
from django.shortcuts import get_object_or_404


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


class Search(APIView):
    def get(self, request):
        value = request.GET.get('value')
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
            data=self.serializer_class(self.queryset.filter(name__startswith=request.GET.get('value')), many=True).data,
            status=200
        )

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class FilterAuthor(ListModelMixin, GenericAPIView):
    """Результат поиска по перовй букве автора"""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        return Response(
            data=self.serializer_class(self.queryset.filter(name__startswith=request.GET.get('value')), many=True).data,
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
        names = {}
        for name in self.get_queryset():
            names[name] = names.get(name, 0) + 1
        return names

    def get(self, request):
        return Response(status=status.HTTP_200_OK, data=self.list(request))


class GetAuthor(RetrieveModelMixin, GenericAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorDetailSerializer

    def get(self, request, pk):
        return self.retrieve(request, pk=pk)
