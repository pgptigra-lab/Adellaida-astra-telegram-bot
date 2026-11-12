import logging
import os

from openai import AsyncOpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

MENU = ReplyKeyboardMarkup(
    [["✨ Натальная карта", "ℹ️ О проекте"]],
    resize_keyboard=True,
)

WELCOME = (
    "✨ Добро пожаловать в ASTRA — пространство астрологии и самопознания.\n\n"
    "Я помогу подготовить символический разбор натальной карты. "
    "Для начала нажми «Натальная карта»."
)

SYSTEM_PROMPT = """
Ты — ASTRA, бережный и грамотный астрологический помощник.
Подготовь содержательный, понятный и красиво структурированный символический
разбор натальной карты на русском языке, опираясь ТОЛЬКО на данные рождения,
которые предоставил пользователь. Не выдумывай рассчитанные положения планет,
дома, асцендент или аспекты: если точные астрономические положения не переданы,
честно скажи, что это предварительный разбор по дате и времени, а не точный расчёт.
Не представляй астрологию как науку или достоверное предсказание. Не давай
медицинских, юридических или финансовых указаний. Избегай фатальных прогнозов.
Структура: 1) общее впечатление; 2) сильные стороны; 3) возможные сложности;
4) отношения и общение; 5) работа и самореализация; 6) вопросы для размышления.
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
        "Дата: 15.05.1989\n"
        "Время: 07:30 (если неизвестно — так и напиши)\n"
        "Место: Кишинёв, Молдова\n\n"
        "Укажи местное время рождения. Не отправляй личные документы или адрес."
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ASTRA — астрологический проект для самопознания. "
        "Материалы носят развлекательный и рефлексивный характер: "
        "астрология не является научно подтверждённым способом описания личности "
        "или предсказания будущего."
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
    status = await update.message.reply_text("🌙 ASTRA готовит твой разбор. Это может занять несколько секунд…")

    try:
        response = await client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=f"Данные рождения пользователя:\n{text}\n\nСоставь предварительный разбор и явно обозначь ограничения точности.",
        )
        answer = response.output_text.strip()
        if not answer:
            answer = "Не удалось подготовить разбор. Попробуй ещё раз командой /chart."
        # Telegram messages have a 4096-character limit.
        for start_index in range(0, len(answer), 3900):
            await update.message.reply_text(answer[start_index:start_index + 3900], reply_markup=MENU)
        await status.delete()
    except Exception:
        logger.exception("Failed to generate natal reading")
        await status.edit_text(
            "Не получилось создать разбор. Попробуй позже. "
            "Если ошибка повторяется, проверь настройки OPENAI_API_KEY в Railway."
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", begin_chart))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
