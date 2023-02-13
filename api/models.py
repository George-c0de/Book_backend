from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User)


    # settings


class Genre(models.Model):
    class Meta:
        verbose_name = 'Жанры'
        verbose_name_plural = 'Жанр'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField('Название', max_length=150)


class Author(models.Model):
    class Meta:
        verbose_name = 'Авторы'
        verbose_name_plural = 'Автор'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField('ФИО автора', max_length=300)
    name_en = models.CharField('ФИО автора транслитом', max_length=300)

    date_birth = models.DateField('Дата рождения')
    date_death = models.DateField('Дата смерти')

    info = models.TextField('Информация')


class Artworks(models.Model):
    class Meta:
        verbose_name = 'Произведения'
        verbose_name_plural = 'Произведение'

    def __str__(self):
        return f'{self.name}'

    # TODO сделать многие ко многим
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    name = models.CharField('Название', max_length=300)
    name_en = models.CharField('Название транслитом', max_length=300)

    date = models.CharField('Дата написания', max_length=4)
    # TODO сделать дату
    # date = models.DateField('Дата написания')

    field_1 = models.CharField('Поле 1', max_length=150)
    field_2 = models.CharField('Поле 2', max_length=150)

    genres = models.ManyToManyField(Genre)


class Feedback(models.Model):
    class Meta:
        verbose_name = 'Произведения'
        verbose_name_plural = 'Произведение'

    def __str__(self):
        return f'{self.text[:10]}'

    text = models.TextField('Текст обращения')
    user = models.ForeignKey(User, on_delete=models.CASCADE)



class BookState(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    book = models.ForeignKey(Artworks)
    epubcfi = models.CharField(max_length=1024)
    # ...
