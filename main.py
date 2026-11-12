import logging
import os

from openai import AsyncOpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
PUBLIC_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
PORT = int(os.environ.get("PORT", "10000"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "astra-telegram-webhook")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET") or None

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
MENU = ReplyKeyboardMarkup([["✨ Натальная карта", "ℹ️ О проекте"]], resize_keyboard=True)

WELCOME = (
    "✨ Добро пожаловать в ASTRA — пространство астрологии и самопознания.\n\n"
    "Я помогу подготовить символический разбор натальной карты. "
    "Для начала нажми «Натальная карта»."
)

SYSTEM_PROMPT = """
Ты — ASTRA, бережный и грамотный астрологический помощник.
Подготовь содержательный, понятный и красиво структурированный символический
разбор натальной карты на русском языке, опираясь только на данные рождения,
которые предоставил пользователь. Не выдумывай рассчитанные положения планет,
дома, асцендент или аспекты: если точные астрономические положения не переданы,
честно скажи, что это предварительный разбор, а не точный расчёт.
Не представляй астрологию как науку или достоверное предсказание. Не давай
медицинских, юридических или финансовых указаний. Избегай фатальных прогнозов.
Структура: общее впечатление; сильные стороны; возможные сложности;
отношения и общение; работа и самореализация; вопросы для размышления.
Тон тёплый, уважительный, без категоричных утверждений.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME, reply_markup=MENU)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n/start — начать заново\n/chart — создать разбор\n"
        "/cancel — отменить ввод\n\n"
        "Для разбора понадобятся дата рождения, время рождения и город/страна."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Ввод отменён. Когда будешь готов(а), нажми «Натальная карта».", reply_markup=MENU)

async def begin_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_birth_details"] = True
    await update.message.reply_text(
        "Напиши данные одним сообщением в таком формате:\n\n"
        "Дата: 15.05.1989\nВремя: 07:30 (если неизвестно — так и напиши)\n"
        "Место: Кишинёв, Молдова\n\n"
        "Укажи местное время рождения. Не отправляй личные документы или адрес."
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ASTRA — астрологический проект для самопознания. Материалы носят "
        "развлекательный и рефлексивный характер: астрология не является научно "
        "подтверждённым способом описания личности или предсказания будущего."
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

    context.user_data["awaiting_birth_details"] = False
    status = await update.message.reply_text("🌙 ASTRA готовит твой разбор…")
    try:
        response = await client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=f"Данные рождения пользователя:\n{text}\n\nСоставь предварительный разбор и обозначь ограничения точности.",
        )
        answer = response.output_text.strip() or "Не удалось подготовить разбор. Попробуй /chart."
        for i in range(0, len(answer), 3900):
            await update.message.reply_text(answer[i:i + 3900], reply_markup=MENU)
        await status.delete()
    except Exception:
        logger.exception("Failed to generate natal reading")
        await status.edit_text("Не получилось создать разбор. Проверь переменную OPENAI_API_KEY в настройках Render.")

def main():
    if not PUBLIC_HOST:
        raise RuntimeError("Render did not provide RENDER_EXTERNAL_HOSTNAME. Deploy this service as a Render Web Service.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", begin_chart))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"https://{PUBLIC_HOST}/{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
