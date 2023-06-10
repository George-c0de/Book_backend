from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from api.views import (CreateBookState, CreateFeedBack, FilterArtworks,
                       FilterAuthor, FilterGenreArtworks, FilterYearArtworks,
                       FirstLetterAuthor, GenreListCategory, GetAuthor,
                       GetBook, GetGenreAuthorBooks, GetSettings,
                       ListBookState, Search, UpdateStateBook,
                       YearCategoryArtworks, BookCreate)

schema_view = get_schema_view(
    openapi.Info(
        title="API",
        default_version='v1',
        description="Your description",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
urlpatterns = [
    # User
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('api/settings/', GetSettings.as_view()),

    # Docs
    path('docs/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    path('docs/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Search
    path('api/search/', Search.as_view()),

    # Select First Litter
    path('api/first-letter-author/', FirstLetterAuthor.as_view()),

    # Фильтры
    path('api/filter-author-first/', FilterAuthor.as_view()),
    path('api/filter-artworks-first/', FilterArtworks.as_view()),

    # Поиск по году
    path('api/filter-year-artworks/', FilterYearArtworks.as_view()),
    # Получение произведений по жанру
    path('api/filter-genre-artworks/', FilterGenreArtworks.as_view()),

    # Получение select
    path('api/artworks-year/', YearCategoryArtworks.as_view()),
    path('api/genre-names/', GenreListCategory.as_view()),

    # Получение автора
    path('api/detail-author/<int:pk>/', GetAuthor.as_view()),

    # Получение книг по жанру и автору
    path('api/books-genre-author/', GetGenreAuthorBooks.as_view()),

    # Получение книги
    path('api/book/<int:pk>/', GetBook.as_view()),

    # Форма обратной связи
    path('api/feedback/', CreateFeedBack.as_view()),

    # Создание списка для чтения
    path('api/book-state/', CreateBookState.as_view()),

    # Список книг у пользователя
    path('api/books/', ListBookState.as_view()),

    # Удаление книги из списка чтения
    # path('api/delete-book-state/<int:pk>/', DeleteBookState.as_view()),

    # Обновление состояния книги
    path('api/update-state-book/<int:pk>/', UpdateStateBook.as_view()),

    path('api/create-book/', BookCreate.as_view()),

]
