from collections import defaultdict
from rest_framework.parsers import JSONParser
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Artworks, Author, BookState, Feedback, Genre, Settings
from api.serializer import (ArtworksSerializer,
                            ArtworksWithoutAuthorSerializer,
                            AuthorDetailSerializer, AuthorSerializer,
                            BookGetSerializer, BookSerializer,
                            BookStateSerializer, FeedbackSerializer,
                            FeedBackSerializer, FirstLitterSerializer,
                            ListBookStateSerializer, SearchSerializer,
                            SettingsSerializer, UpdateBookStateSerializer,
                            YearArtworksSerializer)


class PaginationApiView:
    """
    Пагинация
    """

    def __init__(self, request, data):
        """
        Создание класса для пагинации
        :param request: В зарпосе передаются значения page, limit
        :param data: Данные, которые нужно разбить
        """
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        if limit < 0:
            limit = 10
        limit = min(limit, 100)
        p = Paginator(data, limit)
        if page > p.num_pages:
            page = p.num_pages
        elif page < 1:
            page = 1
        page_data = p.get_page(page)
        self.count = p.count
        self.limit = limit
        self.page = page
        self.total = p.num_pages
        self.items = page_data.object_list

    def get_str(self) -> dict:
        return {
            "count": self.count,
            "limit": self.limit,
            "page": self.page,
            "total": self.total,
            "items": self.items,
        }


RESPONSE = ''


def get_first_litters(model) -> list:
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
    return [{'name': result, 'count': value} for result, value in letters.items()]


def check_in_reading_list(user: User | None, book: Artworks) -> int | None:
    """
    Проверяет есть ли книга в списке для чтения
    :param book: Книга для проверки
    :param user: Пользователь
    :return: Если книга есть в списке для чтения выводит словарь с процентами для чтения, если нет пустой список
    """
    if BookState.objects.filter(user=user).filter(book=book).exists():
        return BookState.objects.filter(user=user).get(book=book).percent
    else:
        return None


class Library(ListModelMixin, GenericAPIView):
    """
    Endpoints для библиотеки
    Получение списка всех авторов, отсортированных по ФИО
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
    Поиск производиться среди авторов и произведений, принимает value - str, null=True
    Если value = null, выдает полный список авторов и произведений
    """

    def get_filters(self, request) -> tuple:
        """Получить все фильтры"""
        value = request.GET.get('value', '')
        author = request.GET.get('author', False)
        artwork = request.GET.get('artworks', False)
        return value, author, artwork

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'value', in_=openapi.IN_QUERY, description='Значение для поиска',
                type=openapi.TYPE_STRING, default=''
            ),
            openapi.Parameter(
                'author', in_=openapi.IN_QUERY, description='bool значение, задает критерий поиска',
                type=openapi.TYPE_BOOLEAN, default=False
            ),
            openapi.Parameter(
                'artworks', in_=openapi.IN_QUERY, description='bool значение, задает критерий поиска',
                type=openapi.TYPE_BOOLEAN, default=False
            ),
            openapi.Parameter(
                'page', in_=openapi.IN_QUERY, description='Страница', type=openapi.TYPE_INTEGER, default=1
            ),
            openapi.Parameter(
                'limit', in_=openapi.IN_QUERY, description='Лимит страницы', type=openapi.TYPE_INTEGER, default=10
            ),
        ],
        responses={
            200: openapi.Response('Successful Response', schema=SearchSerializer),
        })
    def get(self, request):
        data = {}
        value, author, artwork = self.get_filters(request=request)

        if author:
            authors = Author.objects.filter(name__icontains=value)
            data['authors'] = PaginationApiView(
                request=request,
                data=AuthorSerializer(authors, many=True).data
            ).get_str()
        elif artwork:
            artworks = Artworks.objects.filter(name__icontains=value)
            data['artworks'] = ArtworksSerializer(artworks, many=True).data
            for el in data.get('artworks', []):
                el['read'] = check_in_reading_list(user=request.user.id, book=el.get('id'))
            data['artworks'] = PaginationApiView(data=data['artworks'], request=request).get_str()
        else:
            authors = Author.objects.filter(name__icontains=value)
            artworks = Artworks.objects.filter(name__icontains=value)
            data['authors'] = AuthorSerializer(authors, many=True).data
            data['artworks'] = ArtworksSerializer(artworks, many=True).data

            for el in data.get('artworks', []):
                el['read'] = check_in_reading_list(user=request.user.id, book=el.get('id'))

            new_data = []
            AUTHOR = 'author'
            ARTWORKS = 'artworks'
            for author_t in data['authors']:
                author_t['type'] = AUTHOR
                new_data.append(author_t)
            for artw_t in data['artworks']:
                artw_t['type'] = ARTWORKS
                new_data.append(artw_t)
            data = PaginationApiView(data=new_data, request=request).get_str()
        return Response(status=status.HTTP_200_OK, data=data)


