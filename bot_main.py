import os
import telebot
from flask import Flask, request
import pandas as pd

# === Переменные окружения ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === Excel файл ===
EXCEL_FILE = "data.xlsx"

# Если файла нет — создаём с нужными колонками
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["Месторождение", "#Скважины", "Статус выполнения", "Комментарий"])
    df.to_excel(EXCEL_FILE, index=False)
    print("📘 Создан новый файл data.xlsx")

# === /start ===
@bot.message_handler(commands=["start"])
def start_handler(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "👋 Привет! Я бот для учёта статусов скважин.\n\n"
        "Ты можешь добавить данные или посмотреть таблицу.",
    )

# === Добавление строки ===
@bot.message_handler(commands=["add"])
def add_handler(message):
    chat_id = message.chat.id
    try:
        parts = message.text.split(" ", 4)
        if len(parts) < 5:
            bot.send_message(chat_id, "⚠️ Формат: /add месторождение скважина статус комментарий")
            return

        _, mest, well, status, comment = parts
        df = pd.read_excel(EXCEL_FILE)
        df.loc[len(df)] = [mest, well, status, comment]
        df.to_excel(EXCEL_FILE, index=False)
        bot.send_message(chat_id, "✅ Запись добавлена в таблицу!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")

# === Просмотр таблицы ===
@bot.message_handler(commands=["show"])
def show_handler(message):
    chat_id = message.chat.id
    try:
        df = pd.read_excel(EXCEL_FILE)
        if df.empty:
            bot.send_message(chat_id, "Таблица пуста.")
        else:
            text = ""
            for _, row in df.iterrows():
                text += f"🏭 {row['Месторождение']} | ⛽ {row['#Скважины']} | 📊 {row['Статус выполнения']} | 💬 {row['Комментарий']}\n"
            bot.send_message(chat_id, text[:4000])
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при чтении файла: {e}")

# === Установка webhook ===
def setup_webhook():
    if not BOT_TOKEN or not RENDER_EXTERNAL_URL:
        print("❌ BOT_TOKEN или RENDER_EXTERNAL_URL не заданы!")
        return False
    bot.remove_webhook()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    result = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook установлен: {result} ({webhook_url})")
    return result

# === Главная страница ===
@app.route("/")
def index():
    return "✅ Бот запущен и слушает Telegram!"

# === Обработка webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        print(f"📩 Получено обновление (raw): {update}")
        bot.process_new_updates([update])  # 👈 теперь Telebot точно обрабатывает
        print("✅ Обновление успешно обработано")
    except Exception as e:
        print(f"❌ Ошибка при обработке webhook: {e}")
    return "OK", 200

# === Запуск приложения ===
if __name__ == "__main__":
    setup_webhook()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
