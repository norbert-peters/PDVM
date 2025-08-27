# -*- coding: utf-8 -*-
# pdvm_datenbank.py

import sqlite3
import json
import allgemeines as all  # Enthält all.neue_guid(), all.convert_from_time() 
import pdvm_datetime as dt  # Enthält PdvmDateTimeNow()

# looging setup
import logging
logger = logging.getLogger(__name__)


class PdvmDatenbank:
    SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, db_name="PdvmManager.db", table_name="menudaten", historisch=False):
        """Initialisiert die Klasse mit einer spezifischen Datenbank und Tabelle"""
        self.db_name    = db_name
        self.table_name = table_name
        self.hist       = historisch

    def _erzeuge_tabelle(self):
        """Erstellt die Tabelle, falls sie nicht existiert"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            uid TEXT PRIMARY KEY,
            daten TEXT NOT NULL
        )'''
        cursor.execute(create_table_query)
        conn.commit()
        conn.close()

    def _update_last_change(self):
        """
        Aktualisiert in der Systemsteuerung unter SYSTEM_USER_ID
        das Feld 'last_change', 'row_count' und 'size_bytes' für diese Tabelle.
        """
        # Berechne aktuelle Metriken für diese Tabelle
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Zeilenanzahl
        cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        row_count = cursor.fetchone()[0]
        logging.log(logging.INFO,f"Anzahl der Zeilen in {self.table_name}: {row_count}")
        # Gesamtgröße der JSON-Daten in Bytes
        cursor.execute(f"SELECT SUM(LENGTH(daten)) FROM {self.table_name}")
        size_bytes = cursor.fetchone()[0] or 0
        logging.log(logging.INFO,f"Gesamtgröße der Daten in {self.table_name}: {size_bytes} Bytes")
        # Aktuelles Datum und Uhrzeit
        dt_instance = dt.Pdvm_DateTime("DEU")
        dt_instance.PdvmDateTime = 2025106.0    # fiktives Datum, damit intern Struktiur erzeugt wird
        current_time = dt_instance.PdvmDateTimeNow()
        logging.log(logging.INFO,f"Aktuelle Zeit: {current_time}")
        conn.close()

        # Lade aktuellen Systemsteuerungs-Datensatz
        sys_db = PdvmDatenbank(self.db_name, table_name="systemsteuerung", historisch=False)
        sys_record = sys_db.lesen(self.SYSTEM_USER_ID) 
        logging.log(logging.INFO,f"Systemsteuerung-Datensatz: {sys_record}")

        # WICHTIG: Null-Prüfung für sys_record
        if sys_record is None:
            logging.log(logging.WARNING, f"Systemsteuerung-Datensatz für {self.SYSTEM_USER_ID} ist None, erstelle neuen Datensatz")
            sys_record = {}
        
        # Stelle sicher, dass der Eintrag für diese Tabelle existiert
        sys_record[self.table_name] = sys_record.get(self.table_name, {})
        # Setze Metriken
        logging.log(logging.INFO,f"Setze Metriken für {self.table_name} in der Systemsteuerung")
        sys_record[self.table_name].update({
            "last_change":    current_time, # Aktuelles Datum und Uhrzeit
            "row_count":      row_count,
            "size_bytes":     size_bytes
        })

        # Schreibe zurück in die Systemsteuerung - hier ohne die Methode schreiben . sonst loop
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        json_daten = json.dumps(sys_record)

        # Prüfen, ob Datensatz existiert
        select_query = f'SELECT COUNT(*) FROM {"systemsteuerung"} WHERE uid = ?'
        cursor.execute(select_query, (self.SYSTEM_USER_ID,))
        result = cursor.fetchone()

        if result[0] > 0:
            update_query = f'UPDATE {"systemsteuerung"} SET daten = ? WHERE uid = ?'
            cursor.execute(update_query, (json_daten, self.SYSTEM_USER_ID))
        else:
            insert_query = f'INSERT INTO {"systemsteuerung"} (uid, daten) VALUES (?, ?)'
            cursor.execute(insert_query, (self.SYSTEM_USER_ID, json_daten))

        conn.commit()
        conn.close()


    def anlegen(self, daten):
        """Erstellt einen neuen Datensatz mit einer GUID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        uid = all.neue_guid()  # Neue GUID generieren
        json_daten = json.dumps(daten)

        insert_query = f'INSERT INTO {self.table_name} (uid, daten) VALUES (?, ?)'
        cursor.execute(insert_query, (uid, json_daten))
        conn.commit()
        conn.close()

        # Systemsteuerung aktualisieren
        self._update_last_change()
        return uid

    def speichern(self, guid, daten):
        """Speichert oder aktualisiert einen Datensatz"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        json_daten = json.dumps(daten)

        # Prüfen, ob Datensatz existiert
        select_query = f'SELECT COUNT(*) FROM {self.table_name} WHERE uid = ?'
        cursor.execute(select_query, (guid,))
        result = cursor.fetchone()

        if result[0] > 0:
            update_query = f'UPDATE {self.table_name} SET daten = ? WHERE uid = ?'
            cursor.execute(update_query, (json_daten, guid))
        else:
            insert_query = f'INSERT INTO {self.table_name} (uid, daten) VALUES (?, ?)'
            cursor.execute(insert_query, (guid, json_daten))

        conn.commit()
        conn.close()

        # Systemsteuerung aktualisieren
        logging.log(logging.INFO,f"Systemsteuerung aktualisieren für {self.table_name}")
        self._update_last_change()

    def set_historisch_kennzeichen(self, historisch=False):
        """
        Setzt das historische Kennzeichen für diese Tabelle in der Systemsteuerung.
        Wird von PdvmCentralDatenbank verwendet um zu ermitteln, ob Daten historisch sind.
        """
        try:
            # Lade aktuellen Systemsteuerungs-Datensatz
            sys_db = PdvmDatenbank(self.db_name, table_name="systemsteuerung", historisch=False)
            sys_record = sys_db.lesen(self.SYSTEM_USER_ID) 
            
            # WICHTIG: Null-Prüfung für sys_record
            if sys_record is None:
                logging.log(logging.INFO, f"Erstelle neuen Systemsteuerung-Datensatz für {self.SYSTEM_USER_ID}")
                sys_record = {}
            
            # Stelle sicher, dass der Eintrag für diese Tabelle existiert
            sys_record[self.table_name] = sys_record.get(self.table_name, {})
            
            # Setze historisch-Kennzeichen
            sys_record[self.table_name]["historisch"] = bool(historisch)
            
            logging.log(logging.INFO, f"Setze historisch-Kennzeichen für {self.table_name}: {historisch}")
            
            # Schreibe zurück in die Systemsteuerung
            sys_db.speichern(self.SYSTEM_USER_ID, sys_record)
            
        except Exception as e:
            logging.log(logging.ERROR, f"Fehler beim Setzen des historisch-Kennzeichens für {self.table_name}: {e}")

    def get_historisch_kennzeichen(self):
        """
        Liest das historische Kennzeichen für diese Tabelle aus der Systemsteuerung.
        """
        try:
            # Lade aktuellen Systemsteuerungs-Datensatz
            sys_db = PdvmDatenbank(self.db_name, table_name="systemsteuerung", historisch=False)
            sys_record = sys_db.lesen(self.SYSTEM_USER_ID) 
            
            if sys_record and isinstance(sys_record, dict):
                table_settings = sys_record.get(self.table_name, {})
                if isinstance(table_settings, dict):
                    return bool(table_settings.get('historisch', False))
            
            return False
            
        except Exception as e:
            logging.log(logging.ERROR, f"Fehler beim Lesen des historisch-Kennzeichens für {self.table_name}: {e}")
            return False

    def loeschen(self, guid):
        """Löscht einen Datensatz anhand der GUID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        delete_query = f'DELETE FROM {self.table_name} WHERE uid = ?'
        cursor.execute(delete_query, (guid,))
        conn.commit()
        conn.close()

        # Systemsteuerung aktualisieren
        self._update_last_change()

    def lesen(self, guid):
        """Liest einen Datensatz aus der Datenbank"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        select_query = f'SELECT daten FROM {self.table_name} WHERE uid = ?'
        cursor.execute(select_query, (guid,))
        result = cursor.fetchone()
        conn.close()

        if result:
            raw = result[0]
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                start = max(0, e.pos - 40)
                end   = min(len(raw), e.pos + 40)
                logging.log(logging.INFO,"JSONDecodeError:", e)
                logging.log(logging.INFO,"…", raw[start:end], "…")
                raise
            # Führe time-konvertierungen bei historischen Daten durch
            return all.convert_from_time(data) if self.hist else data
        else:
            logging.log(logging.INFO,f"GUID {guid} nicht gefunden.")
            return None

    def lesen_alle(self):
        """Liest alle Datensätze aus der Tabelle"""
        logging.log(logging.INFO,f"Alle Datensätze aus {self.table_name} lesen")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        select_query = f'SELECT * FROM {self.table_name}'
        cursor.execute(select_query)
        rows = cursor.fetchall()
        conn.close()

        return [
            {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            for row in rows
        ]

if __name__ == "__main__":
    daten = {
        "0d10a0d0-b1a5-4544-b284-e8a09ca979b5": {
            "last_created_at":  "2025-04-17T11:05:00Z",
            "stichtag":         2025006.0,
            "last_accessed":    "2025-04-18T09:30:00Z",
            "filters":          { "Familienname": "Müller", "Geburtsdatum": {"from":"1950-01-01","to":"1970-12-31"} },
            "sort_order":       [ { "column": "Familienname", "dir": "asc" } ],
            "page":             { "offset": 0, "limit": 50 },
            "cache_expires_at": "2025-04-18T10:05:00Z",
            "status":           "ready",
            "row_count":        234
        },
        "626a2c5a-2d03-4cfd-8c24-c36badedc3b2": {
            "last_created_at":  "2025-04-17T11:05:00Z",
            "stichtag":         2025006.0,
            "last_accessed":    "2025-04-18T09:30:00Z",
            "filters":          { "Familienname": "Müller", "Geburtsdatum": {"from":"1950-01-01","to":"1970-12-31"} },
            "sort_order":       [ { "column": "Familienname", "dir": "asc" } ],
            "page":             { "offset": 0, "limit": 50 },
            "cache_expires_at": "2025-04-18T10:05:00Z",
            "status":           "ready",
            "row_count":        234
        }
    }


    # Beispielhafte Nutzung der Klasse
#    db = PdvmDatenbank("PdvmManager.db", "beschreibungen", hist=False)
#    db._erzeuge_tabelle()  # Tabelle erstellen, falls nicht vorhanden
#    logging.log(logging.INFO,f"Tabelle {db.table_name} erstellt oder existiert bereits.")

#    uid = db.anlegen({"Test": {}})
#    uid = "dded74a4-40d0-4861-ab9b-f6cc08e75bec"
#    uid = "00000000-0000-0000-0000-000000000001"
#    logging.log(logging.INFO,f"Erstellte GUID: {uid}")

    # Speichern eines Datensatzes
#    db.speichern(uid, daten)
#    logging.log(logging.INFO,f"Datensatz mit GUID {uid} gespeichert.")

    # Lesen eines Datensatzes
#    daten = db.lesen(uid)
#    logging.log(logging.INFO,f"Gelesene Daten für GUID {uid}: {daten}")

    # Löschen eines Datensatzes
    #db.loeschen(uid)
    #logging.log(logging.INFO,f"Datensatz mit GUID {uid} gelöscht.")