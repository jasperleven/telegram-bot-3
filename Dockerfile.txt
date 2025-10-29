# Используем стабильный Python 3.11
FROM python:3.11-slim

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы
COPY . /app

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Устанавливаем переменные окружения (не секретные)
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "bot.py"]