class FilterArtworks(ListModelMixin, GenericAPIView):
    """Результат поиска по первой букве произведения"""
    queryset = Artworks.objects.all()
    serializer_class = ArtworksSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        data = self.serializer_class(
            self.queryset.filter(name__startswith=request.GET.get('value', '')),
            many=True).data
        for el in data:
            el['read'] = check_in_reading_list(user=request.user.id, book=el.get('id'))
        return Response(
            data=data,
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


class FirstLetterAuthor(GenericAPIView):
    """Получение списка букв для поиска авторов по первой букве"""
    serializer_class = FirstLitterSerializer(many=True)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Successful Response', schema=FirstLitterSerializer(many=True)),
        })
    def get(self, request):
        letters = get_first_litters(model=Author)
        return Response(status=200, data=letters)


class YearCategoryArtworks(GenericAPIView):
    """Вывод всех дат и кол-во произведений"""
    queryset = Artworks.objects.all().values_list('date', flat=True)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Successful Response', schema=FirstLitterSerializer(many=True)),
        })
    def get(self, request, *args, **kwargs):
        years = {}
        for artwork in self.get_queryset():
            years[artwork] = years.get(artwork, 0) + 1
        result = [{'name': year, 'count': value} for year, value in years.items()]
        return Response(status=status.HTTP_200_OK, data=result)


class GenreListCategory(ListModelMixin, GenericAPIView):
    """Получение списка жанров и кол-во"""
    queryset = Genre.objects.all().values_list('name', flat=True)

    def list(self, request, *args, **kwargs):
        return [
            {
                'name': name,
                'count': Artworks.objects.filter(genres__name=name).count(),
            }
            for name in self.get_queryset()
        ]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Successful Response', schema=FirstLitterSerializer(many=True)),
        })
    def get(self, request):
        return Response(status=status.HTTP_200_OK, data=self.list(request))


def last_book_by_author(user: int, author: Author) -> dict | None:
    """
    Получение последней книги для чтения по автору, если нет, возвращаем None
    :param user: Авторизированный пользователь или None, id
    :param author: Автор для поиска
    :return: Возвращаем название и процент книги, если не нашли, None
    """
    if BookState.objects.filter(book__author=author).filter(user=user).exists():
        book = BookState.objects.filter(book__author=author).filter(user=user).order_by('-date_update').first()
        return {
            'id': book.book.id,
            'name': book.book.name,
            'percent': book.percent,
        }
    else:
        return None


class GetAuthor(RetrieveModelMixin, GenericAPIView):
    """ Получение автора """
    queryset = Author.objects.all()
    serializer_class = AuthorDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['last'] = last_book_by_author(user=request.user.id, author=data['id'])
        return Response(data)

    def get(self, request, pk):
        return self.retrieve(request, pk=pk)


class GetBook(GenericAPIView):
    """Получение книги, файл, точка остановки и проценты"""
    queryset = BookState.objects.all()
    serializer_class = BookGetSerializer

    @swagger_auto_schema(
        responses={
            201: openapi.Response('Created', schema=BookGetSerializer()),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'errors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    )
                }
            )),
            401: openapi.Response('Authentication credentials were not provided.')
        },
    )
    def get(self, request, pk):
        book = get_object_or_404(Artworks, id=pk)
        book_state = get_object_or_404(self.get_queryset().filter(user=request.user.id), book_id=pk)
        data = {
            'file': book.file,
            'epubcfi': book_state.epubcfi,
            'percent': book_state.percent,
        }
        serializer = self.get_serializer(data)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class GetSettings(GenericAPIView):
    """Получение настроек"""
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
        if not obj_ser.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=obj_ser.errors)
        obj_ser.save()
        return Response(status=status.HTTP_200_OK, data=obj_ser.data)


class CreateFeedBack(CreateAPIView):
    """Создание сообщения для обратной связи"""
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['text'],
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            201: openapi.Response('Created', schema=FeedBackSerializer()),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'errors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    )
                }
            )),
            401: openapi.Response('Authentication credentials were not provided.')
        },
    )
    def post(self, request, *args, **kwargs):
        return self.create(request)

    def create(self, request, *args, **kwargs):
        data = {'user': request.user.id}
        data |= request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CreateBookState(CreateAPIView):
    """Добавление книги для чтения"""
    queryset = BookState.objects.all()
    serializer_class = BookStateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        data = {'user': request.user.id}
        data |= request.data
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['epubcfi', 'percent', 'book'],
            properties={
                'epubcfi': openapi.Schema(type=openapi.TYPE_STRING),
                'percent': openapi.Schema(type=openapi.TYPE_INTEGER),
                'book': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={
            201: openapi.Response('Created', schema=FeedBackSerializer()),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'errors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    )
                }
            )),
            401: openapi.Response('Authentication credentials were not provided.')
        },
    )
    def post(self, request, *args, **kwargs):
        return self.create(request)


