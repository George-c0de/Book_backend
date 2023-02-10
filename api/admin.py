from django.contrib import admin

from api.models import Genre, Author, Artworks


admin.site.register(Artworks)
admin.site.register(Author)
admin.site.register(Genre)

