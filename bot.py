import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

STACK, BOUNTIES, BB, STAGE = range(4)

STAGES = [
    ("25% — начало", "25"),
    ("33% — поздняя реги до ITM", "33"),
    ("40% — ITM до финалки", "40"),
    ("50% — финалка", "50"),
]


def stage_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=value)] for text, value in STAGES])


def result_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Новый расчёт", callback_data="restart")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_chat.send_message("Стартовый стек?")
    return STACK


async def restart_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.edit_text("Стартовый стек?")
    return STACK


async def get_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stack"] = float(update.message.text.replace(",", "."))
    await update.effective_chat.send_message("Количество стартовых ноков?")
    return BOUNTIES


async def get_bounties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bounties"] = float(update.message.text.replace(",", "."))
    await update.effective_chat.send_message("Текущий большой блайнд?")
    return BB


async def get_bb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bb"] = float(update.message.text.replace(",", "."))
    await update.effective_chat.send_message("Выбери стадию турнира:", reply_markup=stage_keyboard())
    return STAGE


async def stage_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stage_percent = query.data
    stage_text = next(text for text, value in STAGES if value == stage_percent)

    # 1) СРАЗУ после клика — отдельное сообщение со стадией
    await query.message.chat.send_message(f"Стадия: {stage_text}")

    # 2) Финальный результат — ТОЛЬКО стоимость нока
    stack = context.user_data["stack"]
    bounties = context.user_data["bounties"]
    bb = context.user_data["bb"]

    result_bb = (stack * (float(stage_percent) / 100) * bounties) / bb
    result_text = f"Стоимость нока: {round(result_bb, 2)} BB"

    # Редактируем сообщение с кнопками стадии в финальный результат
    await query.edit_message_text(result_text, reply_markup=result_keyboard())

    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(restart_entry, pattern="^restart$"),
        ],
        states={
            STACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stack)],
            BOUNTIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bounties)],
            BB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bb)],
            STAGE: [CallbackQueryHandler(stage_selected)],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
