import os
import telebot
from flask import Flask, request
import pandas as pd

# === Настройки ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

DATA_FILE = "data.xlsx"

# === Инициализация Excel ===
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Месторождение", "№ Скважины", "Статус", "Комментарий"])
    df.to_excel(DATA_FILE, index=False)

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📋 Посмотреть таблицу", "➕ Добавить запись")
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для работы с таблицей.\nВыбери действие:",
        reply_markup=markup
    )

# === Ответ на кнопки ===
@bot.message_handler(func=lambda msg: msg.text == "📋 Посмотреть таблицу")
def show_table(message):
    df = pd.read_excel(DATA_FILE)
    if df.empty:
        bot.send_message(message.chat.id, "Таблица пока пустая 🗒️")
    else:
        text = "\n\n".join([f"{row['Месторождение']} | {row['№ Скважины']} | {row['Статус']} | {row['Комментарий']}"
                            for _, row in df.iterrows()])
        bot.send_message(message.chat.id, f"📊 Таблица:\n\n{text}")

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить запись")
def add_entry(message):
    bot.send_message(message.chat.id, "✏️ Введи данные в формате:\n\nМесторождение; № Скважины; Статус; Комментарий")
    bot.register_next_step_handler(message, save_entry)

def save_entry(message):
    try:
        parts = [p.strip() for p in message.text.split(";")]
        if len(parts) != 4:
            raise ValueError
        df = pd.read_excel(DATA_FILE)
        new_row = pd.DataFrame([{
            "Месторождение": parts[0],
            "№ Скважины": parts[1],
            "Статус": parts[2],
            "Комментарий": parts[3]
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(DATA_FILE, index=False)
        bot.send_message(message.chat.id, "✅ Запись добавлена в таблицу.")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Неверный формат. Попробуй снова — через ;")

# === Flask webhook ===
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")
    return "OK", 200

@app.route('/')
def index():
    return "✅ Бот запущен и слушает Telegram!"

# === Запуск ===
if __name__ == '__main__':
    print("🚀 Настройка webhook...")
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook")
    print(f"🔗 Webhook установлен: {RENDER_EXTERNAL_URL}/webhook")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
