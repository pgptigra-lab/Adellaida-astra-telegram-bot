import asyncio
import logging
import os
import re
from datetime import datetime, time

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from chart import calculate_natal_chart, format_natal_chart, format_interpretations, format_aspect_interpretations, format_psychological_portrait

LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "th": "🇹🇭 ไทย",
    "en": "🇬🇧 English",
}

TEXTS = {
    "ru": "Выбери язык:",
    "th": "กรุณาเลือกภาษา:",
    "en": "Please choose your language:",
}
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MENU = ReplyKeyboardMarkup([["✨ Натальная карта", "ℹ️ О проекте"]], resize_keyboard=True)

WELCOME = (
    "✨ Добро пожаловать в ASTRA — пространство астрологии и самопознания.\n\n"
    "Я могу рассчитать астрологическую натальную карту по дате, времени и месту рождения. "
    "Для начала нажми «Натальная карта»."
)


def parse_birth_date(message):
    patterns = [
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        values = [int(value) for value in match.groups()]
        try:
            if len(match.group(1)) == 4:
                return datetime(values[0], values[1], values[2]).date()
            return datetime(values[2], values[1], values[0]).date()
        except ValueError:
            return None
    return None


def parse_birth_time(message):
    match = re.search(r"(?:время|time)\s*[:=\-]?\s*(\d{1,2}:\d{2})", message, re.IGNORECASE)
    if not match:
        return None
    try:
        hour, minute = map(int, match.group(1).split(":"))
        return time(hour, minute)
    except ValueError:
        return None


def parse_birth_place(message):
    match = re.search(r"(?:место|город|place|city)\s*[:=\-]?\s*([^\n]+)", message, re.IGNORECASE)
    if not match:
        return None
    place = match.group(1).strip()
    if place.lower() in {"не знаю", "неизвестно", "unknown", "не указано"}:
        return None
    return place[:160]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇹🇭 ไทย", callback_data="lang_th")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выбери язык / Choose language / เลือกภาษา:",
        reply_markup=reply_markup
    )

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    language = query.data.replace("lang_", "")
    context.user_data["language"] = language

    messages = {
        "ru": "🇷🇺 Отлично! Язык выбран. Добро пожаловать в ASTRA!",
        "th": "🇹🇭 ยินดีต้อนรับสู่ ASTRA! เลือกภาษาไทยแล้ว",
        "en": "🇬🇧 Welcome to ASTRA! English selected.",
    }

    await query.edit_message_text(messages[language])async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n/start — начать заново\n/chart — создать натальную карту\n"
        "/cancel — отменить ввод\n\n"
        "Для полной карты нужны дата, точное местное время и город/страна рождения."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Ввод отменён. Когда будешь готов(а), нажми «Натальная карта».",
        reply_markup=MENU,
    )


async def begin_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_birth_details"] = True
    await update.message.reply_text(
        "Пришли данные одним сообщением в таком формате:\n\n"
        "Дата: 15.05.1989\n"
        "Время: 07:30\n"
        "Место: Кишинёв, Молдова\n\n"
        "Укажи местное время рождения. Если точное время неизвестно, полную карту "
        "с Асцендентом и домами рассчитать нельзя. Не отправляй личные документы или адрес."
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ASTRA — астрологический проект для самопознания. Расчёты показывают положения "
        "небесных тел; астрологические трактовки носят развлекательный и рефлексивный "
        "характер и не являются научно подтверждённым описанием личности или прогнозом."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if text == "✨ Натальная карта":
        await begin_chart(update, context)
        return
    if text == "ℹ️ О проекте":
        await about(update, context)
        return
    if not context.user_data.get("awaiting_birth_details"):
        await update.message.reply_text("Выбери действие на клавиатуре ниже или введи /chart.", reply_markup=MENU)
        return
    if len(text) > 1200:
        await update.message.reply_text("Сообщение слишком длинное. Пришли только дату, время и место рождения.")
        return

    birth_date = parse_birth_date(text)
    birth_time = parse_birth_time(text)
    birth_place = parse_birth_place(text)
    missing = []
    if birth_date is None:
        missing.append("дату (например, 15.05.1989)")
    if birth_time is None:
        missing.append("время (например, 07:30)")
    if birth_place is None:
        missing.append("город и страну")
    if missing:
        await update.message.reply_text(
            "Не хватает или не удалось распознать: " + ", ".join(missing) +
            ".\nПришли все три пункта одним сообщением. Для отмены введи /cancel."
        )
        return

    context.user_data["awaiting_birth_details"] = False
    status = await update.message.reply_text("🔭 Рассчитываю натальную карту. Это может занять несколько секунд.")
    try:
        result = await asyncio.to_thread(calculate_natal_chart, birth_date, birth_time, birth_place)
        answer = format_natal_chart(result, birth_date, birth_time, birth_place)
        answer += format_interpretations(result)
        answer += format_aspect_interpretations(result)
        answer += format_psychological_portrait(result)
        for start in range(0, len(answer), 3900):
            await update.message.reply_text(answer[start:start + 3900], reply_markup=MENU)
    except Exception as exc:
        logger.exception("Natal chart calculation failed")
        context.user_data["awaiting_birth_details"] = True
        await update.message.reply_text(
            f"Не получилось рассчитать карту: {exc}\n"
            "Проверь написание города и попробуй ещё раз. Для отмены введи /cancel.",
            reply_markup=MENU,
        )
    finally:
        try:
            await status.delete()
        except Exception:
            pass


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_language, pattern="^lang_"))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", begin_chart))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("ASTRA bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
