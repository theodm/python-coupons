# coding=utf-8
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
from config import get_allowed_user_ids, get_telegram_token
from src.database.database import get_dc_accounts, get_payback_accounts
from src.deutschland_card.DeutschlandCardApi import (
    dc_activate_all_coupons_and_get_account_balance,
)
from src.handler.register_dc_handler import get_register_dc_handler
from src.handler.register_payback_handler import get_register_payback_handler
from src.handler.remove_account import get_remove_account_handler
from src.payback.PaybackAPI import payback_activate_all_available_coupons


# Hiermit kann das Menü für den Bot in Telegram gesetzt werden.
async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            (
                "activate_coupons",
                "Aktiviert für alle registrierten Accounts alle offenen Coupons unabhängig von dem gesetzten Intervall.",
            ),
            (
                "register_dc",
                "Registriert einen neuen DeutschlandCard-Account, dessen Coupons im konfigurierten Intervall aktiviert werden.",
            ),
            (
                "register_payback",
                "Registriert einen neuen Payback-Account, dessen Coupons im konfigurierten Intervall aktiviert werden.",
            ),
            ("remove_account", "Entfernt einen Account."),
            ("cancel", "Bricht eine bestehende Konversation ab."),
        ]
    )


# Diese Methode wird jeden Tag aufgerufen und aktiviert alle Coupons der registrierten Benutzer.
async def activate_coupons(context: CallbackContext):
    dc_accounts = get_dc_accounts()
    payback_accounts = get_payback_accounts()

    async def send_to_all(text):
        for user_id in get_allowed_user_ids():
            await context.bot.send_message(
                chat_id=user_id, text=text, parse_mode="HTML"
            )

    message = ""
    message2 = ""
    if dc_accounts:
        message = "Für folgende DeutschlandCard-Accounts wurde eine Aktivierung durchgeführt:\n\n"
        message2 = "Punkte der DeutschlandCard-Accounts:\n\n"

        for account in dc_accounts:
            try:
                card_number = account["dc_card_number"]
                birthdate = account["dc_birthdate"]
                plz = account["dc_plz"]

                (
                    count_activated,
                    count_skipped,
                    count_errored,
                    points,
                    expiring_points,
                    points_expiry,
                ) = dc_activate_all_coupons_and_get_account_balance(
                    card_number, birthdate, plz
                )

                logger.info(
                    f"Activated {count_activated} coupons for {account['dc_card_number']}. Skipped {count_skipped} and errored {count_errored}."
                )
                message = (
                    message
                    + f"{account['dc_card_number']}: 👍 {count_activated} 👌 {count_skipped} 👎 {count_errored}\n"
                )

                logger.info(
                    f"Points for {account['dc_card_number']}: {points}. Expiring points: {expiring_points} at {points_expiry}."
                )
                message2 = (
                    message2
                    + f"{account['dc_card_number']}: {points} Punkte "
                    + (
                        f"({expiring_points} verfallen am {points_expiry})"
                        if expiring_points > 0
                        else ""
                    )
                    + "\n"
                )
            except Exception as e:
                logger.error(
                    f"Could not activate coupons for {account['dc_card_number']}: {e}"
                )
                message = (
                    message + f"{account['dc_card_number']}: Fehler aufgetreten 👎.\n"
                )
                message2 = (
                    message2 + f"{account['dc_card_number']}: Fehler aufgetreten 👎.\n"
                )

        message = message + "\n\n"
        message2 = message2 + "\n\n"

    if payback_accounts:
        message = (
            message
            + "Für folgende Payback-Accounts wurde eine Aktivierung durchgeführt:\n\n"
        )
        message2 = message2 + "Punkte der Payback-Accounts:\n\n"

        for account in payback_accounts:
            try:
                username = account["payback_username"]
                password = account["payback_password"]

                (
                    count_activated,
                    count_skipped,
                    count_errored,
                    points,
                    expiring_points,
                    points_expiry,
                ) = payback_activate_all_available_coupons(username, password)

                logger.info(
                    f"Activated {count_activated} coupons for {account['payback_username']}. Skipped {count_skipped} and errored {count_errored}."
                )
                message = (
                    message
                    + f"{account['payback_username']}: 👍 {count_activated} 👌 {count_skipped} 👎 {count_errored}\n"
                )

                logger.info(
                    f"Points for {account['payback_username']}: {points}. Expiring points: {expiring_points} at {points_expiry}."
                )
                message2 = (
                    message2
                    + f"{account['payback_username']}: {points} Punkte "
                    + (
                        f"({expiring_points} verfallen am {points_expiry})"
                        if expiring_points > 0
                        else ""
                    )
                    + "\n"
                )
            except Exception as e:
                logger.error(
                    f"Could not activate coupons for {account['payback_username']}: {e}"
                )
                message = (
                    message + f"{account['payback_username']}: Fehler aufgetreten 👎.\n"
                )

    if not message:
        message = "Es sind keine Accounts registriert."

        await send_to_all(message)
        return

    await send_to_all(message)
    await send_to_all(message2)

    pass


async def activate_coupons_manually(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await activate_coupons(context)


app = ApplicationBuilder().token(get_telegram_token()).post_init(post_init).build()

register_dc_account_handler = get_register_dc_handler()
register_payback_account_handler = get_register_payback_handler()
remove_account_handler = get_remove_account_handler()


p = app.job_queue.run_repeating(
    activate_coupons, interval=timedelta(days=1), first=timedelta(seconds=5)
)

app.add_handler(CommandHandler("activate_coupons", activate_coupons_manually))

app.add_handler(register_dc_account_handler)
app.add_handler(register_payback_account_handler)
app.add_handler(remove_account_handler)
app.run_polling()
