import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === Устанавливаем webhook ===
def set_webhook():
    if not BOT_TOKEN or not RENDER_EXTERNAL_URL:
        print("❌ BOT_TOKEN или RENDER_EXTERNAL_URL не заданы!")
        return
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook установлен: {success} ({webhook_url})")

# === Сразу при старте приложения ставим webhook ===
print("🚀 Настройка webhook...")
set_webhook()

# === Проверка работы ===
@app.route('/')
def index():
    return "✅ Бот запущен и слушает Telegram!"

# === Обработка обновлений от Telegram ===
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('utf-8')
        print(f"📩 Получено обновление: {json_str}")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")
    return "OK", 200

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет 👋! Бот успешно запущен и готов к работе.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Flask сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port) 
