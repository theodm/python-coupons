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
from src.database.database import insert_dc_account
from src.handler.shared import is_allowed_to_interact, timeout, cancel

DC_ENTER_CARD_NUMBER = 0
DC_ENTER_BIRTH_DATE = 1
DC_ENTER_PLZ = 2


async def register_dc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    await update.message.reply_text(
        "Es wird nun ein neuer DeutschlandCard-Account in der Datenbank aufgenommen. Es wird nur der Login\n "
        "mit Kartennummer, Geburtsdatum und PLZ unterstützt.\n"
    )

    await update.message.reply_text(
        "Bitte gib die Kartennummer der DeutschlandCard ein."
    )

    return DC_ENTER_CARD_NUMBER


async def dc_card_number_entered(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    context.user_data["dc_card_number"] = update.message.text
    await update.message.reply_text(
        "Bitte gib das Geburtsdatum des Karteninhabers im Format YYYY-MM-DD ein."
    )

    return DC_ENTER_BIRTH_DATE


async def dc_birthdate_entered(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    context.user_data["dc_birthdate"] = update.message.text
    await update.message.reply_text(
        "Bitte gib die Postleitzahl des Karteninhabers ein."
    )

    return DC_ENTER_PLZ


async def dc_plz_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    context.user_data["dc_plz"] = update.message.text
    await update.message.reply_text(
        "Vielen Dank, deine DeutschlandCard-Daten wurden erfolgreich registriert."
    )

    insert_dc_account(
        context.user_data["dc_card_number"],
        context.user_data["dc_birthdate"],
        context.user_data["dc_plz"],
    )

    logger.info(
        f"User {update.effective_user.id} registered with DC username {context.user_data['dc_card_number']}, password {context.user_data['dc_birthdate']} and PLZ {context.user_data['dc_plz']}."
    )

    return ConversationHandler.END


def get_register_dc_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("register_dc", register_dc)],
        states={
            DC_ENTER_CARD_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, dc_card_number_entered)
            ],
            DC_ENTER_BIRTH_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, dc_birthdate_entered)
            ],
            DC_ENTER_PLZ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, dc_plz_entered)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, timeout),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        # Maximal 10 Minuten, das ist mehr als genug Zeit, um den Dialog durchzugehen.
        conversation_timeout=timedelta(seconds=60 * 10),
    )
