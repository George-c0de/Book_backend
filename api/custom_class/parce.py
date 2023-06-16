import pandas as pd

from api.models import Author, Artworks, Genre


class ParseXML:
    """
    Класс для парсинга книг
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    @staticmethod
    def create_author(fio):
        """
        Создает автора и возвращает объект Author
        """
        author, _ = Author.objects.get_or_create(name=fio)
        return author

    @staticmethod
    def create_genres(genre):
        """
        Создает жанры и возвращает список их идентификаторов
        """
        genre_objs = []
        if isinstance(genre, str):
            genre = genre.split(',')
            for genre in genre:
                obj, _ = Genre.objects.get_or_create(name=genre)
                genre_objs.append(obj.id)
        return genre_objs

    @staticmethod
    def create_artwork(name, year, file):
        """
        Создает произведение и возвращает объект Artworks
        """
        artwork, _ = Artworks.objects.get_or_create(
            name=name,
            defaults={
                'date': year,
                'file': f'/media/book/{file}.epub',
            }
        )
        return artwork

    def parse_excel_file(self):
        """
        Функция lzk парсинга книг
        :return:
        """
        # Укажите путь к файлу Excel
        excel_file = 'Library.xlsx'

        # Укажите имя листа в файле Excel, на котором находятся данные
        sheet_name = 'Sheet1'

        # Чтение данных из Excel в объект DataFrame
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Выбор необходимых столбцов
        required_columns = [
            'ФИО Автора',
            'Наименование произведения',
            'Название файла',
            'Год',
            'Форма (Библиография)',
            'Жанр',
            'Теги',
        ]
        selected_data = df[required_columns]

        # Преобразование в массив словарей
        data_dict = selected_data.to_dict('records')

        # Вывод данных
        for item in data_dict:
            fio = item['ФИО Автора']
            name = item['Наименование произведения']
            file = item['Название файла']
            year = item['Год']
            # form = item['Форма (Библиография)']
            # tag = item['Теги']
            genre = item['Жанр']
            if Artworks.objects.filter(name=name).exists():
                continue
            author = self.create_author(fio=fio)
            genres = self.create_genres(genre=genre)
            artworks = self.create_artwork(name=name, year=year, file=file)
            artworks.author.add(author)
            artworks.genres.set(genres)

