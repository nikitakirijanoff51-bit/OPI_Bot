import os
import telebot
from flask import Flask, request
import threading
import time

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"

# === Установка вебхука при старте ===
@app.before_first_request
def setup():
    print("🚀 Настройка webhook...")
    bot.remove_webhook()
    time.sleep(1)
    success = bot.set_webhook(url=WEBHOOK_URL)
    print(f"🔗 Webhook установлен: {success} ({WEBHOOK_URL})")


@app.route('/')
def index():
    return "✅ Бот работает на Render!"


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data(as_text=True)
        print("📩 Получено обновление от Telegram:", json_str)
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print("❌ Ошибка при обработке webhook:", e)
    return "OK", 200


@bot.message_handler(commands=['start'])
def handle_start(message):
    print(f"👤 Пользователь {message.from_user.id} запустил /start")
    bot.send_message(message.chat.id, "Привет! 👋 Я живой и работаю на Render!")


# === Keep-alive поток, чтобы Render не убивал контейнер ===
def keep_alive():
    while True:
        print("💓 Keep-alive ping...")
        time.sleep(120)  # каждые 2 минуты


if __name__ == '__main__':
    threading.Thread(target=keep_alive, daemon=True).start()
    print("🚀 Flask сервер запущен...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
