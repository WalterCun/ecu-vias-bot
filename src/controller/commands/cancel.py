from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ConversationHandler, ContextTypes


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    # if "times" in user_data:
    #     del user_data["times"]

    await update.message.reply_text(
        f"Muchas Gracias por usar nuestro servicio, todas las configuraciones han sido eliminadas correctamente",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END
