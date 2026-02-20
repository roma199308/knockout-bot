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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Новый расчёт", callback_data="restart")],
        [InlineKeyboardButton("🗑 Сбросить всё", callback_data="clear")]
    ])


async def send_and_store(update, context, text, reply_markup=None):
    msg = await update.effective_chat.send_message(text, reply_markup=reply_markup)
    context.user_data.setdefault("bot_messages", []).append(msg.message_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_and_store(update, context, "Стартовый стек?")
    return STACK


async def restart_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await send_and_store(update, context, "Стартовый стек?")
    return STACK


async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # удаляем все сообщения бота
    for msg_id in context.user_data.get("bot_messages", []):
        try:
            await context.bot.delete_message(chat_id=query.message.chat.id, message_id=msg_id)
        except:
            pass

    context.user_data.clear()

    # отправляем только кнопку нового расчёта
    msg = await context.bot.send_message(
        chat_id=query.message.chat.id,
        text="",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Новый расчёт", callback_data="restart")]
        ])
    )
    context.user_data["bot_messages"] = [msg.message_id]

    return ConversationHandler.END


async def get_stack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stack"] = float(update.message.text.replace(",", "."))
    await send_and_store(update, context, "Количество стартовых ноков?")
    return BOUNTIES


async def get_bounties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bounties"] = float(update.message.text.replace(",", "."))
    await send_and_store(update, context, "Текущий большой блайнд?")
    return BB


async def get_bb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bb"] = float(update.message.text.replace(",", "."))
    await send_and_store(update, context, "Выбери стадию турнира:", reply_markup=stage_keyboard())
    return STAGE


async def stage_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    stage_percent = float(query.data)
    stack = context.user_data["stack"]
    bounties = context.user_data["bounties"]
    bb = context.user_data["bb"]

    result_bb = (stack * (stage_percent / 100) * bounties) / bb
    text = f"{round(result_bb, 2)} BB"

    msg = await query.edit_message_text(text, reply_markup=result_keyboard())
    context.user_data.setdefault("bot_messages", []).append(msg.message_id)

    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(restart_entry, pattern="^restart$"),
            CallbackQueryHandler(clear_chat, pattern="^clear$"),
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
