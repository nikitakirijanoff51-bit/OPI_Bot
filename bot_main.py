import os
import telebot
from flask import Flask, request
import threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# === Настройка webhook ===
def set_webhook():
    if not BOT_TOKEN or not RENDER_EXTERNAL_URL:
        print("❌ BOT_TOKEN или RENDER_EXTERNAL_URL не заданы!")
        return
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook установлен: {success} ({webhook_url})")

# === Выставляем webhook при старте ===
print("🚀 Настройка webhook...")
set_webhook()

# === Проверка работы ===
@app.route('/')
def index():
    return "✅ Бот запущен и слушает Telegram!"

# === Обработка входящих обновлений ===
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        print(f"📩 Получено обновление: {json_str}")
        bot.process_new_updates([update])
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")
    return "OK", 200

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"➡️ Получена команда /start от пользователя {message.from_user.id}")
    try:
        bot.send_message(message.chat.id, "Привет 👋! Бот успешно запущен и готов к работе.")
    except Exception as e:
        print(f"⚠️ Ошибка при отправке сообщения: {e}")

# === Отдельный поток для стабильной работы с Telegram ===
def run_bot():
    print("🧵 Запуск потока обработки сообщений...")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)

threading.Thread(target=run_bot, daemon=True).start()

# === Запуск Flask ===
if __name__ == '__main__':
    print("🚀 Flask сервер запущен...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
