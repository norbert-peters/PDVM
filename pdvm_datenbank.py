# -*- coding: utf-8 -*-
# v2_pdvm_datenbank.py - V2.0 VERSION (KOPIE VON pdvm_datenbank.py)
"""
V2.0 Datenbankschicht - Identisch mit pdvm_datenbank.py
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

    # Liste der zentralen System-Tabellen
    SYSTEM_TABLES = {
        'sys_beschreibungen',
        'sys_dialogdaten',
        'sys_dropdowndaten',
        'sys_framedaten',
        'sys_menudaten',
        'sys_viewdaten'
    }

    def __init__(self, table_name="sys_menudaten"):
        """
        V2.0: Initialisiert die Datenbankverbindung.
        
        DB-Pfad wird aus GCS geholt (gcs.db_path) - zentrale Konfiguration!
        
        SYSTEM-DB ROUTING:
        - System-Tabellen → pdvm_system.db (aus Mandanten METADATEN.SYSTEM_DB)
        - Andere Tabellen → Mandanten-DB (gcs.db_path)
        
        Args:
            table_name: Name der Tabelle (Standard: sys_menudaten)
        
        Raises:
            ValueError: Wenn table_name fehlt oder GCS nicht initialisiert
            RuntimeError: Wenn SYSTEM_DB nicht konfiguriert ist (bei System-Tabellen)
        """
        if not table_name:
            raise ValueError("❌ Tabellenname muss angegeben werden!")
        
        # V2.0: DB-Pfad aus GCS holen (zentrale Konfiguration)
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            raise ValueError("❌ GCS nicht initialisiert! DB-Pfad nicht verfügbar.")
        
        if not hasattr(gcs, 'db_path') or not gcs.db_path:
            raise ValueError("❌ GCS.db_path nicht gesetzt!")
        
        # SYSTEM-DB ROUTING: Prüfe ob System-Tabelle
        self.table_name = table_name
        self.is_system_table = table_name in self.SYSTEM_TABLES
        
        if self.is_system_table:
            # System-Tabelle → pdvm_system.db
            self.db_name = self._get_system_db_path(gcs)
            logger.info(f"✅ System-Tabelle: {self.db_name} → {table_name}")
        else:
            # Mandanten-Tabelle → Mandanten-DB
            self.db_name = gcs.db_path
            logger.info(f"✅ Mandanten-Tabelle: {gcs.db_path} → {table_name}")
        
        # Tabelle erstellen falls nicht vorhanden
        self._ensure_table_exists()
        
        # Historisch-Status aus Datenbank ermitteln
        self.historisch = self._ermittle_historisch_status()
        
        logger.info(f"PdvmDatenbank initialisiert: {self.db_name}.{table_name} (historisch: {self.historisch})")

    def _ensure_table_exists(self):
        """Erstellt die Tabelle falls sie nicht existiert mit vollständiger PDVM-Struktur."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            uid          TEXT    PRIMARY KEY,
            daten        TEXT    NOT NULL,
            name         TEXT,
            historisch   INTEGER DEFAULT 0,
            source_hash  TEXT,
            sec_id       TEXT,
            gilt_bis     TEXT    DEFAULT '9999365.00000',
            created_at   TEXT,
            modified_at  TEXT,
            daten_backup TEXT
        )'''
        
        cursor.execute(create_table_query)
        conn.commit()
        conn.close()
        
        logger.debug(f"Tabelle {self.table_name} mit vollständiger PDVM-Struktur sichergestellt")
    
    def _get_system_db_path(self, gcs):
        """
        Ermittelt Pfad zur System-Datenbank aus Mandanten-Metadaten.
        
        Liest METADATEN.SYSTEM_DB aus gcs._mandant_data und baut DB-Pfad.
        
        Args:
            gcs: GlobalCentralSystemsteuerung Instanz
            
        Returns:
            str: Vollständiger Pfad zur System-DB (z.B. "Daten/pdvm_system.db")
            
        Raises:
            RuntimeError: Wenn SYSTEM_DB nicht konfiguriert ist
        """
        import os
        
        try:
            # Hole SYSTEM_DB aus Mandanten-Metadaten
            metadaten = gcs._mandant_data.get('METADATEN', {})
            system_db_name = metadaten.get('SYSTEM_DB')
            
            if not system_db_name:
                logger.error("❌ KRITISCH: METADATEN.SYSTEM_DB nicht in Mandanten-Daten definiert!")
                logger.error("   System-Tabelle kann nicht geladen werden.")
                logger.error("   Bitte METADATEN.SYSTEM_DB in Mandanten-Daten setzen (z.B. 'pdvm_system')")
                raise RuntimeError(
                    "SYSTEM_DB nicht konfiguriert!\n\n"
                    "Die System-Datenbank ist nicht in den Mandanten-Daten konfiguriert.\n"
                    "Bitte setzen Sie METADATEN.SYSTEM_DB in den Mandanten-Daten.\n\n"
                    "Beispiel: METADATEN.SYSTEM_DB = 'pdvm_system'\n\n"
                    "Das System kann ohne System-Datenbank nicht gestartet werden."
                )
            
            # Baue DB-Pfad (System-DB ist eine Ebene höher als Mandanten-DB)
            # Mandanten-DB: z.B. "Daten/mandant_001/datenbank.db"
            # System-DB:    z.B. "Daten/pdvm_system.db"
            mandant_dir = os.path.dirname(gcs.db_path)  # z.B. "Daten/mandant_001"
            daten_dir = os.path.dirname(mandant_dir)     # z.B. "Daten"
            system_db_path = os.path.join(daten_dir, f"{system_db_name}.db")
            
            # Prüfe ob System-DB existiert
            if not os.path.exists(system_db_path):
                logger.error(f"❌ KRITISCH: System-Datenbank nicht gefunden: {system_db_path}")
                logger.error("   Bitte erstellen Sie die System-Datenbank mit create_pdvm_system_db.py")
                raise RuntimeError(
                    f"System-Datenbank nicht gefunden!\n\n"
                    f"Erwartet: {system_db_path}\n"
                    f"Konfiguriert in METADATEN.SYSTEM_DB: {system_db_name}\n\n"
                    f"Bitte erstellen Sie die System-Datenbank mit:\n"
                    f"  python create_pdvm_system_db.py\n\n"
                    f"Das System kann ohne System-Datenbank nicht gestartet werden."
                )
            
            logger.debug(f"   System-DB gefunden: {system_db_path}")
            return system_db_path
            
        except KeyError as e:
            logger.error(f"❌ Fehler beim Zugriff auf Mandanten-Metadaten: {e}")
            raise RuntimeError(f"Fehler beim Zugriff auf METADATEN: {e}")

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
            
            # Prüfe ob historisch-Spalte existiert (V1.0 Schema)
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'historisch' not in columns:
                # V2.0 Schema: keine historisch-Spalte → Standard False (oder 0)
                conn.close()
                logger.debug(f"{self.table_name}: Keine historisch-Spalte (V2.0) → historisch=0")
                return 0  # Nicht historisch
            
            # Versuche Datensatz zu finden (zuerst aktueller, dann SYSTEM_USER_ID)
            for uid in [getattr(self, 'guid', None), self.SYSTEM_USER_ID]:
                if uid:
                    cursor.execute(f"SELECT historisch FROM {self.table_name} WHERE uid = ?", (uid,))
                    result = cursor.fetchone()
                    if result:
                        conn.close()
                        return int(result[0])  # 0 oder 1
            
            # Kein Datensatz gefunden = nicht historisch
            conn.close()
            return 0
            
        except Exception as e:
            logger.warning(f"Konnte historisch-Status nicht ermitteln: {e}")
            return 0

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
            # Update (created_at bleibt unverändert)
            cursor.execute(
                f'UPDATE {self.table_name} SET daten = ?, modified_at = ? WHERE uid = ?',
                (json_daten, timestamp, guid)
            )
            logger.debug(f"Datensatz aktualisiert: {guid}")
        else:
            # Insert (created_at wird mit aktuellem Zeitstempel gesetzt)
            cursor.execute(
                f'INSERT INTO {self.table_name} (uid, daten, created_at, modified_at) VALUES (?, ?, ?, ?)',
                (guid, json_daten, timestamp, timestamp)
            )
            logger.debug(f"Datensatz eingefügt: {guid} (created_at={timestamp})")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Datensatz gespeichert: {guid} ({len(json_daten)} Zeichen)")
    
    def set_name(self, guid, name):
        """
        Setzt die name-Spalte für einen Datensatz.
        
        Args:
            guid (str): GUID des Datensatzes
            name (str): Name-Wert
        """
        if not guid:
            raise ValueError("GUID darf nicht leer sein")
        if not name:
            raise ValueError("Name darf nicht leer sein")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Prüfen ob Datensatz existiert
        cursor.execute(f'SELECT COUNT(*) FROM {self.table_name} WHERE uid = ?', (guid,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            # Update name
            cursor.execute(
                f'UPDATE {self.table_name} SET name = ? WHERE uid = ?',
                (name, guid)
            )
            logger.debug(f"Name aktualisiert für {guid}: {name}")
        else:
            # Name kann nur für existierende Datensätze gesetzt werden
            raise ValueError(f"Datensatz {guid} existiert nicht - kann name nicht setzen")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Name gesetzt für {guid}: {name}")

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
            list[dict]: Liste aller Datensätze mit uid, daten, modified_at (falls vorhanden)
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Prüfe ob modified_at Spalte existiert
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        has_modified_at = 'modified_at' in columns
        
        # Query anpassen je nach Spalten-Verfügbarkeit
        if has_modified_at:
            cursor.execute(f'SELECT uid, daten, modified_at FROM {self.table_name}')
        else:
            cursor.execute(f'SELECT uid, daten FROM {self.table_name}')
            logger.debug(f"⚠️ Tabelle {self.table_name} hat keine 'modified_at' Spalte")
        
        results = cursor.fetchall()
        conn.close()
        
        datensaetze = []
        for row in results:
            if has_modified_at:
                uid, raw_json, modified_at = row
            else:
                uid, raw_json = row
                modified_at = None
            
            try:
                # JSON → Dict konvertieren
                data = json.loads(raw_json)
                
                # Historische Zeitkonvertierung falls erforderlich
                if self.historisch:
                    data = all.convert_from_time(data)
                
                datensaetze.append({
                    'uid': uid,
                    'daten': data,
                    'modified_at': modified_at
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

    def get_name(self, guid):
        """
        Liest den 'name' Wert für eine GUID.
        
        Args:
            guid (str): GUID des Datensatzes
            
        Returns:
            str|None: Name-Wert oder None wenn nicht gefunden
        """
        if not guid:
            raise ValueError("GUID darf nicht leer sein")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT name FROM {self.table_name} WHERE uid = ?', (guid,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            name = result[0]
            logger.debug(f"Name gelesen: {guid} → '{name}'")
            return name if name else ""
        else:
            logger.debug(f"Datensatz nicht gefunden: {guid}")
            return None

    def set_name(self, guid, name_value):
        """
        Setzt den 'name' Wert für eine GUID.
        
        Args:
            guid (str): GUID des Datensatzes
            name_value (str): Neuer Name-Wert
            
        Returns:
            bool: True wenn erfolgreich, False wenn GUID nicht existiert
        """
        if not guid:
            raise ValueError("GUID darf nicht leer sein")
        
        # Sicherstellen dass name_value ein String ist
        name_str = str(name_value) if name_value is not None else ""
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Prüfe ob GUID existiert
        cursor.execute(f'SELECT COUNT(*) FROM {self.table_name} WHERE uid = ?', (guid,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            cursor.execute(
                f'UPDATE {self.table_name} SET name = ? WHERE uid = ?',
                (name_str, guid)
            )
            conn.commit()
            conn.close()
            logger.info(f"Name gesetzt: {guid} → '{name_str}'")
            return True
        else:
            conn.close()
            logger.warning(f"set_name fehlgeschlagen: GUID {guid} nicht gefunden")
            return False
