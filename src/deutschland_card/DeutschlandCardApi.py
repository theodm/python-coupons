import requests as req
import json
import datetime
from enum import Enum
from dateutil import parser as dateparser
from loguru import logger

from http.client import HTTPConnection  # py3
import logging
import contextlib

from src.config import get_deutschlandcard_secret_api_token

# Reverse-Engineered API from DeutschlandCard Android App
X_API_TOKEN = get_deutschlandcard_secret_api_token()
USER_AGENT = "okhttp/3.12.1"
API_BASE_URL = "https://wsp.deutschlandcard.de/dlc-integration/app-dc/v2"


class DeutschlandCardApi:
    def __init__(self):
        headers = {"x-api-token": X_API_TOKEN, "User-Agent": USER_AGENT}

        self.session = req.Session()
        self.session.headers = headers

    def login(self, card_number, geb_dat, plz):
        """
        Führt den Login-Prozess wie in der DeutschlandCard-App durch. Diese Methode gibt den X-Auth-Token zurück, der für
        alle weiteren Anfragen benötigt wird.

        :param card_number: Nummer der DeutschlandCard
        :param geb_dat: Geburtsdatum des Inhabers im Format "YYYY-MM-DD"
        :param plz: PLZ des Inhabers (bei Umzug ändern)
        :return:
        """
        _data = {"cardNumber": card_number, "password": (geb_dat + "|" + plz)}

        _headers = {
            # Initial kein X-Auth-Token: Wird nach dem Login gesetzt.
            "X-auth-token": "",
        }

        result = self.session.post(
            f"{API_BASE_URL}/members/login", headers=_headers, json=_data
        )

        return result.json()["x-auth-token"]

    def getcoupons(self, card_number, token):
        """
        Gibt alle Coupons zurück, die für den Nutzer sichtbar sind.

        :param card_number: Nummer der DeutschlandCard
        :param token: Token, der nach dem Login zurückgegeben wird.
        :return:
        """
        data = {
            # Wir fragen wie in der App nur die Coupons ab, die für den Nutzer sichtbar sind.
            "visibleFrom": (
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).isoformat(),
            "visibleTo": (
                datetime.datetime.now() + datetime.timedelta(days=1)
            ).isoformat(),
            "cardNumber": card_number,
        }

        headers = {
            "x-auth-token": token,
        }

        result = self.session.post(
            f"{API_BASE_URL}/members/coupons/query", headers=headers, json=data
        )

        return result.json()

    def points(self, card_number, token):
        """
        Gibt die Punkte des Nutzers und zugehörige Informationen wie bald ablaufende Punkte zurück.

        :param card_number: Nummer der DeutschlandCard
        :param token: Token, der nach dem Login zurückgegeben wird.
        :return:
        """
        data = {"cardNumber": card_number}

        headers = {
            "x-auth-token": token,
        }

        result = self.session.post(
            f"{API_BASE_URL}/members/points", headers=headers, json=data
        )

        return result.json()

    def activate_coupon(
        self, card_number, token, public_promotion_id, partner_subgroup
    ):
        """
        Aktiviert einen Coupon für den Nutzer.

        :param card_number: Nummer der DeutschlandCard
        :param token: Token, der nach dem Login zurückgegeben wird.
        :param public_promotion_id: publicPromotionId des Coupons
        :param partner_subgroup: partnerSubgroup des Coupons
        :return:
        """
        data = {
            "cardNumber": card_number,
            "publicPromotionId": public_promotion_id,
            "partnerSubgroup": partner_subgroup,
        }

        headers = {
            "x-auth-token": token,
        }

        result = self.session.post(
            f"{API_BASE_URL}/members/coupons/registration", headers=headers, json=data
        )

        if result.status_code != 200:
            logger.error(f"Could not activate {public_promotion_id}")
            raise Exception(f"Could not activate {public_promotion_id}")

        return


def dc_activate_all_coupons_and_get_account_balance(card_number, birth_date, plz):
    """
    Aktiviert alle Coupons für den Nutzer. Diese Methode gibt die Anzahl der aktivierten, übersprungenen und fehlerhaften
    Coupons zurück. Außerdem gibt die Methode die Anzahl der Punkte, bald ablaufenden Punkte und das Datum des nächsten
    Punkteverfalls zurück.

    :param card_number: Nummer der DeutschlandCard
    :param birth_date: Geburtsdatum des Inhabers im Format "YYYY-MM-DD"
    :param plz: PLZ des Inhabers (bei Umzug ändern)
    :return: Anzahl der aktivierten, übersprungenen und fehlerhaften Coupons (in dieser Reihenfolge)
    """
    api = DeutschlandCardApi()
    token = api.login(card_number, birth_date, plz)

    coupon_result = api.getcoupons(card_number, token)

    def format_coupon(coupon):
        return (
            coupon["content"]["headline"]
            + " "
            + coupon["content"]["shortDescription"]
            + " "
            + coupon["content"]["partnerName"]
        )

    current_datetime = datetime.datetime.now()
    count_skipped = 0
    count_activated = 0
    count_error = 0

    for coupon in coupon_result["coupons"]:
        try:

            def is_filled(coupon, key):
                return key in coupon["content"] and coupon["content"][key]

            def get_filled(coupon, key):
                return coupon["content"][key] if is_filled(coupon, key) else "None"

            if is_filled(coupon, "affiliateURLApp") or is_filled(
                coupon, "affiliateURLWeb"
            ):
                logger.debug(
                    f"SKIPPED: {format_coupon(coupon)} has affiliate URL: {get_filled(coupon, 'affiliateURLApp')} {get_filled(coupon, 'affiliateURLWeb')}"
                )
                count_skipped = count_skipped + 1
                continue

            if coupon["status"] != "NRG":
                logger.debug(
                    f"SKIPPED: {format_coupon(coupon)} status is {coupon['status']}"
                )
                count_skipped = count_skipped + 1
                continue

            begin = dateparser.parse(coupon["visibleFrom"])
            end = dateparser.parse(coupon["visibleTo"])

            if not (begin < current_datetime < end):
                logger.debug(f"SKIPPED: {format_coupon(coupon)} is not visible")
                count_skipped = count_skipped + 1
                continue

            api.activate_coupon(
                card_number,
                token,
                coupon["publicPromotionId"],
                coupon["partnerSubgroup"],
            )
            logger.debug(f"ACTIVATED: {format_coupon(coupon)}")
            count_activated = count_activated + 1
        except Exception as e:
            logger.error(f"Could not activate coupon: {coupon['publicPromotionId']}")
            logger.error(e)
            count_error = count_error + 1

    points_json = api.points(card_number, token)

    balance = points_json["balance"]
    expiring_points = points_json["expiringPoints"]
    date_of_next_expiry = points_json["dateOfNextExpiry"]

    points_expiry_date = (
        date_of_next_expiry[8:10]
        + "."
        + date_of_next_expiry[5:7]
        + "."
        + date_of_next_expiry[0:4]
    )

    return (
        count_activated,
        count_skipped,
        count_error,
        balance,
        expiring_points,
        points_expiry_date,
    )
