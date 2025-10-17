import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === Устанавливаем webhook ===
def set_webhook():
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook set: {success} ({webhook_url})")

# === Проверка сервера ===
@app.route('/')
def index():
    return "✅ Бот запущен и слушает Telegram!"

# === Маршрут для Telegram webhook ===
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! 👋 Бот успешно запущен и готов к работе.")

# === Точка входа ===
if __name__ == '__main__':
    set_webhook()  # <-- Устанавливаем сразу при запуске
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
