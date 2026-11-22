import asyncio
import logging
import os
import re
from datetime import datetime, time

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from chart import calculate_natal_chart
from localization import format_localized_chart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

TEXT = {
    "th": {
        "menu_chart": "✨ สร้างแผนภูมิดวงกำเนิด", "menu_about": "ℹ️ เกี่ยวกับ ASTRA",
        "welcome": "✨ ยินดีต้อนรับสู่ ASTRA\n\nฉันจะช่วยคำนวณแผนภูมิดวงกำเนิดจากวัน เวลา และสถานที่เกิด\n\nกด «สร้างแผนภูมิดวงกำเนิด» เพื่อเริ่มต้น",
        "help": "คำสั่ง:\n/start — เริ่มต้นใหม่\n/chart — สร้างแผนภูมิดวงกำเนิด\n/thai — ใช้ภาษาไทย\n/english — เปลี่ยนเป็นภาษาอังกฤษ\n/cancel — ยกเลิก",
        "cancel": "ยกเลิกการกรอกข้อมูลแล้ว หากพร้อมเมื่อไร กด «สร้างแผนภูมิดวงกำเนิด»",
        "prompt": "ส่งข้อมูลทั้งสามรายการในข้อความเดียวตามรูปแบบนี้:\n\nDate: 15.05.1989\nTime: 07:30\nPlace: Bangkok, Thailand\n\nโปรดใช้เวลาท้องถิ่น ณ สถานที่เกิด หากไม่ทราบเวลาเกิดที่แน่นอน จะไม่สามารถคำนวณลัคนาและเรือนชะตาได้ โปรดอย่าส่งเอกสารส่วนตัวหรือที่อยู่บ้าน",
        "about": "ASTRA เป็นโครงการโหราศาสตร์เพื่อการสำรวจตนเอง การตีความเป็นเชิงสัญลักษณ์เพื่อความบันเทิงและการไตร่ตรอง ไม่ใช่ข้อเท็จจริงทางวิทยาศาสตร์หรือคำทำนายที่รับประกันผล",
        "choose": "เลือกคำสั่งจากเมนูด้านล่าง หรือพิมพ์ /chart",
        "long": "ข้อความยาวเกินไป โปรดส่งเฉพาะวัน เวลา และสถานที่เกิด",
        "missing": "ข้อมูลไม่ครบหรืออ่านไม่เข้าใจ: {items}\nโปรดส่งข้อมูลทั้งสามรายการในข้อความเดียว ใช้ /cancel เพื่อยกเลิก",
        "calculating": "🔭 กำลังคำนวณแผนภูมิดวงกำเนิด โปรดรอสักครู่...",
        "error": "ไม่สามารถคำนวณดวงได้: {error}\nโปรดตรวจสอบการสะกดชื่อเมืองแล้วลองอีกครั้ง ใช้ /cancel เพื่อยกเลิก",
    },
    "en": {
        "menu_chart": "✨ Create natal chart", "menu_about": "ℹ️ About ASTRA",
        "welcome": "✨ Welcome to ASTRA\n\nI can calculate a natal chart using your birth date, time, and place.\n\nPress «Create natal chart» to begin.",
        "help": "Commands:\n/start — start again\n/chart — create a natal chart\n/thai — switch to Thai\n/english — switch to English\n/cancel — cancel",
        "cancel": "Input cancelled. Press «Create natal chart» whenever you're ready.",
        "prompt": "Send all three details in one message using this format:\n\nDate: 15.05.1989\nTime: 07:30\nPlace: Bangkok, Thailand\n\nUse the local time at your place of birth. Without an accurate birth time, the Ascendant and houses cannot be calculated. Do not send identity documents or your home address.",
        "about": "ASTRA is an astrology project for self-reflection. Interpretations are symbolic and intended for entertainment and reflection; they are not scientifically established facts or guaranteed predictions.",
        "choose": "Choose an action below or enter /chart.",
        "long": "Message too long. Send only your birth date, time, and place.",
        "missing": "Missing or unrecognized: {items}\nSend all three details in one message. Enter /cancel to stop.",
        "calculating": "🔭 Calculating your natal chart. This may take a few seconds...",
        "error": "Could not calculate the chart: {error}\nCheck the city spelling and try again. Enter /cancel to stop.",
    },
}

