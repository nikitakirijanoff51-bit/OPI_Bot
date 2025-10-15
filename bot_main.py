import telebot

# 🔹 ВСТАВЬ свой токен от BotFather сюда (в кавычках)
BOT_TOKEN = "ВСТАВЬ_СВОЙ_ТОКЕН_ОТСЮДА"

bot = telebot.TeleBot(BOT_TOKEN)

# Основное меню
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! 👋 Это бот отдела OPI.\n\n"
                          "Здесь можно посмотреть статус готовности исследований по скважинам.\n\n"
                          "Введи /help чтобы узнать больше.")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Доступные команды:\n"
                          "/status — Степень готовности исследований по скважинам\n"
                          "/about — О проекте")

# Пример вывода статуса
@bot.message_handler(commands=['status'])
def status(message):
    data = {
        "Месторождение А": {"Скв.101": "Готово на 80%", "Скв.102": "Готово на 60%"},
        "Месторождение Б": {"Скв.45": "Готово на 100%", "Скв.46": "В процессе (40%)"},
    }

    text = "📊 *Степень готовности исследований:*\n\n"
    for field, wells in data.items():
        text += f"🏞 *{field}*\n"
        for well, progress in wells.items():
            text += f"— {well}: {progress}\n"
        text += "\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['about'])
def about(message):
    bot.reply_to(message, "Этот бот создан для сотрудников отдела OPI "
                          "для оперативного отслеживания готовности петрофизических исследований.\n\n"
                          "Разработка: внутренний проект ЛУКОЙЛ-Инжиниринг.")

# Запуск
bot.polling(non_stop=True)
