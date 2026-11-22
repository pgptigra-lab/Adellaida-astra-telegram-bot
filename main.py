import asyncio
import logging
import os
import re
from datetime import datetime, time

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from chart import calculate_natal_chart, format_natal_chart, format_interpretations, format_aspect_interpretations, format_psychological_portrait, translate_chart_text

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
# Prevent httpx request URLs from exposing the Telegram bot token in Railway logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

UI = {
    "ru": {
        "chart": "✨ Натальная карта", "about": "ℹ️ О проекте",
        "welcome": "✨ Добро пожаловать в ASTRA! Я могу рассчитать натальную карту по дате, времени и месту рождения. Выбери действие ниже.",
        "prompt": "Пришли данные одним сообщением в таком формате:\n\nДата: 15.05.1989\nВремя: 07:30\nМесто: Кишинёв, Молдова\n\nУкажи местное время рождения. Если точное время неизвестно, полную карту с Асцендентом и домами рассчитать нельзя.",
        "about_text": "ASTRA — астрологический проект для самопознания. Расчёты и трактовки носят развлекательный и рефлексивный характер, а не являются научным описанием личности или прогнозом.",
        "choose": "Выбери действие на клавиатуре ниже или введи /chart.",
        "cancel": "Ввод отменён. Когда будешь готов(а), выбери «Натальная карта».",
        "help": "Команды:\n/start — начать заново\n/chart — создать натальную карту\n/cancel — отменить ввод\n\nДля полной карты нужны дата, точное местное время и город/страна рождения.",
        "too_long": "Сообщение слишком длинное. Пришли только дату, время и место рождения.",
        "missing_date": "дату (например, 15.05.1989)",
        "missing_time": "время (например, 07:30)",
        "missing_place": "город и страну",
        "missing_prefix": "Не хватает или не удалось распознать: ",
        "missing_suffix": ".\nПришли все три пункта одним сообщением. Для отмены введи /cancel.",
        "calculating": "🔭 Рассчитываю натальную карту. Это может занять несколько секунд.",
        "translation_error": "Не удалось перевести результат. Проверь доступность API и попробуй ещё раз позже.",
        "chart_error": "Не получилось рассчитать карту. Проверь написание города и попробуй ещё раз. Для отмены введи /cancel.",
    },
    "th": {
        "chart": "✨ แผนภูมิดวงกำเนิด", "about": "ℹ️ เกี่ยวกับ ASTRA",
        "welcome": "✨ ยินดีต้อนรับสู่ ASTRA! ฉันสามารถคำนวณแผนภูมิดวงกำเนิดจากวัน เวลา และสถานที่เกิด กรุณาเลือกเมนูด้านล่าง",
        "prompt": "ส่งข้อมูลทั้งหมดในข้อความเดียวตามรูปแบบนี้:\n\nDate: 15.05.1989\nTime: 07:30\nPlace: Bangkok, Thailand\n\nกรุณาระบุเวลาท้องถิ่น ณ สถานที่เกิด หากไม่ทราบเวลาเกิดที่แน่นอน จะไม่สามารถคำนวณลัคนาและเรือนชะตาได้",
        "about_text": "ASTRA เป็นโครงการโหราศาสตร์เพื่อการสำรวจตนเอง การตีความมีไว้เพื่อความบันเทิงและการไตร่ตรอง ไม่ใช่คำอธิบายบุคลิกภาพหรือคำทำนายที่ได้รับการพิสูจน์ทางวิทยาศาสตร์",
        "choose": "กรุณาเลือกเมนูด้านล่าง หรือพิมพ์ /chart",
        "cancel": "ยกเลิกการกรอกข้อมูลแล้ว หากพร้อม ให้เลือกเมนูแผนภูมิดวงกำเนิด",
        "help": "คำสั่ง:\n/start — เริ่มต้นใหม่\n/chart — สร้างแผนภูมิดวงกำเนิด\n/cancel — ยกเลิกการกรอกข้อมูล\n\nต้องใช้วันเกิด เวลาเกิดตามเวลาท้องถิ่นที่แน่นอน และเมือง/ประเทศที่เกิด",
        "too_long": "ข้อความยาวเกินไป กรุณาส่งเฉพาะวันเกิด เวลาเกิด และสถานที่เกิด",
        "missing_date": "วันเดือนปีเกิด (ตัวอย่าง 15.05.1989)",
        "missing_time": "เวลาเกิด (ตัวอย่าง 07:30)",
        "missing_place": "เมืองและประเทศที่เกิด",
        "missing_prefix": "ข้อมูลต่อไปนี้ยังไม่ครบหรืออ่านไม่สำเร็จ: ",
        "missing_suffix": "\nกรุณาส่งข้อมูลทั้งสามรายการในข้อความเดียว หากต้องการยกเลิก พิมพ์ /cancel",
        "calculating": "🔭 กำลังคำนวณแผนภูมิดวงกำเนิด โปรดรอสักครู่",
        "translation_error": "ขออภัย ไม่สามารถแปลผลลัพธ์ได้ในขณะนี้ กรุณาลองใหม่อีกครั้งภายหลัง",
        "chart_error": "ขออภัย ไม่สามารถคำนวณแผนภูมิได้ กรุณาตรวจสอบชื่อเมืองแล้วลองอีกครั้ง หากต้องการยกเลิก พิมพ์ /cancel",
    },
    "en": {
        "chart": "✨ Natal chart", "about": "ℹ️ About ASTRA",
        "welcome": "✨ Welcome to ASTRA! I can calculate a natal chart using your birth date, time, and place. Choose an option below.",
        "prompt": "Send all details in one message using this format:\n\nDate: 15.05.1989\nTime: 07:30\nPlace: London, UK\n\nUse the local birth time. Without an exact birth time, the Ascendant and houses cannot be calculated.",
        "about_text": "ASTRA is an astrology project for self-reflection. Its interpretations are for entertainment and reflection, not scientifically validated descriptions of personality or predictions.",
        "choose": "Choose an option below or type /chart.",
        "cancel": "Input cancelled. When ready, choose Natal chart.",
        "help": "Commands:\n/start — start again\n/chart — create a natal chart\n/cancel — cancel input\n\nA full chart requires your birth date, exact local birth time, and city/country of birth.",
        "too_long": "Your message is too long. Please send only your birth date, time, and place.",
        "missing_date": "birth date (for example, 15.05.1989)",
        "missing_time": "birth time (for example, 07:30)",
        "missing_place": "birth city and country",
        "missing_prefix": "Missing or unrecognized information: ",
        "missing_suffix": "\nPlease send all three details in one message. Type /cancel to stop.",
        "calculating": "🔭 Calculating your natal chart. This may take a few seconds.",
        "translation_error": "Sorry, I couldn't translate the result right now. Please try again later.",
        "chart_error": "I couldn't calculate the chart. Please check the spelling of the city and try again. Type /cancel to stop.",
    },
}

