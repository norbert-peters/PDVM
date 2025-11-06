"""
V2.0 Mandanten-Datenbank Initialisierung

Liest Mandanten aus auth.db und erstellt fehlende Mandanten-Datenbanken
mit allen sys_* Tabellen.

VERWENDUNG:
- Automatisch beim ersten Start
- Manuell beim Anlegen neuer Mandanten

AUTOR: Norbert Peters
DATUM: 30.10.2025
VERSION: 1.0
"""

import os
import sqlite3
import json
from pathlib import Path


class MandantenDatabaseInit:
    """Initialisiert Mandanten-Datenbanken"""
    
    def __init__(self, auth_db_path: str, mandanten_base_path: str):
        """
        Args:
            auth_db_path: Pfad zu auth.db (enthält sys_mandanten)
            mandanten_base_path: Basis-Pfad für Mandanten (z.B. 'Daten')
        """
        self.auth_db_path = auth_db_path
        self.mandanten_base_path = Path(mandanten_base_path)
        
    def get_all_mandanten(self):
        """
        Liest alle Mandanten aus auth.db
        
        Returns:
            List[dict]: Liste mit {'uid': str, 'bezeichnung': str}
        """
        mandanten = []
        
        try:
            conn = sqlite3.connect(self.auth_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT uid, daten FROM sys_mandanten")
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                daten = json.loads(row['daten'])
                mandanten.append({
                    'uid': row['uid'],
                    'bezeichnung': daten['ROOT']['BEZEICHNUNG']  # Korrigiert!
                })
            
            return mandanten
            
        except Exception as e:
            print(f"❌ Fehler beim Lesen der Mandanten: {e}")
            return []
    
    def mandant_db_exists(self, mandant_uid: str) -> bool:
        """
        Prüft ob Mandanten-DB existiert
        
        Args:
            mandant_uid: Mandanten-UID (z.B. 'mandant_001')
        
        Returns:
            True wenn DB existiert
        """
        db_path = self.mandanten_base_path / mandant_uid / "datenbank.db"
        return db_path.exists()
    
    def create_mandant_database(self, mandant_uid: str, bezeichnung: str):
        """
        Erstellt neue Mandanten-Datenbank mit allen sys_* Tabellen
        
        Args:
            mandant_uid: Mandanten-UID (z.B. 'mandant_001')
            bezeichnung: Mandanten-Bezeichnung (z.B. 'Hauptverwaltung')
        """
        # Verzeichnis erstellen
        mandant_dir = self.mandanten_base_path / mandant_uid
        mandant_dir.mkdir(parents=True, exist_ok=True)
        
        db_path = mandant_dir / "datenbank.db"
        
        print(f"📂 Erstelle DB: {db_path}")
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # sys_anwendungsdaten: Anwendungsdaten (Filter, Sortierungen, Spalten-Einstellungen)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_anwendungsdaten (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_beschreibungen: Beschreibungstexte für Felder/Controls
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_beschreibungen (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_dialogdaten: Dialog-Konfigurationen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_dialogdaten (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_dropdowndaten: Dropdown-Listen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_dropdowndaten (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_framedaten: Frame-Layouts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_framedaten (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_menudaten: Menü-Strukturen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_menudaten (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_systemsteuerung: Systemkonfiguration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_systemsteuerung (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            # sys_viewdaten: View-Definitionen
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sys_viewdaten (
                    uid TEXT PRIMARY KEY,
                    daten TEXT NOT NULL,
                    name TEXT,
                    historisch INTEGER DEFAULT 0,
                    source_hash TEXT,
                    sec_id TEXT,
                    gilt_bis TEXT DEFAULT '9999365.00000',
                    created_at TEXT,
                    modified_at TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ 8 Tabellen erstellt")
            
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
            if conn:
                conn.close()
    
    def initialize_all_mandanten(self):
        """
        Hauptfunktion: Prüft alle Mandanten und erstellt fehlende DBs
        """
        print("\n" + "="*70)
        print("🚀 MANDANTEN-DATENBANK INITIALISIERUNG")
        print("="*70)
        
        # Mandanten aus auth.db lesen
        mandanten = self.get_all_mandanten()
        
        if not mandanten:
            print("❌ Keine Mandanten in auth.db gefunden!")
            return
        
        print(f"\n📋 Gefundene Mandanten: {len(mandanten)}")
        for m in mandanten:
            print(f"   - {m['uid']}: {m['bezeichnung']}")
        
        # Fehlende DBs erstellen
        print(f"\n🔍 Prüfe Mandanten-Datenbanken...")
        
        created = 0
        skipped = 0
        
        for mandant in mandanten:
            uid = mandant['uid']
            bezeichnung = mandant['bezeichnung']
            
            if self.mandant_db_exists(uid):
                print(f"\n⏭️  {uid} ({bezeichnung})")
                print(f"   Datenbank existiert bereits")
                skipped += 1
            else:
                print(f"\n📦 {uid} ({bezeichnung})")
                self.create_mandant_database(uid, bezeichnung)
                created += 1
        
        # Zusammenfassung
        print("\n" + "="*70)
        print("✅ INITIALISIERUNG ABGESCHLOSSEN")
        print("="*70)
        print(f"   Erstellt: {created}")
        print(f"   Übersprungen: {skipped}")
        print(f"   Gesamt: {len(mandanten)}")
        print("")


def main():
    """Hauptfunktion"""
    # Pfade
    auth_db = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\auth.db"
    mandanten_base = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten"
    
    # Initialisierung
    init = MandantenDatabaseInit(auth_db, mandanten_base)
    init.initialize_all_mandanten()


if __name__ == "__main__":
    main()
