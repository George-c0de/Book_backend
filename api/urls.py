from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from api.views import Search, FilterAuthor, FilterArtworks, FirstLetterAuthor, YearCategoryArtworks, GenreListCategory, \
    GetAuthor, GetBook

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

    # Получение select
    path('api/artworks-year/', YearCategoryArtworks.as_view()),
    path('api/genre-names/', GenreListCategory.as_view()),

    # Получение автора
    path('api/detail-author/<int:pk>/', GetAuthor.as_view()),

    # Получение книги
    path('api/book/<int:pk>', GetBook.as_view()),


]
