import sqlite3
import json
import os
import re
import bcrypt
import allgemeines as all  # Enthält all.neue_guid() und all.convert_from_time()
import logging
from pd_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmUserDatenbank gestartet")

# Email-Validierung Pattern
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Passwort-Komplexität Pattern
PASSWORD_MIN_LENGTH = 8
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

class PdvmUserDatenbank:
    def __init__(self):
        """Initialisiert die Klasse mit auth.db und sys_benutzer Tabelle"""
        # FIXIERT: auth.db statt Hauptdatenbank verwenden
        import os
        self.db_name = os.path.join("Daten", "auth.db")
        self.table_name = "sys_benutzer"  # User-Management in auth.db
        
        # Debug: DB-Pfad prüfen
        logger.info(f"🔍 PdvmUserDatenbank initialisiert")
        logger.info(f"   DB-Pfad: {self.db_name}")
        logger.info(f"   Existiert: {os.path.exists(self.db_name)}")
        
        # Aktueller User (wird bei Login gesetzt)
        self.current_user = None
        self.current_data = None
    
    @staticmethod
    def normalize_email(email):
        """
        Normalisiert Email-Adresse (case-insensitive)
        
        Args:
            email (str): Email-Adresse
            
        Returns:
            str: Email in Kleinbuchstaben
        """
        if email:
            return email.strip().lower()
        return email

    # _load_database_from_init() und _erzeuge_tabelle() entfernt
    # auth.db und sys_benutzer sind fest vorgegeben und existieren bereits

    def anlegen(self, benutzer=None, passwort=None, daten={}):
        """Erstellt einen neuen Datensatz mit Benutzer und verschlüsseltem Password"""
        # Email normalisieren (case-insensitive)
        benutzer = self.normalize_email(benutzer)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if not benutzer or not passwort:
            logger.error(f"🔹 Benutzer und/oder Passwort fehlen.")
            return False
        json_daten = json.dumps(daten)

        insert_query = f'INSERT INTO {self.table_name} (benutzer, passwort, daten) VALUES (?, ?, ?)'
        cursor.execute(insert_query, (benutzer, passwort, json_daten))
        conn.commit()
        conn.close()
        return True

    def speichern(self, benutzer=None, passwort=None, daten={}):
        """Speichert oder aktualisiert einen Datensatz"""
        if not benutzer or not passwort:
            logger.error(f"🔹 Benutzer und/oder Passwort fehlen.")
            return False        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        json_daten = json.dumps(daten)

        # Prüfen, ob Datensatz existiert
        select_query = f'SELECT COUNT(*) FROM {self.table_name} WHERE benutzer = ?'
        cursor.execute(select_query, (benutzer,))
        result = cursor.fetchone()

        if result[0] > 0:
            update_query = f'UPDATE {self.table_name} SET daten = ? WHERE benutzer = ?'
            cursor.execute(update_query, (json_daten, benutzer, passwort))
        else:
            insert_query = f'INSERT INTO {self.table_name} (benutzer, passwort, daten) VALUES (?, ?)'
            cursor.execute(insert_query, (benutzer, passwort, json_daten))

        conn.commit()
        conn.close()

    def lesen(self, benutzer):
        """Liest einen Datensatz anhand des Benutzers"""
        # Email normalisieren (case-insensitive)
        benutzer = self.normalize_email(benutzer)
        
        logger.info(f"🔍 lesen() für Benutzer: {benutzer}")
        logger.info(f"   DB: {self.db_name}")
        logger.info(f"   Tabelle: {self.table_name}")
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            select_query = f'SELECT * FROM {self.table_name} WHERE benutzer = ?'
            cursor.execute(select_query, (benutzer,))
            result = cursor.fetchone()
            conn.close()

            if result:
                logger.info(f"✅ Benutzer gefunden: {result[0]}")
                logger.info(f"   Spalten: {len(result)}")
                return result
            else:
                logger.warning(f"⚠️ Benutzer nicht gefunden: {benutzer}")
                return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Lesen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def loeschen(self, benutzer):
        """Löscht einen Datensatz anhand des Benutzers"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        delete_query = f'DELETE FROM {self.table_name} WHERE benutzer = ?'
        cursor.execute(delete_query, (benutzer,))
        conn.commit()
        conn.close()
    
    # ============================================================================
    # ERWEITERTE METHODEN - PASSWORD & EMAIL MANAGEMENT
    # ============================================================================
    
    @staticmethod
    def validate_email(email):
        """
        Validiert Email-Format
        
        Args:
            email (str): Email-Adresse
            
        Returns:
            bool: True wenn gültig, False sonst
        """
        if not email:
            return False
        return bool(re.match(EMAIL_REGEX, email))
    
    @staticmethod
    def validate_password_complexity(password):
        """
        Prüft Passwort-Komplexität
        
        Anforderungen:
        - Min. 8 Zeichen
        - Min. 1 Großbuchstabe
        - Min. 1 Kleinbuchstabe
        - Min. 1 Zahl
        - Min. 1 Sonderzeichen (@$!%*?&)
        
        Args:
            password (str): Passwort im Klartext
            
        Returns:
            tuple: (bool: gültig, str: Fehlermeldung oder None)
        """
        if not password:
            return False, "Passwort darf nicht leer sein"
        
        if len(password) < PASSWORD_MIN_LENGTH:
            return False, f"Passwort muss mindestens {PASSWORD_MIN_LENGTH} Zeichen lang sein"
        
        if not re.search(r'[a-z]', password):
            return False, "Passwort muss mindestens einen Kleinbuchstaben enthalten"
        
        if not re.search(r'[A-Z]', password):
            return False, "Passwort muss mindestens einen Großbuchstaben enthalten"
        
        if not re.search(r'\d', password):
            return False, "Passwort muss mindestens eine Zahl enthalten"
        
        if not re.search(r'[@$!%*?&]', password):
            return False, "Passwort muss mindestens ein Sonderzeichen (@$!%*?&) enthalten"
        
        return True, None
    
    @staticmethod
    def hash_password(password):
        """
        Erstellt bcrypt-Hash eines Passworts
        
        Args:
            password (str): Passwort im Klartext
            
        Returns:
            str: Gehashtes Passwort
        """
        if not password:
            raise ValueError("Passwort darf nicht leer sein")
        
        # bcrypt arbeitet mit bytes
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Als String zurückgeben für DB-Speicherung
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed_password):
        """
        Verifiziert Passwort gegen Hash
        
        Args:
            password (str): Passwort im Klartext
            hashed_password (str): Gehashtes Passwort aus DB
            
        Returns:
            bool: True wenn Passwort korrekt, False sonst
        """
        if not password or not hashed_password:
            return False
        
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Fehler bei Passwort-Verifizierung: {e}")
            return False
    
    def change_password(self, benutzer, old_password, new_password):
        """
        Ändert Passwort eines Benutzers
        
        Args:
            benutzer (str): Email des Benutzers
            old_password (str): Altes Passwort (zur Verifizierung)
            new_password (str): Neues Passwort
            
        Returns:
            tuple: (bool: Erfolg, str: Fehlermeldung oder None)
        """
        # Email normalisieren (case-insensitive)
        benutzer = self.normalize_email(benutzer)
        
        # Email validieren
        if not self.validate_email(benutzer):
            return False, "Ungültige Email-Adresse"
        
        # Aktuellen User laden
        user_data = self.lesen(benutzer)
        if not user_data:
            return False, "Benutzer nicht gefunden"
        
        benutzer_db, passwort_hash, daten_json = user_data
        
        # Altes Passwort prüfen
        if not self.verify_password(old_password, passwort_hash):
            return False, "Altes Passwort ist falsch"
        
        # Neues Passwort validieren
        valid, error_msg = self.validate_password_complexity(new_password)
        if not valid:
            return False, error_msg
        
        # Neues Passwort hashen
        new_hash = self.hash_password(new_password)
        
        # Daten-Struktur laden und erweitern
        daten = json.loads(daten_json)
        
        # SECURITY-Gruppe aktualisieren
        if 'SECURITY' not in daten:
            daten['SECURITY'] = {}
        
        # Timestamp für Passwortänderung
        dt = Pdvm_DateTime()
        current_timestamp = dt.PdvmDateTime
        
        daten['SECURITY']['PASSWORD_CHANGE_REQUIRED'] = False
        daten['SECURITY']['LAST_PASSWORD_CHANGE'] = current_timestamp
        
        # Audit-Trail aktualisieren
        if 'AUDIT' not in daten:
            daten['AUDIT'] = {}
        daten['AUDIT']['MODIFIED_AT'] = current_timestamp
        daten['AUDIT']['MODIFIED_BY'] = benutzer
        
        # In DB speichern
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        json_daten = json.dumps(daten, ensure_ascii=False)
        
        update_query = f'UPDATE {self.table_name} SET passwort = ?, daten = ? WHERE benutzer = ?'
        cursor.execute(update_query, (new_hash, json_daten, benutzer))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Passwort geändert für {benutzer}")
        return True, None
    
    def admin_set_password(self, benutzer, new_password, require_change=True):
        """
        Setzt Passwort als Admin (ohne altes Passwort zu prüfen)
        Für: Startpasswort setzen, Passwort zurücksetzen
        
        Args:
            benutzer (str): Email des Benutzers
            new_password (str): Neues Passwort
            require_change (bool): Benutzer muss Passwort beim Login ändern
            
        Returns:
            tuple: (bool: Erfolg, str: Fehlermeldung oder None)
        """
        # Email normalisieren (case-insensitive)
        benutzer = self.normalize_email(benutzer)
        
        # Email validieren
        if not self.validate_email(benutzer):
            return False, "Ungültige Email-Adresse"
        
        # User laden
        user_data = self.lesen(benutzer)
        if not user_data:
            return False, "Benutzer nicht gefunden"
        
        # Neues Passwort validieren
        valid, error_msg = self.validate_password_complexity(new_password)
        if not valid:
            return False, error_msg
        
        # Passwort hashen
        new_hash = self.hash_password(new_password)
        
        # Daten-Struktur laden
        benutzer_db, passwort_hash, uid, daten_json = user_data[0], user_data[1], user_data[2], user_data[3]
        daten = json.loads(daten_json) if daten_json else {}
        
        # SECURITY-Gruppe aktualisieren
        if 'SECURITY' not in daten:
            daten['SECURITY'] = {}
        
        # Timestamp
        dt = Pdvm_DateTime()
        current_timestamp = dt.PdvmDateTime
        
        daten['SECURITY']['PASSWORD_CHANGE_REQUIRED'] = require_change
        daten['SECURITY']['LAST_PASSWORD_CHANGE'] = current_timestamp
        daten['SECURITY']['PASSWORD_SET_BY_ADMIN'] = True
        
        # Audit-Trail
        if 'AUDIT' not in daten:
            daten['AUDIT'] = {}
        daten['AUDIT']['MODIFIED_AT'] = current_timestamp
        daten['AUDIT']['MODIFIED_BY'] = 'ADMIN'
        
        # In DB speichern
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        json_daten = json.dumps(daten, ensure_ascii=False)
        
        update_query = f'UPDATE {self.table_name} SET passwort = ?, daten = ? WHERE benutzer = ?'
        cursor.execute(update_query, (new_hash, json_daten, benutzer))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Passwort gesetzt für {benutzer} (Admin-Aktion, require_change={require_change})")
        return True, None
    
    # ============================================================================
    # GRUPPE/FELD METHODEN (für strukturierten Zugriff)
    # ============================================================================
    
    def get_value(self, benutzer, gruppe, feld):
        """
        Liest einen Wert aus der Gruppe/Feld-Struktur
        
        Args:
            benutzer (str): Email des Benutzers
            gruppe (str): Name der Gruppe (z.B. 'USER', 'SETTINGS')
            feld (str): Name des Feldes (z.B. 'NAME', 'THEME')
            
        Returns:
            Any: Wert oder None wenn nicht gefunden
        """
        user_data = self.lesen(benutzer)
        if not user_data:
            return None
        
        # user_data ist ein Tuple mit 11 Spalten: (benutzer, passwort, uid, daten, ...)
        # Wir brauchen nur daten (Index 3)
        daten_json = user_data[3]
        daten = json.loads(daten_json)
        
        return daten.get(gruppe, {}).get(feld)
    
    def set_value(self, benutzer, gruppe, feld, wert):
        """
        Setzt einen Wert in der Gruppe/Feld-Struktur
        
        Args:
            benutzer (str): Email des Benutzers
            gruppe (str): Name der Gruppe
            feld (str): Name des Feldes
            wert (Any): Zu setzender Wert
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        user_data = self.lesen(benutzer)
        if not user_data:
            logger.error(f"Benutzer {benutzer} nicht gefunden")
            return False
        
        # user_data ist ein Tuple mit 11 Spalten: (benutzer, passwort, uid, daten, ...)
        daten_json = user_data[3]
        daten = json.loads(daten_json)
        
        # Gruppe erstellen falls nicht vorhanden
        if gruppe not in daten:
            daten[gruppe] = {}
        
        # Wert setzen
        daten[gruppe][feld] = wert
        
        # Audit-Trail aktualisieren
        dt = Pdvm_DateTime()
        current_timestamp = dt.PdvmDateTime
        
        if 'AUDIT' not in daten:
            daten['AUDIT'] = {}
        daten['AUDIT']['MODIFIED_AT'] = current_timestamp
        daten['AUDIT']['MODIFIED_BY'] = benutzer
        
        # In DB speichern
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        json_daten = json.dumps(daten, ensure_ascii=False)
        
        update_query = f'UPDATE {self.table_name} SET daten = ? WHERE benutzer = ?'
        cursor.execute(update_query, (json_daten, benutzer))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_all_data(self, benutzer):
        """
        Gibt alle Daten eines Benutzers zurück
        
        Args:
            benutzer (str): Email des Benutzers
            
        Returns:
            dict: Alle Benutzer-Daten oder {} bei Fehler
        """
        # Email normalisieren (case-insensitive)
        benutzer = self.normalize_email(benutzer)
        
        logger.info(f"🔍 get_all_data() für Benutzer: {benutzer}")
        user_data = self.lesen(benutzer)
        if not user_data:
            logger.warning(f"⚠️ Keine Daten gefunden für: {benutzer}")
            return {}
        
        # user_data ist ein Tuple mit 11 Spalten: (benutzer, passwort, uid, daten, ...)
        daten_json = user_data[3]
        result = json.loads(daten_json)
        logger.info(f"✅ Daten geladen: {len(result)} Gruppen")
        return result
    
    def save_all_data(self, benutzer, daten):
        """
        Speichert alle Daten eines Benutzers (vollständiges Update)
        
        Args:
            benutzer (str): Email des Benutzers
            daten (dict): Vollständige Daten-Struktur
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        # Email normalisieren (case-insensitive)
        benutzer = self.normalize_email(benutzer)
        
        user_data = self.lesen(benutzer)
        if not user_data:
            logger.error(f"Benutzer {benutzer} nicht gefunden")
            return False
        
        # user_data ist ein Tuple mit 11 Spalten: (benutzer, passwort, uid, daten, ...)
        # Wir brauchen nichts davon - updaten nur daten-Spalte
        
        # Audit-Trail aktualisieren
        dt = Pdvm_DateTime()
        current_timestamp = dt.PdvmDateTime
        
        if 'AUDIT' not in daten:
            daten['AUDIT'] = {}
        daten['AUDIT']['MODIFIED_AT'] = current_timestamp
        daten['AUDIT']['MODIFIED_BY'] = benutzer
        
        # In DB speichern
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        json_daten = json.dumps(daten, ensure_ascii=False)
        
        update_query = f'UPDATE {self.table_name} SET daten = ? WHERE benutzer = ?'
        cursor.execute(update_query, (json_daten, benutzer))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Benutzerdaten gespeichert für {benutzer}")
        return True
    
    # ============================================================================
    # SECURITY & AUDIT METHODEN
    # ============================================================================
    
    def check_password_change_required(self, benutzer):
        """
        Prüft ob Passwort geändert werden muss
        
        Args:
            benutzer (str): Email des Benutzers
            
        Returns:
            bool: True wenn Änderung erforderlich, False sonst
        """
        value = self.get_value(benutzer, 'SECURITY', 'PASSWORD_CHANGE_REQUIRED')
        return bool(value) if value is not None else False
    
    def set_password_change_required(self, benutzer, required=True):
        """
        Setzt Flag für erzwungene Passwortänderung
        
        Args:
            benutzer (str): Email des Benutzers
            required (bool): True = Änderung erforderlich
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        return self.set_value(benutzer, 'SECURITY', 'PASSWORD_CHANGE_REQUIRED', required)
    
    def update_last_login(self, benutzer):
        """
        Aktualisiert Last-Login Timestamp
        
        Args:
            benutzer (str): Email des Benutzers
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        dt = Pdvm_DateTime()
        current_timestamp = dt.PdvmDateTime
        
        success = self.set_value(benutzer, 'SECURITY', 'LAST_LOGIN', current_timestamp)
        if success:
            # Failed login attempts zurücksetzen bei erfolgreichem Login
            self.set_value(benutzer, 'SECURITY', 'FAILED_LOGIN_ATTEMPTS', 0)
        
        return success
    
    def increment_failed_login(self, benutzer):
        """
        Erhöht Failed-Login Counter
        
        Args:
            benutzer (str): Email des Benutzers
            
        Returns:
            int: Neue Anzahl Failed-Attempts
        """
        current = self.get_value(benutzer, 'SECURITY', 'FAILED_LOGIN_ATTEMPTS')
        if current is None:
            current = 0
        
        new_count = current + 1
        self.set_value(benutzer, 'SECURITY', 'FAILED_LOGIN_ATTEMPTS', new_count)
        
        # Account sperren nach 5 Fehlversuchen
        if new_count >= 5:
            self.set_value(benutzer, 'SECURITY', 'ACCOUNT_LOCKED', True)
            logger.warning(f"⚠️ Account gesperrt nach {new_count} Fehlversuchen: {benutzer}")
        
        return new_count
    
    def is_account_locked(self, benutzer):
        """
        Prüft ob Account gesperrt ist
        
        Args:
            benutzer (str): Email des Benutzers
            
        Returns:
            bool: True wenn gesperrt, False sonst
        """
        value = self.get_value(benutzer, 'SECURITY', 'ACCOUNT_LOCKED')
        return bool(value) if value is not None else False
    
    def unlock_account(self, benutzer):
        """
        Entsperrt Account (nur durch Admin)
        
        Args:
            benutzer (str): Email des Benutzers
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        success1 = self.set_value(benutzer, 'SECURITY', 'ACCOUNT_LOCKED', False)
        success2 = self.set_value(benutzer, 'SECURITY', 'FAILED_LOGIN_ATTEMPTS', 0)
        
        if success1 and success2:
            logger.info(f"✅ Account entsperrt: {benutzer}")
        
        return success1 and success2