def language_of(context):
    return context.user_data.get("language", "ru")

def menu_for(context):
    ui = UI[language_of(context)]
    return ReplyKeyboardMarkup([[ui["chart"], ui["about"]]], resize_keyboard=True)

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
    match = re.search(r"(?:время|time|เวลา)\s*[:=\-]?\s*(\d{1,2}:\d{2})", message, re.IGNORECASE)
    if not match:
        return None
    try:
        hour, minute = map(int, match.group(1).split(":"))
        return time(hour, minute)
    except ValueError:
        return None


def parse_birth_place(message):
    match = re.search(r"(?:место|город|place|city|สถานที่|เมือง)\s*[:=\-]?\s*([^\n]+)", message, re.IGNORECASE)
    if not match:
        return None
    place = match.group(1).strip()
    if place.lower() in {"не знаю", "неизвестно", "unknown", "не указано", "ไม่ทราบ", "ไม่รู้"}:
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

    await query.edit_message_text(messages[language])
    await query.message.reply_text(UI[language]["welcome"], reply_markup=menu_for(context))
    
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(UI[language_of(context)]["help"])


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = language_of(context)
    context.user_data.clear()
    context.user_data["language"] = language
    await update.message.reply_text(UI[language]["cancel"], reply_markup=menu_for(context))

async def begin_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_birth_details"] = True
    await update.message.reply_text(UI[language_of(context)]["prompt"])

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(UI[language_of(context)]["about_text"], reply_markup=menu_for(context))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    language = language_of(context)
    ui = UI[language]
    if text in {ui["chart"], "✨ Натальная карта", "✨ แผนภูมิดวงกำเนิด", "✨ Natal chart"}:
        await begin_chart(update, context)
        return
    if text in {ui["about"], "ℹ️ О проекте", "ℹ️ เกี่ยวกับ ASTRA", "ℹ️ About ASTRA"}:
        await about(update, context)
        return
    if not context.user_data.get("awaiting_birth_details"):
        await update.message.reply_text(ui["choose"], reply_markup=menu_for(context))
        return
    if len(text) > 1200:
        await update.message.reply_text(ui["too_long"])
        return

    birth_date = parse_birth_date(text)
    birth_time = parse_birth_time(text)
    birth_place = parse_birth_place(text)
    missing = []
    if birth_date is None:
        missing.append(ui["missing_date"])
    if birth_time is None:
        missing.append(ui["missing_time"])
    if birth_place is None:
        missing.append(ui["missing_place"])
    if missing:
        await update.message.reply_text(
            ui["missing_prefix"] + ", ".join(missing) + ui["missing_suffix"]
        )
        return

    context.user_data["awaiting_birth_details"] = False
    status = await update.message.reply_text(ui["calculating"])
    try:
        result = await asyncio.to_thread(calculate_natal_chart, birth_date, birth_time, birth_place)
        answer = format_natal_chart(result, birth_date, birth_time, birth_place)
        answer += format_interpretations(result)
        answer += format_aspect_interpretations(result)
        answer += format_psychological_portrait(result)
        if language != "ru":
            try:
                answer = await asyncio.to_thread(translate_chart_text, answer, language)
            except Exception:
                logger.exception("Natal chart translation failed")
                context.user_data["awaiting_birth_details"] = True
                await update.message.reply_text(
                    ui["translation_error"], reply_markup=menu_for(context)
                )
                return
        for start in range(0, len(answer), 3900):
            await update.message.reply_text(answer[start:start + 3900], reply_markup=menu_for(context))
    except Exception as exc:
        logger.exception("Natal chart calculation failed")
        context.user_data["awaiting_birth_details"] = True
        await update.message.reply_text(
            ui["chart_error"], reply_markup=menu_for(context)
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

    # Railway runs this service as a worker. Long polling does not require
    # a public URL, webhook path, or Render-specific environment variables.
    logger.info("Starting ASTRA Telegram bot using long polling")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        poll_interval=1.0,
    )


if __name__ == "__main__":
    main()
