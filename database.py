from sqlalchemy import create_engine, Column, Integer, String, Float, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os


# 1. Настройка подключения
engine = create_async_engine(os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"), echo=True, pool_recycle=3600, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# 2. Создаем базовый класс для моделей
class Base(DeclarativeBase):
    pass

# 3. Описываем таблицу через класс
class heroes_stats(Base):
    __tablename__ = "heroes_stats"

    id = Column(Integer, primary_key=True) # hero id from stratz
    name = Column(String)
    winrate = Column(Float)
    role_data = Column(JSON)
    best_facet = Column(String)
    core_items = Column(JSON)
    role = Column(String)
    matches = Column(Integer)


class users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True) #telegram id
    language = Column(String, default="eng")
    rank = Column(String, nullable=True)


# 4. Создаем таблицы в самой базе данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print(f"Создаю таблицы: {Base.metadata.tables.keys()}")
        print(f"DEBUG: Список таблиц для создания: {Base.metadata.tables.keys()}")
        await conn.run_sync(Base.metadata.create_all)


# 5. Создаем сессию (инструмент для работы с данными)
async def get_data():
    async with async_session_factory() as session:
        pass