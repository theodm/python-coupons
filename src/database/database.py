import dataset
from loguru import logger

db = dataset.connect("sqlite:///accounts.db")


def insert_dc_account(dc_card_number, dc_birthdate, dc_plz):
    table = db["dc_accounts"]

    table.insert(
        {
            "dc_card_number": dc_card_number,
            "dc_birthdate": dc_birthdate,
            "dc_plz": dc_plz,
        }
    )

    logger.info(
        f"Persisted DC account with username {dc_card_number}, password {dc_birthdate} and PLZ {dc_plz}."
    )


def insert_payback_account(payback_username, payback_password):
    table = db["payback_accounts"]

    table.insert(
        {"payback_username": payback_username, "payback_password": payback_password}
    )

    logger.info(
        f"Persisted Payback account with username {payback_username} and password {payback_password}."
    )


def remove_dc_account_by_id(account_id):
    table = db["dc_accounts"]

    table.delete(id=account_id)

    logger.info(f"Removed DC account with id {account_id}.")


def remove_payback_account_by_id(account_id):
    table = db["payback_accounts"]

    table.delete(id=account_id)

    logger.info(f"Removed Payback account with id {account_id}.")


def get_dc_accounts():
    table = db["dc_accounts"]

    return list(table.all())


def get_payback_accounts():
    table = db["payback_accounts"]

    return list(table.all())
