FROM python:3.10
# Создать директорию вашего приложения.
RUN mkdir /app
RUN mkdir /app/staticfiles

# Скопировать с локального компьютера файл зависимостей
# в директорию /app.
COPY requirements.txt /app

# Выполнить установку зависимостей внутри контейнера.
RUN pip3 install -r /app/requirements.txt --no-cache-dir

# Скопировать содержимое директории /api_yamdb c локального компьютера
# в директорию /app.
COPY / /app
# Сделать директорию /app рабочей директорией.
WORKDIR /app

# copy entrypoint-prod.sh

COPY ./entrypoint.sh /app
RUN ["chmod", "+x", "./entrypoint.sh"]

CMD ["gunicorn", "Book_backend.wsgi:application", "--timeout", "5000", "--bind", "0:8000"]
ENTRYPOINT ["./entrypoint.sh"]
