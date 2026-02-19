import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN = os.getenv("BOT_TOKEN")

STACK, BOUNTIES, BB, STAGE = range(4)

def stage_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("25%", callback_data="25")],
        [InlineKeyboardButton("33%", callback_data="33")],
        [InlineKeyboardButton("40%", callback_data="40")],
        [InlineKeyboardButton("50%", callback_data="50")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Стартовый стек?")
    return STACK

async def get_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stack"] = float(update.message.text)
    await update.message.reply_text("Количество ноков?")
    return BOUNTIES

async def get_bounties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bounties"] = float(update.message.text)
    await update.message.reply_text("Большой блайнд?")
    return BB

async def get_bb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bb"] = float(update.message.text)
    await update.message.reply_text("Выбери стадию:", reply_markup=stage_keyboard())
    return STAGE

async def stage_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stage_percent = float(query.data)
    stack = context.user_data["stack"]
    bounties = context.user_data["bounties"]
    bb = context.user_data["bb"]

    result = (stack * (stage_percent / 100) * bounties) / bb
    await query.edit_message_text(str(round(result, 2)))
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
        fallbacks=[],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
