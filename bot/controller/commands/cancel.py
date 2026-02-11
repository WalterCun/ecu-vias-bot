from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ConversationHandler, ContextTypes
from bot.libs.translate import trans


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data

    await update.message.reply_text(
        str(trans.main.cancel.message),
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END
