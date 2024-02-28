import requests as req
import logging as log
import json
import datetime
from enum import Enum
from dateutil import parser as dateparser
from loguru import logger

from src.config import (
    get_payback_basic_auth_username,
    get_payback_basic_auth_credential,
    get_payback_principal,
)


class CouponStatus(Enum):
    Available = 1
    Activated = 2
    Used = 3  # ?
    Used2 = 4  # ?


PAYBACK_BASIC_AUTH_USERNAME = get_payback_basic_auth_username()
PAYBACK_BASIC_AUTH_CREDENTIAL = get_payback_basic_auth_credential()
PAYBACK_PRINCIPAL = get_payback_principal()

PAYBACK_API_BASE_URL = f"https://services-ext.payback.de/{PAYBACK_PRINCIPAL}/v1"

payback_date_format = "%Y-%m-%dT%H:%M:%S+0200"


class PaybackApi:
    def __init__(self):
        self.session = req.Session()
        self.session.auth = (PAYBACK_BASIC_AUTH_USERNAME, PAYBACK_BASIC_AUTH_CREDENTIAL)
        self.session.headers = {
            "Content-Type": "application/json; charset=utf8",
            "Accept": "application/json; charset=utf-8",
            "Accept-Encoding": "gzip",
            "User-Agent": "DSA/24.02.0101(1707819571) iOS/16.1.1",
        }

    # https://services-ext.payback.de/138/v1/json/secureauthenticate
    # {
    #   "consumerIdentification": {
    #     "consumerAuthentication": {
    #       "credential": "XXXX",
    #       "principal": "XXX"
    #     }
    #   },
    #   "authorizationRequestValidityDuration": 120,
    #   "authentication": {
    #     "identification": {
    #       "alias": "XXX@XXX.com",
    #       "aliasType": 5
    #     },
    #     "security": {
    #       "secret": "XXX",
    #       "secretType": 3
    #     }
    #   },
    #   "clientDisplayName": "iPhone",
    #   "managedMemberDeviceIdentifiers": []
    # }

    def _login(self, identification, security):
        _data = {
            "consumerIdentification": {
                "consumerAuthentication": {
                    "credential": PAYBACK_BASIC_AUTH_CREDENTIAL,
                    "principal": PAYBACK_PRINCIPAL,
                }
            },
            "authorizationRequestValidityDuration": 120,
            "authentication": {"identification": identification, "security": security},
            "clientDisplayName": "iPhone",
            "managedMemberDeviceIdentifiers": [],
        }

        result = self.session.post(
            f"{PAYBACK_API_BASE_URL}/json/secureauthenticate", json=_data
        )

        result_data = result

        authentication = result_data.json()["standardAuthentication"]

        authentication.pop("refreshToken")

        return authentication

    def login_with_mail(self, mail, password):
        return self._login(
            {
                "alias": mail,
                "aliasType": 5,
            },
            {"secret": password, "secretType": 3},
        )

    def login_with_kdnr(self, kdNr, password):
        return self._login(
            {"alias": kdNr, "aliasType": 1}, {"secret": password, "secretType": 3}
        )

    # https://services-ext.payback.de/139/v1/json/activatecoupon
    # {
    #     "activatedAt": "2019-09-18T22:01:37+02",
    #     "authentication": {
    #         "token": "D92E1BB9E663E817F04DC6D28D11CCB39522784C20F0011F5D59B828A2200405"
    #     },
    #     "couponID": "497462",
    #     "force": false,
    #     "consumerIdentification": {
    #         "consumerAuthentication": {
    #             "credential": "XXXX",
    #             "principal": "XXX"
    #         }
    # }
    def activate_coupon(self, authentication, couponID):
        _data = {
            "activatedAt": datetime.datetime.now().strftime(payback_date_format),
            "authentication": authentication,
            "couponID": couponID,
            "force": False,
            "consumerIdentification": {
                "consumerAuthentication": {
                    "credential": PAYBACK_BASIC_AUTH_CREDENTIAL,
                    "principal": PAYBACK_PRINCIPAL,
                }
            },
        }

        result = self.session.post(
            f"{PAYBACK_API_BASE_URL}/json/activatecoupon", json=_data
        )

        return

    # https://services-ext.payback.de/139/v1/json/getcoupons
    # {
    #   "authentication": {
    #     "token": "T04N--878df1cf-0185-4dea-b4e0-53601a4acbd1--D8uvcuoDD8I7o0INEh2Q6fCktRFWmf4BxAlWqqiINEWNwNeJkAh1RlqDhNot1X4N"
    #   },
    #   "couponFilter": {
    #     "couponDistributionChannel": [
    #       5
    #     ]
    #   },
    #   "couponPeriodFilter": [
    #     {
    #       "referenceDate": "2024-02-22T20:04:32+01:00",
    #       "periodQuery": 9
    #     }
    #   ],
    #   "consumerIdentification": {
    #     "consumerAuthentication": {
    #       "credential": "XXXX",
    #       "principal": "XXX"
    #     }
    #   }
    # }
    def get_coupons(self, authentication):
        _data = {
            "authentication": authentication,
            "couponFilter": {"couponDistributionChannel": [5]},
            "couponPeriodFilter": [
                {
                    "periodQuery": 9,
                    "referenceDate": datetime.datetime.now().strftime(
                        payback_date_format
                    ),
                }
            ],
            "locationFilter": {
                "position": {"latitude": 51.165691, "longitude": 10.451526}
            },
            "consumerIdentification": {
                "consumerAuthentication": {
                    "credential": PAYBACK_BASIC_AUTH_CREDENTIAL,
                    "principal": PAYBACK_PRINCIPAL,
                }
            },
        }

        result = self.session.post(
            f"{PAYBACK_API_BASE_URL}/json/getcoupons", json=_data
        )

        result_data = result

        return result_data.json()

    # https://services-ext.payback.de/139/v1/json/getaccountbalance
    # {
    #   "authentication": {
    #     "token": "T04N--878df1cf-0185-4dea-b4e0-53601a4acbd1--D8uvcuoDD8I7o0INEh2Q6fCktRFWmf4BxAlWqqiINEWNwNeJkAh1RlqDhNot1X4N"
    #   },
    #   "consumerIdentification": {
    #     "consumerAuthentication": {
    #       "credential": "XXXX",
    #       "principal": "XXX"
    #     }
    #   }
    # }
    def get_account_balance(self, authentication):
        _data = {
            "authentication": authentication,
            "consumerIdentification": {
                "consumerAuthentication": {
                    "credential": PAYBACK_BASIC_AUTH_CREDENTIAL,
                    "principal": PAYBACK_PRINCIPAL,
                }
            },
        }

        result = self.session.post(
            f"{PAYBACK_API_BASE_URL}/json/getaccountbalance", json=_data
        )

        json = result.json()
        return json


