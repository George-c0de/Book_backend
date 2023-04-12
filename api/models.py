from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, PermissionsMixin
from django.db import models
from django.utils import timezone

from api.validate import validate_percent


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email: str, password: str, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.password = None
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    email = models.EmailField('Email', unique=True)

    # Установка необязательного пароля
    password = models.CharField(max_length=128)

    # ФИО
    first_name = models.CharField('Имя', max_length=150, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    patronymic = models.CharField('Отчество', max_length=150, blank=True)

    # Информация для сайта
    is_staff = models.BooleanField('Сотрудник', default=False)
    is_active = models.BooleanField('Активирован', default=True)
    is_suspended = models.BooleanField('Заблокирован', default=False)
    date_joined = models.DateTimeField('Дата регистрации', default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def change_password(self, password: str) -> bool:
        """
        Смена пароля
        :param password: новый пароль
        :return: Успешность смены пароля
        """
        try:
            self.set_password(password)
            self.save()
            return True
        except TypeError:
            return False

    def change_active(self):
        self.is_active = True
        self.save()

    def __str__(self):
        return self.email

    def is_active_user(self):
        self.is_active = True
        self.save()

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.patronymic}'


class Settings(models.Model):
    class Meta:
        verbose_name = 'Настройки пользователей'
        verbose_name_plural = 'Настройка у пользователя'

    def __str__(self):
        return f'{self.user.email}'

    percent = models.IntegerField('Яркость экрана', validators=(validate_percent,), default=50)
    size = models.IntegerField('Размер шрифта', default=16)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)


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

    info = models.TextField('Информация о книге')

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

    text = models.CharField('Текст обращения', max_length=2000)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

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

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    book = models.ForeignKey(Artworks, on_delete=models.CASCADE)
    epubcfi = models.CharField('Место остановки', max_length=150)
    percent = models.IntegerField('Статус чтения', validators=(validate_percent,))

    show = models.BooleanField('Показывать', default=True)

    date_update = models.DateTimeField('Дата обновления', auto_now=True)
