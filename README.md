# Dota 2 Meta Follow Bot

Асинхронный Telegram-бот для мониторинга статистики и мета-изменений в Dota 2. Построен на базе библиотеки **aiogram 3.x** с использованием данных **Stratz API**.

## 🚀 Функционал

* **Fast Meta**: Мгновенный вывод топ-10 актуальных героев на каждую из 5 игровых позиций.
* **Hero Analytics** (в разработке): Глубокий анализ статов конкретных героев.
* **Patch Digest** (в разработке): Краткая сводка изменений последнего патча.

## 🛠 Технологии

* **Language**: Python 3.10+
* **Framework**: [aiogram 3.x](https://github.com/aiogram/aiogram)
* **API**: [Stratz API](https://stratz.com/api)
* **Database**: PostgreSQL + SQLAlchemy (Async)
* **Infrastructure**: Docker, Docker Compose

## 📦 Установка и запуск

### 1. Клонирование репозитория
```bash
git clone [https://github.com/ваш_логин/dota_bot.git](https://github.com/ваш_логин/dota_bot.git)
cd dota_bot
```
### 2. Настройка переменных окружения

Создайте файл .env в корне проекта и заполните его:
```bash
BOT_TOKEN=ваш_токен_от_BotFather
STRATZ_TOKEN=ваш_токен_stratz_api
POSTGRES_DB=dota_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DB_HOST=db
```

### 3. Запуск через Docker Compose

Проект полностью контейнеризирован. Для сборки и запуска выполните:
```bash
docker-compose up -d --build
```

### 📂 Структура проекта

    bot.py — Точка входа.

    handlers/ — Обработка команд и кнопок.

    services/ — Логика запросов к Stratz API.

    models/ — Описание таблиц базы данных (SQLAlchemy).

    Dockerfile & docker-compose.yml — Конфигурация контейнеров.

### 📈 Статус разработки

    [x] Интеграция Stratz API

    [x] Функция Fast Meta (Top 10)

    [ ] Глубокая аналитика героев (Hero Analytics)

    [ ] Дайджест изменений патча (Patch Digest)