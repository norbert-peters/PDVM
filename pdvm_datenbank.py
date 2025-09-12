# -*- coding: utf-8 -*-
# pdvm_datenbank.py - BEREINIGTE LINEARE VERSION
"""
Saubere, lineare Datenbankschicht ohne Redundanzen und Reparatur-Mechanismen.

ARCHITEKTUR:
- Einfache CRUD-Operationen: speichern, lesen, loeschen, alle_lesen
- Automatic last_modified mit pdvm_datetime 
- Linear: Dict → JSON → DB und DB → JSON → Dict
- Keine Reparatur-Mechanismen, keine redundanten Methoden
- Basis-Layer für pdvm_central_datenbank.py
"""

import sqlite3
import json
import allgemeines as all  # Enthält all.neue_guid(), all.convert_from_time() 
import pdvm_datetime as dt  # Enthält PdvmDateTimeNow()
import logging

logger = logging.getLogger(__name__)


class PdvmDatenbank:
    """
    Basis-Datenbankschicht mit linearen CRUD-Operationen.
    Verwaltet JSON-Daten mit automatischem last_modified Zeitstempel.
    """
    SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, table_name="menudaten"):
        """
        Initialisiert die Datenbankverbindung.
        
        Args:
            table_name: Name der Tabelle (MUSS angegeben werden - kein Fallback)
        """
        if not table_name:
            raise ValueError("❌ Tabellenname muss angegeben werden - keine Fallback-Tabellen!")
            
        # Datenbankname aus PdvmInit.json laden
        self.db_name = self._load_database_from_init()
        self.table_name = table_name
        
        # Tabelle erstellen falls nicht vorhanden
        self._ensure_table_exists()
        
        # Historisch-Status aus Datenbank ermitteln
        self.historisch = self._ermittle_historisch_status()
        
        logger.info(f"PdvmDatenbank initialisiert: {self.db_name}.{table_name} (historisch: {self.historisch})")

    def _load_database_from_init(self):
        """
        Lädt den Datenbanknamen aus PdvmInit.json.
        
        Erstellt die Datei falls sie nicht existiert und wirft einen Fehler.
        
        Returns:
            str: Name der Datenbankdatei
            
        Raises:
            ValueError: Wenn PdvmInit.json nicht existiert oder fehlerhaft ist
        """
        import os
        
        init_file_path = "PdvmInit.json"
        
        # Prüfe ob Datei existiert
        if not os.path.exists(init_file_path):
            # Erstelle Standard-PdvmInit.json
            init_data = {
                "ROOT": {
                    "datenbank": "XXX",
                    "lizenz": "00000000-0000-0000-0000-000000000000"
                }
            }
            
            try:
                with open(init_file_path, 'w', encoding='utf-8') as f:
                    json.dump(init_data, f, ensure_ascii=False, indent=4)
                logger.info(f"PdvmInit.json erstellt: {init_file_path}")
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von PdvmInit.json: {e}")
            
            raise ValueError("❌ Grunddaten, wie Datenbank etc. in PdvmInit.json eintragen.")
        
        # Lade und parse PdvmInit.json
        try:
            with open(init_file_path, 'r', encoding='utf-8') as f:
                init_data = json.load(f)
            
            # Validiere Struktur
            if 'ROOT' not in init_data:
                raise ValueError("❌ PdvmInit.json: 'ROOT' Sektion fehlt")
            
            if 'datenbank' not in init_data['ROOT']:
                raise ValueError("❌ PdvmInit.json: 'datenbank' in ROOT Sektion fehlt")
            
            db_name = init_data['ROOT']['datenbank']
            
            # Prüfe ob Datenbank-Wert gesetzt ist
            if db_name == "XXX" or not db_name.strip():
                raise ValueError("❌ Grunddaten, wie Datenbank etc. in PdvmInit.json eintragen.")
            
            logger.debug(f"Datenbank aus PdvmInit.json geladen: {db_name}")
            return db_name
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parsing-Fehler in PdvmInit.json: {e}")
            raise ValueError("❌ PdvmInit.json ist fehlerhaft formatiert")
        except Exception as e:
            logger.error(f"Fehler beim Laden von PdvmInit.json: {e}")
            raise ValueError(f"❌ Fehler beim Laden von PdvmInit.json: {e}")

    def _ensure_table_exists(self):
        """Erstellt die Tabelle falls sie nicht existiert."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            uid TEXT PRIMARY KEY,
            daten TEXT NOT NULL,
            last_modified TEXT NOT NULL DEFAULT ''
        )'''
        
        cursor.execute(create_table_query)
        conn.commit()
        conn.close()
        
        logger.debug(f"Tabelle {self.table_name} sichergestellt")

    def _ermittle_historisch_status(self):
        """
        Ermittelt historisch-Status aus der Datenbank.
        
        Versucht zuerst mit aktueller GUID, dann mit SYSTEM_USER_ID.
        Falls kein Datensatz gefunden wird, ist historisch=False.
        
        Returns:
            bool: True wenn historische Tabelle, False sonst
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Versuche Datensatz zu finden (zuerst aktueller, dann SYSTEM_USER_ID)
            for uid in [getattr(self, 'guid', None), self.SYSTEM_USER_ID]:
                if uid:
                    cursor.execute(f"SELECT historisch FROM {self.table_name} WHERE uid = ?", (uid,))
                    result = cursor.fetchone()
                    if result:
                        conn.close()
                        return bool(result[0])
            
            # Kein Datensatz gefunden = nicht historisch
            conn.close()
            return False
            
        except Exception as e:
            logger.warning(f"Konnte historisch-Status nicht ermitteln: {e}")
            return False

    def get_historisch_status(self):
        """
        Öffentliche Methode um historisch-Status abzufragen.
        
        Returns:
            bool: True wenn historische Tabelle, False sonst
        """
        return self.historisch

    def _get_current_timestamp(self):
        """
        Erstellt aktuellen Zeitstempel im PDVM-Format.
        
        Returns:
            str: Zeitstempel im PDVM-Format
        """
        try:
            # Erstelle DateTime-Instanz und hole aktuellen Zeitstempel
            dt_instance = dt.Pdvm_DateTime("DEU")  # Default auf DEU, kann später erweitert werden
            current_time = dt_instance.PdvmDateTimeNow()
            return str(current_time)
        except Exception as e:
            logger.warning(f"Fehler beim Erstellen des Zeitstempels: {e}")
            return ""

    def anlegen(self, daten):
        """
        Erstellt einen neuen Datensatz mit automatisch generierter GUID.
        
        Args:
            daten (dict): Daten-Dictionary das gespeichert werden soll
            
        Returns:
            str: Die neu generierte GUID
        """
        if not isinstance(daten, dict):
            raise ValueError("Daten müssen ein Dictionary sein")
            
        # Neue GUID generieren
        uid = all.neue_guid()
        
        # Datensatz speichern
        self.speichern(uid, daten)
        
        logger.info(f"Neuer Datensatz angelegt: {uid}")
        return uid

    def speichern(self, guid, daten):
        """
        Speichert oder aktualisiert einen Datensatz.
        
        Args:
            guid (str): GUID des Datensatzes
            daten (dict): Daten-Dictionary das gespeichert werden soll
        """
        if not isinstance(daten, dict):
            raise ValueError("Daten müssen ein Dictionary sein")
        if not guid:
            raise ValueError("GUID darf nicht leer sein")
        
        # Dict → JSON konvertieren
        json_daten = json.dumps(daten, ensure_ascii=False, indent=None)
        
        # Aktueller Zeitstempel
        timestamp = self._get_current_timestamp()
        
        # In Datenbank speichern
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Prüfen ob Datensatz existiert
        cursor.execute(f'SELECT COUNT(*) FROM {self.table_name} WHERE uid = ?', (guid,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            # Update
            cursor.execute(
                f'UPDATE {self.table_name} SET daten = ?, last_modified = ? WHERE uid = ?',
                (json_daten, timestamp, guid)
            )
            logger.debug(f"Datensatz aktualisiert: {guid}")
        else:
            # Insert
            cursor.execute(
                f'INSERT INTO {self.table_name} (uid, daten, last_modified) VALUES (?, ?, ?)',
                (guid, json_daten, timestamp)
            )
            logger.debug(f"Datensatz eingefügt: {guid}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Datensatz gespeichert: {guid} ({len(json_daten)} Zeichen)")

    def lesen(self, guid):
        """
        Liest einen Datensatz aus der Datenbank.
        
        Args:
            guid (str): GUID des Datensatzes
            
        Returns:
            dict|None: Daten-Dictionary oder None wenn nicht gefunden
        """
        if not guid:
            raise ValueError("GUID darf nicht leer sein")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT daten FROM {self.table_name} WHERE uid = ?', (guid,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            raw_json = result[0]
            
            try:
                # JSON → Dict konvertieren
                data = json.loads(raw_json)
                
                # Historische Zeitkonvertierung falls erforderlich
                if self.historisch:
                    data = all.convert_from_time(data)
                
                logger.debug(f"Datensatz gelesen: {guid}")
                return data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON-Parsing-Fehler für GUID {guid}: {e}")
                raise
        else:
            logger.debug(f"Datensatz nicht gefunden: {guid}")
            return None

    def loeschen(self, guid):
        """
        Löscht einen Datensatz aus der Datenbank.
        
        Args:
            guid (str): GUID des Datensatzes
            
        Returns:
            bool: True wenn gelöscht, False wenn nicht gefunden
        """
        if not guid:
            raise ValueError("GUID darf nicht leer sein")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f'DELETE FROM {self.table_name} WHERE uid = ?', (guid,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        success = deleted_count > 0
        if success:
            logger.info(f"Datensatz gelöscht: {guid}")
        else:
            logger.debug(f"Datensatz zum Löschen nicht gefunden: {guid}")
        
        return success

    def alle_lesen(self):
        """
        Liest alle Datensätze aus der Tabelle.
        
        Returns:
            list[dict]: Liste aller Datensätze mit uid, daten, last_modified
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT uid, daten, last_modified FROM {self.table_name}')
        results = cursor.fetchall()
        conn.close()
        
        datensaetze = []
        for row in results:
            uid, raw_json, last_modified = row
            
            try:
                # JSON → Dict konvertieren
                data = json.loads(raw_json)
                
                # Historische Zeitkonvertierung falls erforderlich
                if self.historisch:
                    data = all.convert_from_time(data)
                
                datensaetze.append({
                    'uid': uid,
                    'daten': data,
                    'last_modified': last_modified
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON-Parsing-Fehler für GUID {uid}: {e}")
                # Fehlerhafte Datensätze überspringen
                continue
        
        logger.info(f"Alle Datensätze gelesen: {len(datensaetze)} von {len(results)} erfolgreich")
        return datensaetze

    def get_table_info(self):
        """
        Gibt Informationen über die Tabelle zurück.
        
        Returns:
            dict: Statistiken über die Tabelle
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Anzahl Datensätze
        cursor.execute(f'SELECT COUNT(*) FROM {self.table_name}')
        row_count = cursor.fetchone()[0]
        
        # Gesamtgröße der Daten
        cursor.execute(f'SELECT SUM(LENGTH(daten)) FROM {self.table_name}')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'table_name': self.table_name,
            'row_count': row_count,
            'total_size_bytes': total_size,
            'historisch': self.historisch
        }