def language(context):
    return context.user_data.get("language", "th")

def menu_for(context):
    t = TEXT[language(context)]
    return ReplyKeyboardMarkup([[t["menu_chart"], t["menu_about"]]], resize_keyboard=True)

def parse_birth_date(message):
    patterns = [r"(\\d{4})-(\\d{1,2})-(\\d{1,2})", r"(\\d{1,2})[./-](\\d{1,2})[./-](\\d{4})"]
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
    match = re.search(r"(?:time|เวลา)\\s*[:=\\-]?\\s*(\\d{1,2}:\\d{2})", message, re.IGNORECASE)
    if not match:
        return None
    try:
        hour, minute = map(int, match.group(1).split(":"))
        return time(hour, minute)
    except ValueError:
        return None

def parse_birth_place(message):
    match = re.search(r"(?:place|city|สถานที่|เมือง)\\s*[:=\\-]?\\s*([^\\n]+)", message, re.IGNORECASE)
    if not match:
        return None
    place = match.group(1).strip()
    if place.lower() in {"unknown", "ไม่ทราบ", "ไม่ระบุ"}:
        return None
    return place[:160]

async def set_language(update, context, lang):
    context.user_data["language"] = lang
    context.user_data.pop("awaiting_birth_details", None)
    t = TEXT[lang]
    await update.message.reply_text(t["welcome"], reply_markup=menu_for(context))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["language"] = "th"
    await update.message.reply_text(TEXT["th"]["welcome"], reply_markup=menu_for(context))

async def thai(update, context):
    await set_language(update, context, "th")

async def english(update, context):
    await set_language(update, context, "en")

async def help_command(update, context):
    await update.message.reply_text(TEXT[language(context)]["help"], reply_markup=menu_for(context))

async def cancel(update, context):
    context.user_data.pop("awaiting_birth_details", None)
    await update.message.reply_text(TEXT[language(context)]["cancel"], reply_markup=menu_for(context))

async def begin_chart(update, context):
    context.user_data["awaiting_birth_details"] = True
    await update.message.reply_text(TEXT[language(context)]["prompt"], reply_markup=menu_for(context))

async def about(update, context):
    await update.message.reply_text(TEXT[language(context)]["about"], reply_markup=menu_for(context))

async def handle_text(update, context):
    text = (update.message.text or "").strip()
    lang = language(context)
    t = TEXT[lang]
    if text == t["menu_chart"]:
        await begin_chart(update, context)
        return
    if text == t["menu_about"]:
        await about(update, context)
        return
    if not context.user_data.get("awaiting_birth_details"):
        await update.message.reply_text(t["choose"], reply_markup=menu_for(context))
        return
    if len(text) > 1200:
        await update.message.reply_text(t["long"])
        return

    birth_date = parse_birth_date(text)
    birth_time = parse_birth_time(text)
    birth_place = parse_birth_place(text)
    missing = []
    if birth_date is None:
        missing.append("วันเกิด (เช่น 15.05.1989)" if lang == "th" else "birth date (e.g. 15.05.1989)")
    if birth_time is None:
        missing.append("เวลาเกิด (เช่น 07:30)" if lang == "th" else "birth time (e.g. 07:30)")
    if birth_place is None:
        missing.append("เมืองและประเทศ" if lang == "th" else "city and country")
    if missing:
        await update.message.reply_text(t["missing"].format(items=", ".join(missing)))
        return

    context.user_data["awaiting_birth_details"] = False
    status = await update.message.reply_text(t["calculating"])
    try:
        result = await asyncio.to_thread(calculate_natal_chart, birth_date, birth_time, birth_place)
        answer = format_localized_chart(result, birth_date, birth_time, birth_place, lang)
        for offset in range(0, len(answer), 3900):
            await update.message.reply_text(answer[offset:offset + 3900], reply_markup=menu_for(context))
    except Exception as exc:
        logger.exception("Natal chart calculation failed")
        context.user_data["awaiting_birth_details"] = True
        await update.message.reply_text(t["error"].format(error=str(exc)), reply_markup=menu_for(context))
    finally:
        try:
            await status.delete()
        except Exception:
            pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", begin_chart))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("thai", thai))
    app.add_handler(CommandHandler("english", english))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("ASTRA bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
