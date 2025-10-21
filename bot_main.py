import os
import telebot
from telebot import types
from flask import Flask, request
import pandas as pd

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("SERVICE_URL")
EXCEL_FILE = "data.xlsx"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

# === Подготовка Excel-файла ===
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["Месторождение", "#Скважины", "Статус", "Комментарий"])
        df.to_excel(EXCEL_FILE, index=False)
        print("📘 Создан новый файл data.xlsx")
    else:
        print("📗 Файл Excel найден")

init_excel()

# === Flask Webhook ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        if not json_data:
            print("⚠️ Пустой JSON от Telegram")
            return "no data", 400

        print(f"📩 Получено обновление (raw): {json_data}")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        print("✅ Обновление успешно обработано")

    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {e}")

    return "OK", 200

# === Команда /start ===
@bot.message_handler(commands=["start"])
def start(message):
    print(f"➡️ Получена команда /start от пользователя {message.chat.id}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Посмотреть таблицу", "➕ Добавить запись", "✏️ Изменить запись")
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

# === Показать таблицу ===
@bot.message_handler(func=lambda msg: msg.text == "📊 Посмотреть таблицу")
def show_table(message):
    try:
        df = pd.read_excel(EXCEL_FILE)
        if df.empty:
            bot.send_message(message.chat.id, "Таблица пока пуста.")
            return
        text = "\n\n".join([f"🏭 {r['Месторождение']}\n🔩 {r['#Скважины']}\n📋 {r['Статус']}\n💬 {r['Комментарий']}" for _, r in df.iterrows()])
        bot.send_message(message.chat.id, f"📄 Таблица:\n\n{text}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при чтении файла: {e}")

# === Добавить запись ===
@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить запись")
def add_entry(message):
    bot.send_message(message.chat.id, "Введите данные в формате:\nМесторождение; #Скважины; Статус; Комментарий")
    bot.register_next_step_handler(message, save_entry)

def save_entry(message):
    try:
        data = [x.strip() for x in message.text.split(";")]
        if len(data) != 4:
            bot.send_message(message.chat.id, "Ошибка формата. Используй 4 значения через `;`.")
            return
        df = pd.read_excel(EXCEL_FILE)
        new_row = {"Месторождение": data[0], "#Скважины": data[1], "Статус": data[2], "Комментарий": data[3]}
        df.loc[len(df)] = new_row
        df.to_excel(EXCEL_FILE, index=False)
        bot.send_message(message.chat.id, "✅ Запись добавлена!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

# === Изменить запись ===
@bot.message_handler(func=lambda msg: msg.text == "✏️ Изменить запись")
def edit_entry(message):
    bot.send_message(message.chat.id, "Введите номер строки и новые данные:\nНомер; Месторождение; #Скважины; Статус; Комментарий")
    bot.register_next_step_handler(message, update_entry)

def update_entry(message):
    try:
        data = [x.strip() for x in message.text.split(";")]
        if len(data) != 5:
            bot.send_message(message.chat.id, "Ошибка формата. Используй 5 значений через `;`.")
            return
        idx = int(data[0]) - 1
        df = pd.read_excel(EXCEL_FILE)
        if idx < 0 or idx >= len(df):
            bot.send_message(message.chat.id, "Неверный номер строки.")
            return
        df.iloc[idx] = {"Месторождение": data[1], "#Скважины": data[2], "Статус": data[3], "Комментарий": data[4]}
        df.to_excel(EXCEL_FILE, index=False)
        bot.send_message(message.chat.id, "✏️ Запись обновлена!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

# === Главная страница (Render Ping) ===
@app.route("/", methods=["GET"])
def index():
    return "Бот работает 🟢", 200

# === Настройка webhook ===
def setup_webhook():
    if RENDER_URL and BOT_TOKEN:
        webhook_url = f"{RENDER_URL}/webhook"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"🔗 Webhook установлен: {webhook_url}")
    else:
        print("⚠️ Ошибка: переменные окружения не заданы")

import threading
import time

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    setup_webhook()
    print("🚀 Запуск Flask + TeleBot...")

    # Отдельный поток для Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Основной цикл для Telebot — чтобы активировать обработчики
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Ошибка в polling цикле: {e}")
            time.sleep(5)
