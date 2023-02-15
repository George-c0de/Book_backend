from django.contrib import admin

from api.models import Artworks, Author, Genre

admin.site.register(Artworks)
admin.site.register(Author)
admin.site.register(Genre)

