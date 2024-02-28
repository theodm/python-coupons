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
from src.database.database import insert_payback_account
from src.handler.shared import is_allowed_to_interact, timeout, cancel

PAYBACK_ENTER_USERNAME = 0
PAYBACK_ENTER_PASSWORD = 1


async def register_payback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    await update.message.reply_text("Bitte gib deinen Payback-Benutzernamen ein.")

    return PAYBACK_ENTER_USERNAME


async def payback_username_entered(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    context.user_data["payback_username"] = update.message.text
    await update.message.reply_text("Bitte gib dein Payback-Passwort ein.")

    return PAYBACK_ENTER_PASSWORD


async def payback_password_entered(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    context.user_data["payback_password"] = update.message.text

    await update.message.reply_text(
        "Vielen Dank, deine Payback-Daten wurden erfolgreich registriert."
    )

    insert_payback_account(
        context.user_data["payback_username"], context.user_data["payback_password"]
    )

    logger.info(
        f"Registered Payback account for user {update.effective_user.id}. Username: {context.user_data['payback_username']}, Password: {context.user_data['payback_password']}"
    )

    return ConversationHandler.END


def get_register_payback_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("register_payback", register_payback)],
        states={
            PAYBACK_ENTER_USERNAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, payback_username_entered
                )
            ],
            PAYBACK_ENTER_PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, payback_password_entered
                )
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, timeout),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        # Maximal 10 Minuten, das ist mehr als genug Zeit, um den Dialog durchzugehen.
        conversation_timeout=timedelta(seconds=60 * 10),
    )
