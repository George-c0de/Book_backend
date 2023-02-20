from django.contrib.auth.models import User
from django.db import models

from api.validate import validate_percent


class Settings(models.Model):
    class Meta:
        verbose_name = 'Настройки пользователей'
        verbose_name_plural = 'Настройка у пользователя'

    def __str__(self):
        return f'{self.user.username}'

    percent = models.IntegerField('Яркость экрана', validators=(validate_percent,), default=50)
    size = models.IntegerField('Размер шрифта', default=16)
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Genre(models.Model):
    class Meta:
        verbose_name = 'Жанры'
        verbose_name_plural = 'Жанр'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField('Название', max_length=150, unique=True)


class Author(models.Model):
    class Meta:
        verbose_name = 'Авторы'
        verbose_name_plural = 'Автор'

    def __str__(self):
        return f'{self.name}'

    name = models.CharField('ФИО автора', max_length=300)
    name_en = models.CharField('ФИО автора транслитом', max_length=300)

    date_birth = models.DateField('Дата рождения')
    date_death = models.DateField('Дата смерти', null=True)

    photo = models.ImageField('Фотография', upload_to='photo_author')

    info = models.TextField('Информация')


class Artworks(models.Model):
    class Meta:
        verbose_name = 'Произведения'
        verbose_name_plural = 'Произведение'

    def __str__(self):
        return f'{self.name}'

    author = models.ManyToManyField(Author)

    name = models.CharField('Название', max_length=300)
    name_en = models.CharField('Название транслитом', max_length=300)

    date = models.CharField('Дата написания', max_length=4)

    field_1 = models.CharField('Поле 1', max_length=150)
    field_2 = models.CharField('Поле 2', max_length=150)

    file = models.FileField('Файл книги', upload_to='book/')

    genres = models.ManyToManyField(Genre)


class Status(models.TextChoices):
    NEW = 'NEW', 'Новая'
    PROCESSING = 'PROCESSING', 'В обработке'
    PROCESSED = 'PROCESSED', 'Обработана'
    POSTPONED = 'POSTPONED', 'Отложена'


class Feedback(models.Model):
    class Meta:
        verbose_name = 'Заявки'
        verbose_name_plural = 'Заявка'

    def __str__(self):
        return f'{self.status}'

    text = models.TextField('Текст обращения')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    status = models.CharField(
        'Статус заявки',
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
    )


class BookState(models.Model):
    class Meta:
        verbose_name = 'Состояния книг'
        verbose_name_plural = 'Состояние книги'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Artworks, on_delete=models.CASCADE)
    epubcfi = models.CharField('Место остановки', max_length=150)
    percent = models.IntegerField('Статус чтения', validators=(validate_percent,))

    show = models.BooleanField('Показывать', default=True)

    date_update = models.DateTimeField('Дата обновления', auto_now=True)
