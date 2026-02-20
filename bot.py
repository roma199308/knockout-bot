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

def stage_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=value)] for text, value in STAGES])

def restart_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Новый расчёт", callback_data="restart")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Стартовый стек?")
    return STACK

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Ок, отменил. Напиши /start чтобы начать заново.")
    return ConversationHandler.END

async def restart_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("Стартовый стек?")
    return STACK

async def get_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["stack"] = float(update.message.text.replace(",", "."))
        await update.message.reply_text("Количество стартовых ноков?")
        return BOUNTIES
    except:
        await update.message.reply_text("Введи число. Стартовый стек?")
        return STACK

async def get_bounties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["bounties"] = float(update.message.text.replace(",", "."))
        await update.message.reply_text("Текущий большой блайнд?")
        return BB
    except:
        await update.message.reply_text("Введи число. Количество ноков?")
        return BOUNTIES

async def get_bb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["bb"] = float(update.message.text.replace(",", "."))
        await update.message.reply_text("Выбери стадию турнира:", reply_markup=stage_keyboard())
        return STAGE
    except:
        await update.message.reply_text("Введи число. Большой блайнд?")
        return BB

async def stage_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # если нажали кнопку рестарта в момент выбора стадии
    if query.data == "restart":
        return await restart_from_button(update, context)

    stage_percent = float(query.data)
    stack = context.user_data["stack"]
    bounties = context.user_data["bounties"]
    bb = context.user_data["bb"]

    result_bb = (stack * (stage_percent / 100) * bounties) / bb

    # выводим только число, но с кнопкой "Новый расчёт"
    await query.edit_message_text(str(round(result_bb, 2)), reply_markup=restart_keyboard())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stack)],
            BOUNTIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bounties)],
            BB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bb)],
            STAGE: [CallbackQueryHandler(stage_selected)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)

    # Кнопка "Новый расчёт" работает и после завершения диалога
    app.add_handler(CallbackQueryHandler(restart_from_button, pattern="^restart$"))

    app.run_polling()

if __name__ == "__main__":
    main()
