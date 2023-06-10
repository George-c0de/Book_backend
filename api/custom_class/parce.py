import logging

import openpyxl
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
    def create_genres(zhanr):
        """
        Создает жанры и возвращает список их идентификаторов
        """
        genre_ids = []
        zhanr = zhanr.split(',')
        print(zhanr)
        for genre in zhanr:
            genre_obj, _ = Genre.objects.get_or_create(name=genre)
            genre_ids.append(genre_obj.id)
        return genre_ids

    def create_artwork(self, proizvedenie, god, nazvanie_fayla):
        """
        Создает произведение и возвращает объект Artworks
        """
        artwork = Artworks.objects.create(
            name=proizvedenie,
            date=god,
            file=f'/media/book/{nazvanie_fayla}.epub',
        )
        return artwork
    def parse_excel_file(self) -> list:
        """
        Функция lzk парсинга книг
        :return:
        """
        workbook = openpyxl.load_workbook(self.file_path)
        sheet = workbook.active

        for row in sheet.iter_rows(min_row=2, values_only=True):
            fio = row[0]
            proizvedenie = row[1]
            nazvanie_fayla = row[2]
            god = row[3]
            forma = row[4]
            zhanr = row[5]
            tagi = row[6]
            logging.error('start')
            if Artworks.objects.filter(name=proizvedenie).exists():
                continue

            author = self.create_author(fio)
            genres = self.create_genres(zhanr=zhanr)
            artworks = self.create_artwork(
                proizvedenie=proizvedenie,
                god = god,
                nazvanie_fayla=nazvanie_fayla,
            )
            artworks.author.add(author)
            artworks.genres.add(*genres)
            artworks.author.add(author)
        return []
