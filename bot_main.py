# bot_main.py
import os
import sqlite3
import pandas as pd
import time
from flask import Flask, request
import telebot

# --- Настройки ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")  # например https://opi-bot-1.onrender.com

if not BOT_TOKEN or not RENDER_EXTERNAL_URL:
    raise RuntimeError("Не заданы переменные окружения BOT_TOKEN или RENDER_EXTERNAL_URL")

DB_FILE = "data.db"
EXPORT_FILE = "export.xlsx"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ------------------ Работа с БД ------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field TEXT,
            well TEXT UNIQUE,
            status TEXT,
            comment TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_record(field, well, status, comment):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("INSERT INTO wells (field, well, status, comment, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (field, well, status, comment, now))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, str(e)
    finally:
        conn.close()

def update_record(well, status, comment):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("SELECT id FROM wells WHERE well = ?", (well,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Скважина не найдена"
    cur.execute("UPDATE wells SET status = ?, comment = ?, updated_at = ? WHERE well = ?",
                (status, comment, now, well))
    conn.commit()
    conn.close()
    return True, None

def read_all():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT field, well, status, comment, updated_at FROM wells ORDER BY field, well", conn)
    conn.close()
    return df

def get_fields():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT field FROM wells")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

def get_wells_list():
    df = read_all()
    return df

def export_to_excel(path=EXPORT_FILE):
    df = read_all()
    df.to_excel(path, index=False)
    return path

# ------------------ Инициализация ------------------
init_db()

# Вставим пример данных, если таблица пустая (опционально)
if read_all().shape[0] == 0:
    add_record("Северное", "С-101", "В работе", "Первичная гидроразработка")
    add_record("Южное", "Ю-204", "Завершено", "РК проведён")
    add_record("Восточное", "В-301", "Планируется", "Подготовка площадки")

# ------------------ Webhook setup ------------------
def set_webhook():
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    bot.remove_webhook()
    success = bot.set_webhook(url=webhook_url)
    print(f"🔗 Webhook установлен: {success} ({webhook_url})")

# Ставим webhook при старте процесса
print("🚀 Установка webhook...")
set_webhook()

# ------------------ Flask endpoints ------------------
@app.route("/", methods=["GET"])
def index():
    return "✅ OPI Bot (SQLite) running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        print("📩 Получено обновление:", json_str)
        update = telebot.types.Update.de_json(json_str)
        # Если это сообщение — обработаем
        if getattr(update, "message", None):
            # иногда нужно напрямую передать message для корректной обработки handler'ов
            bot.process_new_messages([update.message])
    except Exception as e:
        print("❌ Ошибка обработки webhook:", e)
    return "OK", 200

# ------------------ Bot handlers ------------------
@bot.message_handler(commands=["start"])
def cmd_start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📍 Месторождения", "🛢 Скважины")
    markup.row("➕ Добавить", "✏️ Обновить")
    markup.row("/export", "/help")
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! Выбери действие:", reply_markup=markup)

@bot.message_handler(commands=["help"])
def cmd_help(message):
    help_text = (
        "Команды:\n"
        "/add <Месторождение>|<№_Скважины>|<Статус>|<Комментарий> - добавить скважину\n"
        "/update <№_Скважины>|<Статус>|<Комментарий> - обновить\n"
        "/export - экспорт в Excel\n\n"
        "Или используй кнопки: 📍 Месторождения / 🛢 Скважины / ➕ Добавить / ✏️ Обновить"
    )
    bot.send_message(message.chat.id, help_text)

# кнопки-обработчик
@bot.message_handler(func=lambda m: m.text in ["📍 Месторождения", "🛢 Скважины", "➕ Добавить", "✏️ Обновить"])
def handle_buttons(message):
    text = message.text
    if text == "📍 Месторождения":
        fields = get_fields()
        if not fields:
            bot.send_message(message.chat.id, "Нет данных.")
            return
        reply = "📍 Месторождения:\n" + "\n".join(f"- {f}" for f in fields)
        bot.send_message(message.chat.id, reply)
    elif text == "🛢 Скважины":
        df = get_wells_list()
        if df.empty:
            bot.send_message(message.chat.id, "Нет данных.")
            return
        lines = []
        for _, row in df.iterrows():
            lines.append(f"🛢 {row['well']} ({row['field']})\nСтатус: {row['status']}\nКомментарий: {row['comment']}\n")
        bot.send_message(message.chat.id, "\n".join(lines))
    elif text == "➕ Добавить":
        bot.send_message(message.chat.id, "Для добавления воспользуйся командой:\n/add Месторождение|№_Скважины|Статус|Комментарий")
    elif text == "✏️ Обновить":
        bot.send_message(message.chat.id, "Для обновления воспользуйся командой:\n/update №_Скважины|Новый_Статус|Новый_Комментарий")

@bot.message_handler(commands=["add"])
def cmd_add(message):
    # формат: /add Поле|Скважина|Статус|Комментарий
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Неверный формат. Пример:\n/add Северное|С-101|В работе|Комментарий")
            return
        fields = parts[1].split("|", 3)
        if len(fields) < 4:
            bot.send_message(message.chat.id, "Неверный формат. Нужно 4 поля, разделённых '|'.")
            return
        field, well, status, comment = [s.strip() for s in fields]
        ok, err = add_record(field, well, status, comment)
        if ok:
            bot.send_message(message.chat.id, f"✅ Скважина {well} добавлена в месторождение {field}.")
        else:
            bot.send_message(message.chat.id, f"❌ Не удалось добавить: {err}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка: {e}")

@bot.message_handler(commands=["update"])
def cmd_update(message):
    # формат: /update С-101|НовыйСтатус|НовыйКомментарий
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Неверный формат. Пример:\n/update С-101|Завершено|Комментарий")
            return
        fields = parts[1].split("|", 2)
        if len(fields) < 3:
            bot.send_message(message.chat.id, "Неверный формат. Нужно 3 поля, разделённых '|'.")
            return
        well, status, comment = [s.strip() for s in fields]
        ok, err = update_record(well, status, comment)
        if ok:
            bot.send_message(message.chat.id, f"✅ Данные по {well} обновлены.")
        else:
            bot.send_message(message.chat.id, f"❌ Не удалось обновить: {err}")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка: {e}")

@bot.message_handler(commands=["export"])
def cmd_export(message):
    try:
        path = export_to_excel()
        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка экспорта: {e}")

# Отлов любых других сообщений
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "Не понял. Воспользуйтесь /help или кнопками.")

# ------------------ Запуск Flask (и бот работает через webhook) ------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Flask server starting, webhook should be already set.")
    app.run(host="0.0.0.0", port=port)
