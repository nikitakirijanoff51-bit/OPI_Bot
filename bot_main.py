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
    bot.reply_to(message, "Привет 👋! OPI Bot успешно подключен к серверу и готов к работе.")

# === Обработчик всех сообщений ===
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

# === Flask роут для Telegram webhook ===
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "OPI Bot is alive!", 200

# === Установка webhook при запуске ===
@app.before_request
def before_request():
    if not hasattr(app, 'webhook_set'):
        set_webhook()
        app.webhook_set = True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
