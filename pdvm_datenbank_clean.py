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

    def __init__(self, db_name="PdvmManager.db", table_name="menudaten", historisch=False):
        """
        Initialisiert die Datenbankverbindung.
        
        Args:
            db_name: Name der SQLite-Datenbankdatei
            table_name: Name der Tabelle in der Datenbank
            historisch: Flag für historische Zeitkonvertierung
        """
        self.db_name = db_name
        self.table_name = table_name
        self.historisch = historisch
        
        # Tabelle erstellen falls nicht vorhanden
        self._ensure_table_exists()
        
        logger.info(f"PdvmDatenbank initialisiert: {db_name}.{table_name} (historisch: {historisch})")

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
