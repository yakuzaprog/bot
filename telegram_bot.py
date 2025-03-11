from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import logging
from datetime import datetime, timedelta

# Включаем логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы разговора
NAME, PHONE, TIME = range(3)

# Память о занятых слотах (в идеале — в файл/БД)
booked_slots = []

# Генерация доступных слотов
def generate_available_slots():
    now = datetime.now()
    base_date = now.date()

    if now.hour >= 18:
        base_date += timedelta(days=1)

    slots = []
    for hour in range(10, 18):
        slot_time = datetime(base_date.year, base_date.month, base_date.day, hour)
        slot_str = slot_time.strftime("%d.%m.%Y %H:%M")
        if slot_str not in booked_slots:
            slots.append(slot_str)

    # если все занято — следующий день
    if not slots:
        base_date += timedelta(days=1)
        for hour in range(10, 18):
            slot_time = datetime(base_date.year, base_date.month, base_date.day, hour)
            slot_str = slot_time.strftime("%d.%m.%Y %H:%M")
            if slot_str not in booked_slots:
                slots.append(slot_str)

    return slots

# Проверка формата времени
def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, "%d.%m.%Y %H:%M")
        return True
    except ValueError:
        return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я помогу тебе записаться на консультацию.\nВведи свое имя:")
    return NAME

# Имя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Отлично! Теперь введи свой номер телефона:")
    return PHONE

# Телефон
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()

    available_slots = generate_available_slots()
    if not available_slots:
        await update.message.reply_text("Извините, нет доступных слотов. Попробуйте позже.")
        return ConversationHandler.END

    keyboard = [available_slots[i:i+2] for i in range(0, len(available_slots), 2)]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text("Выберите удобное время:", reply_markup=reply_markup)
    return TIME

# Время
async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_time = update.message.text.strip()

    if not is_valid_time(selected_time):
        await update.message.reply_text("Формат времени неправильный. Используй: ДД.ММ.ГГГГ ЧЧ:ММ")
        return TIME

    if selected_time in booked_slots:
        await update.message.reply_text("Это время уже занято. Выберите другое.")
        return TIME

    booked_slots.append(selected_time)
    context.user_data["time"] = selected_time

    name = context.user_data["name"]
    phone = context.user_data["phone"]

    admin_chat_id = "889342057"  # ← замени на свой ID

    message = (
        f"📝 Новая запись:\n"
        f"👤 Имя: {name}\n📞 Телефон: {phone}\n🕓 Время: {selected_time}"
    )

    await context.bot.send_message(chat_id=admin_chat_id, text=message)
    await update.message.reply_text(
        "Спасибо! Ты записан(а) на консультацию.\nМы свяжемся с тобой в ближайшее время.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена. Если захочешь попробовать снова — нажми /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Запуск бота
async def main():
    # ← Вставь токен своего бота
    application = Application.builder().token("8080491480:AAGKkb3dRshthxmwv1meYaK7X7PK1kP7NOs").build()

    # Команды бота в меню Telegram
    await application.bot.set_my_commands([
        BotCommand("start", "Начать запись"),
        BotCommand("cancel", "Отменить запись"),
    ])

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("cancel", cancel))

    print("Бот запущен")
    await application.run_polling()

# Запуск
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
