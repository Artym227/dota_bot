from datetime import datetime, timezone
from database import engine
import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import heroes_stats, async_session_factory
import os


STRATZ_TOKEN = os.getenv("STRATZ_API")

ROLE_MAP = {
    # Числовые ключи
    1: "Carry", 2: "Mid", 3: "Offlane", 4: "Soft Support", 5: "Hard Support",
    # Строковые числа
    "1": "Carry", "2": "Mid", "3": "Offlane", "4": "Soft Support", "5": "Hard Support",
    # Константы
    "POSITION_1": "Carry", "POSITION_2": "Mid", "POSITION_3": "Offlane",
    "POSITION_4": "Soft Support", "POSITION_5": "Hard Support",
    # Вариант с названиями линий
    "SAFE_LANE": "Carry", "MID_LANE": "Mid", "OFF_LANE": "Offlane",
    "SUPPORT_SOFT": "Soft Support", "SUPPORT_HARD": "Hard Support"
}

async def update_heroes_stats():
    try:
        print("Начинаю обновление статистики героев...")

        # 1. GraphQL запрос к STRATZ
        query = """
        {
          heroStats {
            stats(bracketBasicIds: [CRUSADER_ARCHON], groupByPosition: true) {
              heroId
              position
              matchCount
              winCount
            }
          }
          constants {
            heroes {
              id
              displayName
            }
          }
          constants {
            patchNotes {
              gameVersionId
              heroId
              itemId
              generalId
              text
            }
            gameVersions {
              id
              name
              asOfDateTime
            }
          }
        }
        """

        headers = {
            "Authorization": f"Bearer {STRATZ_TOKEN}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.stratz.com/graphql", json={'query': query}, headers=headers) as resp:
                print(f"Статус движка: {engine}")
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Ошибка API: Статус {resp.status}")
                    print(f"Ответ сервера: {error_text[:200]}")  # Печатаем кусок HTML для диагностики
                    return
                data = await resp.json()
                raw_stats = data['data']['heroStats']['stats']
                heroes_names = {h['id']: h['displayName'] for h in data['data']['constants']['heroes']}
                all_notes = data['data']['constants']['patchNotes']
                versions = data['data']['constants']['gameVersions']
                latest_version = max(versions, key=lambda x: x['id'])
                latest_id = latest_version['id']
                current_notes = [n for n in all_notes if n['gameVersionId'] == latest_id]
                version_name = latest_version['name']
                notes = current_notes

        # 2. Запись в базу данных
        async with async_session_factory() as db_session:
            await db_session.execute(delete(heroes_stats))
            print(f"DEBUG: Получено героев из API: {len(raw_stats)}")

            for s in raw_stats:
                pos_id = s.get('position')
                # Теперь pos_id НЕ будет None!
                role_name = ROLE_MAP.get(pos_id)

                if not role_name:
                    continue

                matches = s.get('matchCount', 0)
                if matches < 1000: continue

                wins = s.get('winCount', 0)
                wr = round((wins / matches * 100), 2)
                h_name = heroes_names.get(s['heroId'], f"Hero {s['heroId']}")


                db_session.add(heroes_stats(
                    name=h_name,
                    winrate=wr,
                    role=role_name,
                    matches = matches

                ))

            await db_session.commit()
            print("✅ Успешно обновлено!")
    except Exception as e:
        print(f"❌ Критическая ошибка при обновлении мета-данных: {e}")
    print("DEBUG: Коммит завершен")
    return notes, version_name, heroes_names

# 3. Настройка планировщика
scheduler = AsyncIOScheduler()
# Запускать каждый день в 03:00 ночи
scheduler.add_job(update_heroes_stats, "cron", hour=3, minute=0)