# pdvm_benutzer.py
import hashlib
import os
import json

# Logging-Setup
import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmBenutzer gestartet")


# Hier wird die Klasse PdvmBenutzer definiert, die für die Benutzerverwaltung zuständig ist.
# Diese Klasse enthält Methoden zur Passwort-Hashing, Passwort-Überprüfung und zur Konvertierung der Benutzerdaten in JSON-Format.
# Außerdem wird ein statisches Attribut für den Standard-Hash-Algorithmus definiert.
# Diese Klasse ist wichtig für die Sicherheit und Verwaltung der Benutzeranmeldedaten in der Anwendung.


class PdvmBenutzer:
    def __init__(self, benutzer, password_hash, settings_json):
        """
        :param benutzer: Der Benutzername, in der Regel die Email-Adresse.
        :param password_hash: Der gespeicherte Passwort-Hash (z.B. "hash:salt").
        :param settings_json: JSON-Daten als String oder Dict mit zusätzlichen Einstellungen (z.B. GUIDs).
        """
        logger.info("🔹 PdvmBenutzer initialisiert")
        logger.info(f"🔹 in Benutzer angekommen - benutzer: {benutzer}")
#        logger.info(f"🔹 passwort hash: {password_hash}")
#        logger.info(f"🔹 settings_json: {json.dumps(settings_json, indent=4)}")
        self.benutzer = benutzer
        self.password_hash = password_hash
        # Falls settings_json ein String ist, wird er in ein Dict umgewandelt.
        if isinstance(settings_json, str):
            self.settings = json.loads(settings_json)
        else:
            self.settings = settings_json

    @staticmethod
    def hash_password(password, salt=None):
        """
        Erzeugt einen sicheren Hash für das gegebene Passwort.
        Wird kein Salt angegeben, wird ein zufälliges generiert.
        Rückgabeformat: "hash:salt"
        """
        if salt is None:
            # Erzeugen eines zufälligen 16-Byte-Salts (hexadezimal)
            salt = os.urandom(16).hex()
        # Hashing mit SHA-256 (alternativ: PBKDF2, bcrypt o.ä. für mehr Sicherheit)
        hash_obj = hashlib.sha256()
        hash_obj.update((salt + password).encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        return f"{password_hash}:{salt}"

    @staticmethod
    def verify_password(stored_password_hash, provided_password):
        """
        Vergleicht das gegebene Passwort mit dem in der Datenbank gespeicherten Hash.
        Erwartetes Format: "hash:salt"
        """
        try:
            stored_hash, salt = stored_password_hash.split(":")
        except ValueError:
            # Falsches Format
            return False

        hash_obj = hashlib.sha256()
        hash_obj.update((salt + provided_password).encode('utf-8'))
        provided_hash = hash_obj.hexdigest()
        return stored_hash == provided_hash

    def to_json(self):
        """
        Gibt die Benutzerdaten (ohne Passwort) als JSON-String zurück.
        Hier könntest Du auch settings und andere relevante Informationen speichern.
        """
        data = {
            "benutzer": self.benutzer,
            "settings": self.settings
        }
        return json.dumps(data)