def payback_activate_all_available_coupons(kdnr_or_email, password):
    api = PaybackApi()

    # Wir loggen mit der Kundennummer oder der E-Mail-Adresse ein,
    # je nachdem welche Information wir vorliegend haben.
    if kdnr_or_email.isdigit():
        authentication = api.login_with_kdnr(kdnr_or_email, password)
    else:
        authentication = api.login_with_mail(kdnr_or_email, password)

    # Abfragen der verfügbaren Coupons mit dem Token
    coupon_data = api.get_coupons(authentication)

    current_datetime = datetime.datetime.now(datetime.timezone.utc)

    coupons = coupon_data["couponListItem"]

    count_successful = 0
    count_skipped = 0
    count_errored = 0
    for coupon in coupons:
        try:
            coupon = coupon["coupon"]

            if coupon["couponStatus"] != CouponStatus.Available.value:
                logger.info(
                    f"UNAVAILABLE: {coupon['couponID']}:{coupon['partner'][0]['partnerDisplayName']}:{coupon['couponStatus']}:{coupon['couponContentSet']['textItem'][2]['textValue']} {coupon['couponContentSet']['textItem'][3]['textValue']}".replace(
                        "\n", " "
                    )
                )
                count_skipped = count_skipped + 1
                continue

            # Parsen des Beginn- und Enddatums des Coupons
            begin = dateparser.parse(coupon["validity"]["validFrom"])
            end = dateparser.parse(coupon["validity"]["validTo"])

            # Überspringen des Coupons, wenn er nicht gültig ist
            if not (begin < current_datetime < end):
                logger.info(
                    f"UNAVAILABLE: {coupon['couponID']}:{coupon['partner'][0]['partnerDisplayName']}:{coupon['couponStatus']}:{coupon['couponContentSet']['textItem'][2]['textValue']} {coupon['couponContentSet']['textItem'][3]['textValue']}".replace(
                        "\n", " "
                    )
                )
                count_skipped = count_skipped + 1
                continue

            # Aktivieren des Coupons mit dem Token und der Coupon-ID
            api.activate_coupon(authentication, coupon["couponID"])

            # Erhöhen des Zählers für die aktivierten Coupons um 1
            count_successful = count_successful + 1

            # Loggen der erfolgreichen Aktivierung des Coupons
            logger.info(
                f"ACTIVATED: {coupon['couponID']}:{coupon['partner'][0]['partnerDisplayName']}:{coupon['couponStatus']}:{coupon['couponContentSet']['textItem'][2]['textValue']} {coupon['couponContentSet']['textItem'][3]['textValue']}".replace(
                    "\n", " "
                )
            )
        except Exception as e:
            logger.error(
                f"FAILED TO ACTIVATE:{coupon['couponID']}:{coupon['partner'][0]['partnerDisplayName']}:{e}".replace(
                    "\n", " "
                )
            )
            count_errored = count_errored + 1

    account_balance = api.get_account_balance(authentication)

    points = account_balance["accountBalanceDetails"][0]["totalPointsAmount"]
    expiring_points = account_balance["accountBalanceDetails"][0]["expiryAnnouncement"][
        "pointsToExpireAmount"
    ]
    points_expiry_date = "30.09." + str(datetime.datetime.now().year)

    return (
        count_successful,
        count_skipped,
        count_errored,
        points,
        expiring_points,
        points_expiry_date,
    )
