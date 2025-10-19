import os
from flask import Flask, request
import telebot

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

# === Инициализация бота после Flask ===
bot = telebot.TeleBot(BOT_TOKEN)
webhook_set = False


# === Устанавливаем webhook ===
def set_webhook():
    global webhook_set
    if not BOT_TOKEN or not RENDER_EXTERNAL_URL:
        print("❌ BOT_TOKEN или RENDER_EXTERNAL_URL не заданы!")
        return
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook set: {success} ({webhook_url})")
    webhook_set = True


@app.before_request
def before_request():
    global webhook_set
    if not webhook_set:
        print("🚀 Первичная инициализация, ставим webhook...")
        set_webhook()


# === Проверка доступности сервера ===
@app.route('/')
def index():
    return "✅ Бот запущен и слушает Telegram!"


# === Обработка запросов Telegram ===
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data(as_text=True)
        print("📩 Получено обновление от Telegram:", json_str)

        update = telebot.types.Update.de_json(json_str)

        if update.message:  # <-- Явная обработка
            bot.process_new_messages([update.message])

    except Exception as e:
        print("❌ Ошибка при обработке webhook:", e)

    return "OK", 200


# === Обработка команды /start ===
@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"👤 Пользователь {message.from_user.id} запустил /start")
    bot.send_message(message.chat.id, "Привет! 👋 Бот успешно запущен и готов к работе.")


if __name__ == '__main__':
    print("🚀 Starting bot server...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
