# Используем легкий образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /bot

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# Команда запуска бота
CMD ["python", "main.py"]