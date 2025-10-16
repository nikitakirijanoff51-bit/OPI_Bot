# bot_main.py
import os
import telebot
from flask import Flask, request, abort

# Читаем токен и публичный URL сервиса из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVICE_URL = os.getenv("SERVICE_URL")  # например: https://opi-bot.onrender.com

if not BOT_TOKEN:
    raise RuntimeError("Error: BOT_TOKEN is not set in environment variables")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Примеры команд ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "Привет! Я бот ОПИ. Используй /help")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "Команды:\n/обновить [месторождение] [номер] [статус]\n"
                          "/коммент [месторождение] [номер] [заметка]\n"
                          "/статус [месторождение] [номер]\n"
                          "/все\n/отчет")

# Здесь должна быть логика обработки команд (взятая из твоего предыдущего кода)
# Для краткости приведём упрощённый пример, вставь свою логику чтения/записи Excel:
import pandas as pd
FILE_NAME = "opi_status.xlsx"
if not os.path.exists(FILE_NAME):
    pd.DataFrame(columns=["Месторождение","Скважина","Статус","Комментарий","Автор","Дата обновления"]).to_excel(FILE_NAME, index=False)

@bot.message_handler(commands=['все'])
def cmd_all(message):
    df = pd.read_excel(FILE_NAME)
    if df.empty:
        bot.reply_to(message, "Нет активных скважин.")
        return
    s = "Текущие статусы:\n"
    for _, row in df.iterrows():
        s += f"{row['Месторождение']} – {row['Скважина']}: {row['Статус']} ({row['Автор']}, {row['Дата обновления']})\n"
    bot.send_message(message.chat.id, s)

# --- Webhook endpoints ---
# Telegram будет POST-ить JSON на /<BOT_TOKEN>
@app.route("/" + BOT_TOKEN, methods=['POST'])
def webhook_handler():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "", 200
    else:
        abort(403)

@app.route("/", methods=['GET'])
def index():
    return "OPI bot is running."

def set_webhook():
    """Устанавливает webhook (вызвать при старте только если SERVICE_URL задан)"""
    if not SERVICE_URL:
        print("SERVICE_URL not set — webhook not configured automatically.")
        return
    webhook_url = SERVICE_URL.rstrip("/") + "/" + BOT_TOKEN
    print("Setting webhook to:", webhook_url)
    try:
        # Удалим старый webhook и установим новый
        bot.remove_webhook()
        ok = bot.set_webhook(url=webhook_url)
        print("set_webhook returned:", ok)
    except Exception as e:
        print("Error setting webhook:", e)

# Запускаем приложение
if __name__ == "__main__":
    # Сначала попытаемся установить webhook (если SERVICE_URL задан)
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
