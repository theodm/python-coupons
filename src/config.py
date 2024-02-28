import configparser


# Liest die secrets.properties Datei und gibt ein ConfigParser-Objekt zurück.
def read_secrets():
    config = configparser.ConfigParser()
    config.read("secrets.properties")

    return config


# Gibt das Telegram-API-Token aus der secrets.properties Datei zurück.
def get_telegram_token():
    config = read_secrets()
    token = config.get("secrets", "TELEGRAM_API_TOKEN")
    return token


# Gibt die Benutzer-IDs zurück, die Nachrichten erhalten dürfen. Diese sind
# in der secrets.properties Datei definiert. Gibt eine Liste von Strings zurück.
# Nur diese Benutzer dürfen mit dem Bot interagieren.
def get_allowed_user_ids():
    config = read_secrets()
    allowed_user_ids = config.get("secrets", "ALLOWED_USER_IDS")
    return allowed_user_ids.split(",")


# Gibt die DeutschlandCard-Kartennummer zurück. Diese wird nur für Test-Methoden innerhalb des Projekts
# verwendet; nicht innerhalb der vollständigen Anwendung.
def get_debug_deutschlandcard_card_number():
    config = read_secrets()
    card_number = config.get("secrets", "DEBUG_DEUTSCHLANDCARD_CARD_NUMBER")
    return card_number


# Gibt das DeutschlandCard-Geburtsdatum zurück. Diese wird nur für Test-Methoden innerhalb des Projekts
# verwendet; nicht innerhalb der vollständigen Anwendung.
def get_debug_deutschlandcard_geburtsdatum():
    config = read_secrets()
    geburtsdatum = config.get("secrets", "DEBUG_DEUTSCHLANDCARD_GEBURTSDATUM")
    return geburtsdatum


# Gibt das DeutschlandCard-PLZ zurück. Diese wird nur für Test-Methoden innerhalb des Projekts
# verwendet; nicht innerhalb der vollständigen Anwendung.
def get_debug_deutschlandcard_plz():
    config = read_secrets()
    plz = config.get("secrets", "DEBUG_DEUTSCHLANDCARD_PLZ")
    return plz


# Gibt das Payback-Kundennummer zurück. Diese wird nur für Test-Methoden innerhalb des Projekts
# verwendet; nicht innerhalb der vollständigen Anwendung.
def get_debug_payback_kdnr():
    config = read_secrets()
    kdnr = config.get("secrets", "DEBUG_PAYBACK_CARD_NUMBER")
    return kdnr


# Gibt das Payback-Passwort zurück. Diese wird nur für Test-Methoden innerhalb des Projekts
# verwendet; nicht innerhalb der vollständigen Anwendung.
def get_debug_payback_password():
    config = read_secrets()
    kdnr = config.get("secrets", "DEBUG_PAYBACK_PASSWORD")
    return kdnr


# Gibt das geheime Token, welches für den Zugriff auf die DeutschlandCard-API notwendig ist,
# zurück.
def get_deutschlandcard_secret_api_token():
    config = read_secrets()
    dc_api_token = config.get("secrets", "DEUTSCHLANDCARD_SECRET_API_TOKEN")
    return dc_api_token


# Gibt den Benutzernamen für die Authentifizierung gegenüber den Payback-Servern zurück. Kann z.B. über Reverse-Engineering
# der Android-App herausgefunden werden.
def get_payback_basic_auth_username():
    config = read_secrets()
    username = config.get("secrets", "PAYBACK_BASIC_AUTH_USERNAME")
    return username


# Gibt das Passwort für die Authentifizierung gegenüber den Payback-Servern zurück. Kann z.B. über Reverse-Engineering
# der Android-App herausgefunden werden.
def get_payback_basic_auth_credential():
    config = read_secrets()
    credential = config.get("secrets", "PAYBACK_BASIC_AUTH_CREDENTIAL")
    return credential


# Gibt den Principial für die Authentifizierung gegenüber den Payback-Servern zurück. Kann z.B. über Reverse-Engineering
# der Android-App herausgefunden werden.
def get_payback_principal():
    config = read_secrets()
    principal = config.get("secrets", "PAYBACK_PRINCIPAL")
    return principal
