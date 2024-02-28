from src.config import (
    get_debug_deutschlandcard_card_number,
    get_debug_deutschlandcard_geburtsdatum,
    get_debug_deutschlandcard_plz,
)
from src.deutschland_card.DeutschlandCardApi import (
    dc_activate_all_coupons_and_get_account_balance,
)

# Der Prozess kann mit dem folgenden Aufruf getestet werden:
(
    count_activated,
    count_skipped,
    count_errored,
    points,
    expiring_points,
    points_expiry,
) = dc_activate_all_coupons_and_get_account_balance(
    get_debug_deutschlandcard_card_number(),
    get_debug_deutschlandcard_geburtsdatum(),
    get_debug_deutschlandcard_plz(),
)

print(f"Aktivierte Coupons: {count_activated}")
print(f"Übersprungene Coupons: {count_skipped}")
print(f"Fehlgeschlagene Coupons: {count_errored}")
print("\n")
print(f"Punkte: {points}")
print(f"Bald verfallende Punkte: {expiring_points}")
print(f"Punkte verfallen am: {points_expiry}")
