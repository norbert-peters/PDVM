import sqlite3
import json
import allgemeines as all  # Enthält all.neue_guid() und all.convert_from_time()
import logging

logger = logging.getLogger(__name__)
logger.info("🔹 PdvmUserDatenbank gestartet")

class PdvmUserDatenbank:
    def __init__(self):
        """Initialisiert die Klasse mit einer spezifischen Datenbank und Tabelle"""
        self.db_name = "PdvmManager.db"
        self.table_name = "benutzerstamm"
        self._erzeuge_tabelle()

    def _erzeuge_tabelle(self):
        """Erstellt die Tabelle, falls sie nicht existiert"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            benutzer TEXT PRIMARY KEY,
            passwort TEXT NOT NULL,
            daten TEXT NOT NULL
        )'''
        cursor.execute(create_table_query)
        conn.commit()
        conn.close()

    def anlegen(self, benutzer=None, passwort=None, daten={}):
        """Erstellt einen neuen Datensatz mit Benutzer und verschlüsseltem Password"""
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
        """Liest einen Datensatz aus der Datenbank"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        select_query = f'SELECT * FROM {self.table_name} WHERE benutzer = ?'
        cursor.execute(select_query, (benutzer,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return result
        else:
            logger.error(f"🔹 Kein Datensatz für Benutzer {benutzer} gefunden.")
            return None  # Oder eine Standardstruktur zurückgeben

    def loeschen(self, benutzer):
        """Löscht einen Datensatz anhand des Benutzers"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        delete_query = f'DELETE FROM {self.table_name} WHERE benutzer = ?'
        cursor.execute(delete_query, (benutzer,))
        conn.commit()
        conn.close()


