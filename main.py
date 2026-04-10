import asyncio
import logging
import os
import socket

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy import select, desc
from api_script import update_heroes_stats, scheduler
from aiohttp import TCPConnector, ClientTimeout

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database import async_session_factory, heroes_stats, init_db, get_data

logging.basicConfig(level=logging.INFO)

# Настройка TCP-соединения с keep-alive и таймаутами
connector = TCPConnector(
    family=socket.AF_INET,
    enable_cleanup_closed=True,
    force_close=False,
)

timeout = ClientTimeout(
    total=300,
    connect=10,
    sock_read=60,
    sock_connect=10,
)

session = AiohttpSession(connector=connector, timeout=timeout)
BOT_API = os.getenv(token = "BOT_API", session=session)
bot = Bot(token=BOT_API)
dp = Dispatcher()

async def on_startup():
    await init_db()
    await get_data()
    # Запускаем планировщик
    scheduler.start()
    # Можно вызвать один раз при старте, чтобы база не была пустой сразу
    version_name, notes, heroes_names = await update_heroes_stats()
    return version_name, notes, heroes_names



@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
            [KeyboardButton(text="⚡️ Fast Meta"),KeyboardButton(text="📜 Patch Digest")],
            [KeyboardButton(text="🔍 Hero Analytics"),KeyboardButton(text="⚙️ Settings")]
        ]
    keyboard = ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True
        )
    await message.answer(
        "Hello, i am DotaMetaFollow.\nI can show you current statement of meta in dota 2",
        reply_markup=keyboard
    )


@dp.message(F.text == "⚡️ Fast Meta")
async def choose_role(message: types.Message):
    builder = ReplyKeyboardBuilder()
    # Добавляем кнопки с ролями
    roles = ["Carry ⚔️", "Mid 🔮", "Offlane 🛡", "Soft Support ⚡️", "Hard Support 🩸"]
    for role in roles:
        builder.button(text=role)

    builder.button(text="🔙 Назад")
    builder.adjust(2, 2, 1, 1)

    await message.answer(
        "Выберите позицию, чтобы узнать лучших героев:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(F.text.in_(["Carry ⚔️", "Mid 🔮", "Offlane 🛡", "Soft Support ⚡️", "Hard Support 🩸"]))
async def show_top_by_role(message: types.Message):
    btn_text = message.text
    if "Carry" in btn_text:
        selected_role = "Carry"
    elif "Mid" in btn_text:
        selected_role = "Mid"
    elif "Offlane" in btn_text:
        selected_role = "Offlane"
    elif "Soft Support" in btn_text:
        selected_role = "Soft Support"
    elif "Hard Support" in btn_text:
        selected_role = "Hard Support"
    else:
        selected_role = btn_text

    async with async_session_factory() as session:
        # Запрос к базе: фильтр по роли, сортировка по WR, лимит 5
        query = (
            select(heroes_stats)
            .where(heroes_stats.role == selected_role)
            .order_by(desc(heroes_stats.winrate))
            .limit(10)
        )

        result = await session.execute(query)
        top_heroes = result.scalars().all()

    if not top_heroes:
        await message.answer(
            f"К сожалению, данных по роли {selected_role} пока нет. "
            "Попробуйте выбрать другую или дождитесь обновления базы."
        )
        return

    # Формируем красивый ответ
    response = f"🔥 **Топ-10 героев: {message.text}**\n"
    response += "За последние 7 дней (All Brackets)\n\n"

    for i, hero in enumerate(top_heroes, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        response += f"{medal} **{hero.name}**\n└ WR: `{hero.winrate}%` \nМатчей:`{hero.matches}`\n\n"

    await message.answer(response, parse_mode="Markdown")

@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await cmd_start(message)


@dp.message(F.text == "🔍 Hero Analytics")
async def get_patch_keyboard(message: types.Message):
    buttons = [
        [KeyboardButton(text="🔎 Изменения героя")],
        [KeyboardButton(text="🌍 Глобальные изменения")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    await message.answer(
        "Выберите категорию аналитики: ",
        reply_markup=keyboard
    )

@dp.message(F.text == "🔎 Изменения героя")
def search_hero_changes(hero_id, notes):
    hero_changes = [n['text'] for n in notes if n['heroId'] == hero_id]
    if not hero_changes:
        return "В этом патче героя не трогали."
    return "• " + "\n• ".join(hero_changes)

@dp.message(F.text == "🌍 Глобальные изменения")
def get_global_changes(notes):
    # generalId: 0 - General, 1 - Map, 2 - Items и т.д.
    global_changes = [n[4] for n in notes if n[1] is None and n[2] is None]
    print(f"DEBUG: type of n is {type(notes[0])}, content: {notes[0]}")

    if not global_changes:
        return "Глобальных изменений не найдено."

    # Берем первые 10 самых важных строк, чтобы не спамить
    return "🌍 <b>Глобальные правки:</b>\n\n" + "\n\n".join(global_changes[:10])

@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await cmd_start(message)

@dp.message(F.text == "⚙️ Settings")
async def show_settings(message: types.Message):
    settings_kb = [
        [KeyboardButton(text="🌐 Change Language"), KeyboardButton(text="🏆 Rank Selection")],
        [KeyboardButton(text="⬅️ Back to Menu")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=settings_kb, resize_keyboard=True)
    await message.answer("Bot settings:", reply_markup=keyboard)

@dp.message(F.text == "⬅️ Back to Menu")
async def back_to_main(message: types.Message):
    await cmd_start(message)

@dp.message(F.text == "🌐 Change Language")
async def change_lang(message: types.Message):
    lang_kb = [
        [KeyboardButton(text="Русский 🇷🇺"), KeyboardButton(text="English 🇺🇸")],
        [KeyboardButton(text="⬅️ Back to settings")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=lang_kb, resize_keyboard=True)
    await message.answer("Choose language:", reply_markup=keyboard)

@dp.message(F.text == "Русский 🇷🇺")
async def set_lang_ru(message: types.Message):
    await message.answer("Язык изменен на русский!")
    
@dp.message(F.text == "English 🇺🇸")
async def set_lang_eng(message: types.Message):
    await message.answer("Now your language is english!")

@dp.message(F.text == "⬅️ Back to settings")
async def back_to_settings(message: types.Message):
    await show_settings(message)








async def main():
    dp.startup.register(on_startup)
    
    # Механизм переподключения при обрыве соединения
    while True:
        try:
            logging.info("Запуск бота...")
            await dp.start_polling(bot)
        except asyncio.CancelledError:
            logging.warning("Поллинг отменён")
            break
        except Exception as e:
            logging.error(f"Соединение потеряно: {e}. Переподключение через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is off")
