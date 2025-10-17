import os
from flask import Flask, request
import telebot

# === Настройки ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = f"https://opi-bot-1.onrender.com/{BOT_TOKEN}"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# === Обработчик команды /start ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 🤖 Бот успешно подключен к серверу и готов к работе.")

# === Обработчик всех остальных сообщений ===
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

# === Flask роут для Telegram webhook ===
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/', methods=['GET'])
def index():
    return "OPI Bot is alive!", 200

# === Установка webhook ===
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook установлен: {WEBHOOK_URL}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
