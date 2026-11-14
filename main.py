import logging
import os
import re
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MENU = ReplyKeyboardMarkup([["✨ Натальная карта", "ℹ️ О проекте"]], resize_keyboard=True)

WELCOME = (
    "✨ Добро пожаловать в ASTRA — пространство астрологии и самопознания.\n\n"
    "Я помогу подготовить символический разбор по дате рождения. "
    "Для начала нажми «Натальная карта»."
)

SIGN_INFO = [
    ((3, 21), (4, 19), "Овен", "инициативность, смелость и стремление действовать", "импульсивность и нетерпение", "Где можно проявить инициативу, не торопя события?"),
    ((4, 20), (5, 20), "Телец", "устойчивость, практичность и верность своим ценностям", "упрямство и сопротивление переменам", "Что даёт тебе чувство устойчивости, а где полезно быть гибче?"),
    ((5, 21), (6, 20), "Близнецы", "любознательность, общение и быстрая адаптация", "рассеянность и избыток впечатлений", "Какие знания и разговоры сейчас действительно важны?"),
    ((6, 21), (7, 22), "Рак", "чуткость, забота и глубокая связь с близкими", "закрытость и повышенная чувствительность", "Как заботиться о других, не забывая о собственных границах?"),
    ((7, 23), (8, 22), "Лев", "творчество, щедрость и желание вдохновлять", "гордость и зависимость от признания", "Где ты можешь проявить себя искренне, не ожидая одобрения?"),
    ((8, 23), (9, 22), "Дева", "внимание к деталям, надёжность и аналитический подход", "перфекционизм и чрезмерная самокритика", "Что уже достаточно хорошо, даже если не идеально?"),
    ((9, 23), (10, 22), "Весы", "дипломатичность, чувство гармонии и партнёрство", "нерешительность и стремление всем угодить", "Какое решение будет честным прежде всего по отношению к себе?"),
    ((10, 23), (11, 21), "Скорпион", "глубина, настойчивость и способность к внутренним переменам", "подозрительность и стремление всё контролировать", "Что можно отпустить, чтобы освободить место для нового?"),
    ((11, 22), (12, 21), "Стрелец", "оптимизм, открытость и тяга к развитию", "нетерпение и обещания без плана", "Как превратить большую идею в один конкретный шаг?"),
    ((12, 22), (1, 19), "Козерог", "ответственность, выдержка и умение строить долгосрочные планы", "излишняя строгость к себе и трудность отдыха", "Как двигаться к цели, сохраняя силы и радость жизни?"),
    ((1, 20), (2, 18), "Водолей", "независимость, оригинальность и интерес к новым идеям", "отстранённость и упрямство во взглядах", "Какая необычная идея заслуживает спокойной проверки?"),
    ((2, 19), (3, 20), "Рыбы", "воображение, эмпатия и тонкое восприятие", "уход от сложностей и размытые границы", "Как соединить интуицию с практическими действиями?"),
]

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

def zodiac_for(day, month):
    value = (month, day)
    for start, finish, name, strengths, challenges, question in SIGN_INFO:
        if start <= finish:
            inside = start <= value <= finish
        else:
            inside = value >= start or value <= finish
        if inside:
            return name, strengths, challenges, question
    return None

def make_reading(birth_date):
    sign, strengths, challenges, question = zodiac_for(birth_date.day, birth_date.month)
    return (
        f"🌙 ASTRA — предварительный символический разбор\n"
        f"Твоя дата рождения: {birth_date.strftime('%d.%m.%Y')}\n"
        f"Солнечный знак: {sign}\n\n"
        f"✨ **Общее впечатление**\n"
        f"В астрологической традиции {sign} связывают с такими качествами, как {strengths}. "
        f"Это темы для самонаблюдения, а не фиксированное описание твоего характера.\n\n"
        f"💎 **Возможные сильные стороны**\n"
        f"Полезно обратить внимание на ситуации, где проявляются {strengths}. "
        f"Подумай, какие из этих качеств действительно знакомы тебе по жизненному опыту.\n\n"
        f"🌱 **Зоны роста**\n"
        f"Символические сложности этого знака — {challenges}. "
        f"Это не недостатки и не предсказание, а возможные темы для размышления.\n\n"
        f"❤️ **Отношения и общение**\n"
        f"Попробуй замечать, как ты выражаешь свои потребности, слушаешь близких и сохраняешь личные границы.\n\n"
        f"🎯 **Работа и самореализация**\n"
        f"Опирайся на реальные навыки и интересы. Астрологический символ может быть поводом подумать, "
        f"какие задачи дают тебе энергию и ощущение смысла.\n\n"
        f"❓ **Вопрос для размышления**\n{question}\n\n"
        f"ℹ️ Сейчас ASTRA определяет только солнечный знак по дате. Время и место рождения пока не "
        f"рассчитываются; Луна, Асцендент, дома и аспекты не определены. Астрология не является "
        f"научно подтверждённым методом описания личности или предсказания будущего."
    )

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
    birth_date = parse_birth_date(text)
    if birth_date is None:
        await update.message.reply_text(
            "Не удалось распознать дату. Напиши её, например: 15.05.1989 или 1989-05-15."
        )
        context.user_data["awaiting_birth_details"] = True
        return

    context.user_data["awaiting_birth_details"] = False
    answer = make_reading(birth_date)
    await update.message.reply_text(answer, reply_markup=MENU)

def main():
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chart", begin_chart))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("ASTRA bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
