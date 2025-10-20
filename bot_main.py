import os
import telebot
from telebot import types
from flask import Flask, request
import pandas as pd

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

EXCEL_FILE = "data.xlsx"

# --- Проверка/создание файла Excel ---
def init_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["Месторождение", "№ Скважины", "Статус выполнения", "Комментарий"])
        df.to_excel(EXCEL_FILE, index=False)

def read_excel():
    return pd.read_excel(EXCEL_FILE)

def write_excel(df):
    df.to_excel(EXCEL_FILE, index=False)

init_excel()


# --- Кнопки ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📋 Показать данные"),
               types.KeyboardButton("➕ Добавить запись"),
               types.KeyboardButton("✏️ Изменить запись"))
    return markup


# --- Команда /start ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋\nЯ бот для ведения данных по месторождениям.\nВыберите действие:",
        reply_markup=main_keyboard()
    )


# --- Показать данные ---
@bot.message_handler(func=lambda msg: msg.text == "📋 Показать данные")
def show_data(message):
    df = read_excel()
    if df.empty:
        bot.send_message(message.chat.id, "📂 В таблице пока нет данных.")
        return
    text = "📊 *Текущие данные:*\n\n"
    for _, row in df.iterrows():
        text += f"🏞️ {row['Месторождение']}\n🔹 Скважина: {row['№ Скважины']}\n" \
                f"⚙️ Статус: {row['Статус выполнения']}\n💬 Комментарий: {row['Комментарий']}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# --- Добавление записи ---
@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить запись")
def add_record_start(message):
    bot.send_message(message.chat.id, "Введите *месторождение*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, add_field_well)


def add_field_well(message):
    user_data = {"Месторождение": message.text}
    bot.send_message(message.chat.id, "Введите *номер скважины*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, add_field_status, user_data)


def add_field_status(message, user_data):
    user_data["№ Скважины"] = message.text
    bot.send_message(message.chat.id, "Введите *статус выполнения*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, add_field_comment, user_data)


def add_field_comment(message, user_data):
    user_data["Статус выполнения"] = message.text
    bot.send_message(message.chat.id, "Введите *комментарий*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_record, user_data)


def save_record(message, user_data):
    user_data["Комментарий"] = message.text
    df = read_excel()
    df = pd.concat([df, pd.DataFrame([user_data])], ignore_index=True)
    write_excel(df)
    bot.send_message(message.chat.id, "✅ Запись успешно добавлена!", reply_markup=main_keyboard())


# --- Изменение записи ---
@bot.message_handler(func=lambda msg: msg.text == "✏️ Изменить запись")
def edit_record_start(message):
    df = read_excel()
    if df.empty:
        bot.send_message(message.chat.id, "❗ Таблица пуста, нечего изменять.")
        return
    text = "Выберите номер строки для изменения (начиная с 1):\n\n"
    for i, row in df.iterrows():
        text += f"{i+1}) {row['Месторождение']} – {row['№ Скважины']}\n"
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, edit_field_select)


def edit_field_select(message):
    try:
        index = int(message.text) - 1
        df = read_excel()
        if index < 0 or index >= len(df):
            raise ValueError
        bot.send_message(message.chat.id, "Введите новое значение *статуса выполнения*:", parse_mode="Markdown")
        bot.register_next_step_handler(message, edit_save, index)
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Неверный номер. Попробуйте снова.")


def edit_save(message, index):
    df = read_excel()
    df.loc[index, "Статус выполнения"] = message.text
    write_excel(df)
    bot.send_message(message.chat.id, "✅ Запись обновлена!", reply_markup=main_keyboard())


# --- Webhook для Render ---
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data(as_text=True)
        print("📩 Получено обновление (raw):", json_str)
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print("❌ Ошибка обработки webhook:", repr(e))
    return "OK", 200


# --- Главная страница (проверка) ---
@app.route('/')
def index():
    return "Бот работает 🚀"


# --- Основной запуск ---
if __name__ == "__main__":
    print("🚀 Настройка webhook...")
    bot.remove_webhook()
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    success = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook установлен: {success} ({webhook_url})")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
