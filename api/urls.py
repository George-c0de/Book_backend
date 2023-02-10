from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from api.views import Search, FirstLetter, FilterAuthor, FilterArtworks

schema_view = get_schema_view(
    openapi.Info(
        title="API",
        default_version='v1',
        description="Your description",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    # User
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('docs/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    path('docs/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/search/', Search.as_view()),
    # Search First Litter
    path('api/search-first-letter/', FirstLetter.as_view()),
    path('api/filter-author-first/', FilterAuthor.as_view()),
    path('api/filter-artworks-first/', FilterArtworks.as_view()),




]
