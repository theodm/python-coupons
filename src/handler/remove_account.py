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
from src.database.database import (
    get_dc_accounts,
    get_payback_accounts,
    remove_dc_account_by_id,
    remove_payback_account_by_id,
)
from src.handler.shared import is_allowed_to_interact, timeout, cancel

ACCOUNT_SELECTED = 0


async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    dc_accounts = get_dc_accounts()
    payback_accounts = get_payback_accounts()

    accounts = []

    for _, account in enumerate(dc_accounts):
        accounts.append(
            {
                "type": "dc",
                "id": account["id"],
                "card_number": account["dc_card_number"],
                "birthdate": account["dc_birthdate"],
                "plz": account["dc_plz"],
                "command": f"/dc_{account['id']}",
            }
        )

    for i, account in enumerate(payback_accounts):
        accounts.append(
            {
                "type": "payback",
                "id": account["id"],
                "username": account["payback_username"],
                "plz": "",
                "command": f"/payback_{account['id']}",
            }
        )

    if len(accounts) == 0:
        await update.message.reply_text("Es sind keine Accounts registriert.")

        return ConversationHandler.END

    message = "Welchen Account möchtest du entfernen?\n\n"
    message += ""

    for i, account in enumerate(accounts):
        if account["type"] == "dc":
            message += f"{i+1}. DeutschlandCard: {account['card_number']} ({account['plz']}) -> {account['command']}\n\n"
        else:
            message += (
                f"{i+1}. Payback: {account['username']} -> {account['command']}\n\n"
            )

    await update.message.reply_text(message)

    context.user_data["accounts"] = accounts

    return ACCOUNT_SELECTED


async def remove_account_selected(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    # Wir lassen nur geladene Gäste rein. ;-)
    if not await is_allowed_to_interact(update):
        return ConversationHandler.END

    accounts = [
        account
        for account in context.user_data["accounts"]
        if account["command"] == update.message.text
    ]

    if len(accounts) == 0:
        await update.message.reply_text(
            "Der Account konnte nicht gefunden werden. Haben Sie den falschen Befehl eingegeben?"
        )

        return ConversationHandler.END

    account = accounts[0]

    if account["type"] == "dc":
        remove_dc_account_by_id(account["id"])

        logger.info(
            f"User {update.effective_user.id} removed DC account with username {account['card_number']} and PLZ {account['plz']}."
        )
    else:
        remove_payback_account_by_id(account["id"])

        logger.info(
            f"User {update.effective_user.id} removed Payback account with username {account['username']}."
        )

    await update.message.reply_text(f"Der Account wurde entfernt.")

    return ConversationHandler.END


def get_remove_account_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("remove_account", remove_account)],
        states={
            ACCOUNT_SELECTED: [
                MessageHandler(filters.COMMAND, remove_account_selected),
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, timeout),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        # Maximal 10 Minuten, das ist mehr als genug Zeit, um den Dialog durchzugehen.
        conversation_timeout=timedelta(seconds=60 * 10),
    )
