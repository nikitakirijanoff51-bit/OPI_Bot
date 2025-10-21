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
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["Месторождение", "#Скважины", "Статус выполнения", "Комментарий"])
    df.to_excel(EXCEL_FILE, index=False)
    print("📘 Создан новый файл data.xlsx")

# === Команды ===
@bot.message_handler(commands=["start"])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для учёта статусов скважин.\n"
        "Доступные команды:\n"
        "/add месторождение скважина статус комментарий\n"
        "/show — показать таблицу."
    )

@bot.message_handler(commands=["add"])
def add_handler(message):
    try:
        parts = message.text.split(" ", 4)
        if len(parts) < 5:
            bot.send_message(message.chat.id, "⚠️ Формат: /add месторождение скважина статус комментарий")
            return

        _, mest, well, status, comment = parts
        df = pd.read_excel(EXCEL_FILE)
        df.loc[len(df)] = [mest, well, status, comment]
        df.to_excel(EXCEL_FILE, index=False)
        bot.send_message(message.chat.id, "✅ Запись добавлена!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=["show"])
def show_handler(message):
    try:
        df = pd.read_excel(EXCEL_FILE)
        if df.empty:
            bot.send_message(message.chat.id, "📂 Таблица пуста.")
            return
        text = ""
        for _, row in df.iterrows():
            text += f"🏭 {row['Месторождение']} | ⛽ {row['#Скважины']} | 📊 {row['Статус выполнения']} | 💬 {row['Комментарий']}\n"
        bot.send_message(message.chat.id, text[:4000])
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при чтении: {e}")

# === Flask webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        print(f"📩 Обновление обработано: {update.message.text if update.message else 'нет message'}")
    except Exception as e:
        print(f"❌ Ошибка при обработке webhook: {e}")
    return "OK", 200

@app.route("/")
def index():
    return "✅ Бот онлайн через webhook!"

# === Установка webhook ===
def setup_webhook():
    bot.remove_webhook()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    result = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook установлен: {result} ({webhook_url})")

if __name__ == "__main__":
    setup_webhook()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
