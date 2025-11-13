
import telebot
import json
import os
from datetime import datetime
import threading
import time

# ТОКЕН ТВОЕГО БОТА — ВСТАВЬ СЮДА!
TOKEN = "7827131440:AAFpxMQeIJc3gh65JO8NYoHpfM_gZGBL4dU
"  # ← ЗАМЕНИ НА СВОЙ!
bot = telebot.TeleBot(TOKEN)

# Файл для хранения заметок
DATA_FILE = "notes.json"

# Загрузка заметок из файла
def load_notes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"notes": [], "reminders": []}

# Сохранение заметок в файл
def save_notes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загружаем данные
notes_data = load_notes()

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """
Привет! 👋 Я твой личный помощник по заметкам и делам.

Команды:
/add [текст] — добавить заметку
/notes — посмотреть все заметки
/remind [время] [текст] — поставить напоминание
/today — дела на сегодня
/help — помощь
    """)

# Команда /add
@bot.message_handler(commands=['add'])
def add_note(message):
    text = message.text[5:].strip()  # убираем "/add "
    if not text:
        bot.reply_to(message, "❌ Напиши, что нужно добавить. Например: /add Купить хлеб")
        return

    notes_data["notes"].append({
        "text": text,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "id": len(notes_data["notes"]) + 1
    })
    save_notes(notes_data)
    bot.reply_to(message, f"✅ Заметка добавлена: {text}")

# Команда /notes
@bot.message_handler(commands=['notes'])
def show_notes(message):
    if not notes_data["notes"]:
        bot.reply_to(message, "📝 У тебя пока нет заметок.")
        return

    text = "📋 Твои заметки:\n\n"
    for note in notes_data["notes"]:
        text += f"{note['id']}. {note['text']} — {note['date']}\n"
    bot.reply_to(message, text)

# Команда /remind
@bot.message_handler(commands=['remind'])
def set_reminder(message):
    text = message.text[8:].strip()  # убираем "/remind "
    if not text:
        bot.reply_to(message, "❌ Напиши время и текст. Например: /remind 18:00 Позвонить маме")
        return

    # Ищем время в формате ЧЧ:ММ
    import re
    match = re.search(r'^(\d{1,2}):(\d{2})\s+(.+)$', text)
    if not match:
        bot.reply_to(message, "❌ Формат: /remind 18:00 Позвонить маме")
        return

    hour, minute, note_text = match.groups()
    try:
        remind_time = f"{int(hour):02d}:{int(minute):02d}"
    except:
        bot.reply_to(message, "❌ Неверное время. Используй формат ЧЧ:ММ")
        return

    # Сохраняем напоминание
    notes_data["reminders"].append({
        "time": remind_time,
        "text": note_text,
        "user_id": message.from_user.id,
        "sent": False
    })
    save_notes(notes_data)

    bot.reply_to(message, f"⏰ Напоминание установлено на {remind_time}: {note_text}")

# Команда /today
@bot.message_handler(commands=['today'])
def show_today(message):
    today = datetime.now().strftime("%d.%m.%Y")
    text = f"📅 Дела на сегодня ({today}):\n\n"

    # Заметки
    notes_today = [n for n in notes_data["notes"] if today in n["date"]]
    if notes_today:
        text += "📌 Заметки:\n"
        for n in notes_today:
            text += f"  • {n['text']}\n"
    else:
        text += "📌 Заметок нет\n"

    # Напоминания
    reminders_today = [r for r in notes_data["reminders"] if r["sent"] == False]
    if reminders_today:
        text += "\n⏰ Напоминания:\n"
        for r in reminders_today:
            text += f"  • {r['time']} — {r['text']}\n"
    else:
        text += "\n⏰ Напоминаний нет\n"

    bot.reply_to(message, text)

# Функция проверки напоминаний (работает в фоне)
def check_reminders():
    while True:
        now = datetime.now().strftime("%H:%M")
        for reminder in notes_data["reminders"]:
            if reminder["time"] == now and not reminder["sent"]:
                try:
                    bot.send_message(reminder["user_id"], f"⏰ Напоминаю: {reminder['text']}")
                    reminder["sent"] = True
                    save_notes(notes_data)
                except:
                    pass
        time.sleep(60)  # Проверять каждую минуту

# Запускаем проверку напоминаний в отдельном потоке
threading.Thread(target=check_reminders, daemon=True).start()

# Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, """
Команды:
/add [текст] — добавить заметку
/notes — посмотреть все заметки
/remind ЧЧ:ММ [текст] — поставить напоминание
/today — что на сегодня
/help — помощь
    """)

# Запуск бота
print("🤖 Бот запущен...")
bot.polling(none_stop=True)