class ListBookState(ListModelMixin, GenericAPIView):
    """Список книг для чтения"""
    queryset = BookState.objects.filter(show=True)
    serializer_class = ListBookStateSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(user=request.user).order_by('-date_update')
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Successful Response', schema=BookSerializer()),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'errors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    )
                }
            )),
            401: openapi.Response('Authentication credentials were not provided.')
        },
    )
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


class UpdateStateBook(GenericAPIView):
    """Обновление состояния книги для чтения"""
    queryset = BookState.objects.all()
    serializer_class = UpdateBookStateSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['epubcfi', 'percent'],
            properties={
                'epubcfi': openapi.Schema(type=openapi.TYPE_STRING),
                'percent': openapi.Schema(type=openapi.TYPE_INTEGER)
            },
        ),
        responses={
            200: openapi.Response('Successful Response', schema=UpdateBookStateSerializer()),
            400: openapi.Response('Bad Request', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'errors': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_STRING,
                        )
                    )
                }
            )),
            401: openapi.Response('Authentication credentials were not provided.')
        },
    )
    def patch(self, request, pk, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id
        data['book'] = get_object_or_404(Artworks, id=pk).id
        if BookState.objects.filter(user=request.user.id, book=data['book']).exists():
            book_state = get_object_or_404(BookState.objects.filter(user=request.user.id), book=data['book'])
            serializer = UpdateBookStateSerializer(book_state, data=data)
        else:
            serializer = UpdateBookStateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)


class FilterYearArtworks(GenericAPIView):
    """Поиск по году"""
    serializer_class = ArtworksSerializer
    queryset = Artworks.objects.all()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'year', in_=openapi.IN_QUERY, description='Значение для поиска',
                type=openapi.TYPE_STRING, default='Передается год для поиска'
            ),
        ], responses={
            200: openapi.Response('Successful Response', schema=YearArtworksSerializer),
        },

    )
    def get(self, request):
        year = request.GET.get('year', '')
        objs = self.get_serializer(self.get_queryset().filter(date=year), many=True).data
        for artwork in objs:
            artwork['read'] = check_in_reading_list(user=request.user.id, book=artwork.get('id'))
        return Response(status=status.HTTP_200_OK, data=objs)


class FilterGenreArtworks(GenericAPIView):
    """Получение произведений по жанру"""
    serializer_class = ArtworksSerializer
    queryset = Artworks.objects.all()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'genre', in_=openapi.IN_QUERY, description='Значение для поиска',
                type=openapi.TYPE_STRING, default='Название жанра для поиска'
            ),
        ], responses={
            200: openapi.Response('Successful Response', schema=YearArtworksSerializer(many=True)),
        },

    )
    def get(self, request):
        genre = request.GET.get('genre', '')
        objs = self.get_serializer(self.get_queryset().filter(genres__name=genre), many=True).data
        for artwork in objs:
            artwork['read'] = check_in_reading_list(user=request.user.id, book=artwork.get('id'))
        return Response(status=status.HTTP_200_OK, data=objs)


class GetGenreAuthorBooks(GenericAPIView):
    """Получение книг по жанру и автору"""
    queryset = Artworks.objects.all()
    serializer_class = ArtworksWithoutAuthorSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'author', in_=openapi.IN_QUERY, description='Значение для поиска',
                type=openapi.TYPE_STRING, default='Id автора'
            ),
            openapi.Parameter(
                'genre', in_=openapi.IN_QUERY, description='Значение для поиска',
                type=openapi.TYPE_STRING, default='Id жанра'
            ),
        ], responses={
            200: openapi.Response('Successful Response', schema=ArtworksWithoutAuthorSerializer(many=True)),
            400: openapi.Response('errors', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, default='Все поля должны быть заполнены')
                })),
        },

    )
    def get(self, request):
        author = request.GET.get('author')
        genre = request.GET.get('genre')
        if author is None or genre is None:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'errors': 'Все поля должны быть заполнены'})

        objs = self.get_serializer(
            self.get_queryset().filter(author__id=int(author)).filter(genres__id=int(genre)),
            many=True
        ).data
        for artwork in objs:
            artwork['read'] = check_in_reading_list(user=request.user.id, book=artwork.get('id'))
        return Response(status=status.HTTP_200_OK, data=objs)
