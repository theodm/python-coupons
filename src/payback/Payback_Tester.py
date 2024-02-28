from src.config import get_debug_payback_kdnr, get_debug_payback_password
from src.payback.PaybackAPI import payback_activate_all_available_coupons

(
    count_activated,
    count_skipped,
    count_errored,
    points,
    expiring_points,
    points_expiry,
) = payback_activate_all_available_coupons(
    get_debug_payback_kdnr(), get_debug_payback_password()
)

print(f"Aktivierte Coupons: {count_activated}")
print(f"Übersprungene Coupons: {count_skipped}")
print(f"Fehlgeschlagene Coupons: {count_errored}")
print("\n")
print(f"Punkte: {points}")
print(f"Bald verfallende Punkte: {expiring_points}")
print(f"Punkte verfallen am: {points_expiry}")
