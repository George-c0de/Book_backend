from django.contrib import admin

from api.models import Artworks, Author, Feedback, Genre

admin.site.register(Artworks)
admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Feedback)

