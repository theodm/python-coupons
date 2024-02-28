from datetime import timedelta

from loguru import logger
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    Application,
    CallbackContext,
)
from src.config import get_allowed_user_ids, get_telegram_token


async def is_allowed_to_interact(update: Update) -> bool:
    if not update.effective_user or not str(update.effective_user.id) in (
        get_allowed_user_ids()
    ):
        logger.info(
            f"User {update.effective_user.id} tried to interact with the bot, but is not allowed. (allowed are {get_allowed_user_ids()}))"
        )
        await update.message.reply_text(
            f"Sorry {update.effective_user.first_name}, I'm not allowed to interact with you."
        )
        return False
    return True


# Konversation: Der Benutzer hat zu lange gebraucht, um das OTP einzugeben.
async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    await update.message.reply_text(
        f"Die Eingabe hat zu lange gedauert. Die Konversation wird abgebrochen."
    )

    return ConversationHandler.END


# Konversation: Der Benutzer hat mit /cancel abgebrochen.
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    await update.message.reply_text(f"Die Konversation wurde vom Benutzer abgebrochen.")

    return ConversationHandler.END
