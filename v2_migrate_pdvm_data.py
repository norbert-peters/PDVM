"""
V2.0 Daten-Migration von PdvmManager.db zu Mandanten-DBs

Kopiert Daten aus den sys_* Tabellen der PdvmManager.db
1:1 in alle Mandanten-Datenbanken.

VERWENDUNG:
- Nach v2_init_mandanten_databases.py ausführen
- Kopiert nur Daten, keine Struktur-Änderungen

AUTOR: Norbert Peters
DATUM: 30.10.2025
VERSION: 1.0
"""

import os
import sqlite3
import json
from pathlib import Path


class PdvmDataMigration:
    """Migriert Daten von PdvmManager.db zu Mandanten-DBs"""
    
    # Tabellen die migriert werden sollen
    # Mapping: alt (ohne sys_) → neu (mit sys_)
    TABLES = {
        'anwendungsdaten': 'sys_anwendungsdaten',
        'beschreibungen': 'sys_beschreibungen',
        'dialogdaten': 'sys_dialogdaten',
        'dropdowndaten': 'sys_dropdowndaten',
        'framedaten': 'sys_framedaten',
        'menudaten': 'sys_menudaten',
        'systemsteuerung': 'sys_systemsteuerung',
        'viewdaten': 'sys_viewdaten'
    }
    
    def __init__(self, source_db_path: str, auth_db_path: str, mandanten_base_path: str):
        """
        Args:
            source_db_path: Pfad zu PdvmManager.db (Quell-DB)
            auth_db_path: Pfad zu auth.db (für Mandanten-Liste)
            mandanten_base_path: Basis-Pfad für Mandanten (z.B. 'Daten')
        """
        self.source_db_path = source_db_path
        self.auth_db_path = auth_db_path
        self.mandanten_base_path = Path(mandanten_base_path)
        
    def get_all_mandanten(self):
        """Liest alle Mandanten aus auth.db"""
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
    
    def table_exists_in_source(self, table_name: str) -> bool:
        """Prüft ob Tabelle in PdvmManager.db existiert"""
        try:
            conn = sqlite3.connect(self.source_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            exists = cursor.fetchone() is not None
            conn.close()
            
            return exists
            
        except Exception as e:
            print(f"❌ Fehler bei Prüfung von {table_name}: {e}")
            return False
    
    def get_table_data(self, source_table_name: str):
        """
        Liest alle Daten aus einer Tabelle in alter DB (ohne sys_ Präfix)
        
        Args:
            source_table_name: Name der Quell-Tabelle (ohne sys_)
        
        Returns:
            List[dict]: Liste mit {'uid', 'daten', 'name', 'historisch', 'last_modified', 'stichtag'}
        """
        try:
            conn = sqlite3.connect(self.source_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT uid, daten, name, historisch, source_hash, last_modified, stichtag FROM {source_table_name}")
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'uid': row['uid'],
                    'daten': row['daten'],
                    'name': row['name'],
                    'historisch': row['historisch'] if row['historisch'] else 0,
                    'source_hash': row['source_hash'],
                    'sec_id': None,  # Neu: wird auf NULL gesetzt (später manuell befüllen)
                    'gilt_bis': row['stichtag'] if row['stichtag'] else '9999365.00000',  # Mapping: stichtag → gilt_bis
                    'created_at': row['last_modified'],  # Als Erstellungszeitpunkt übernehmen
                    'modified_at': row['last_modified']  # Mapping: last_modified → modified_at
                })
            
            return data
            
        except Exception as e:
            print(f"   ❌ Fehler beim Lesen: {e}")
            return []
    
    def insert_table_data(self, mandant_uid: str, target_table_name: str, data: list):
        """
        Schreibt Daten in Mandanten-DB (überschreibt existierende Daten)
        
        Args:
            mandant_uid: Mandanten-UID (z.B. 'mandant_001')
            target_table_name: Ziel-Tabellen-Name (mit sys_)
            data: Liste mit Datensätzen
        """
        db_path = self.mandanten_base_path / mandant_uid / "datenbank.db"
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Alte Daten löschen (komplette Tabelle leeren)
            cursor.execute(f"DELETE FROM {target_table_name}")
            
            # Neue Daten einfügen
            for record in data:
                cursor.execute(f"""
                    INSERT INTO {target_table_name} 
                    (uid, daten, name, historisch, source_hash, sec_id, gilt_bis, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['uid'],
                    record['daten'],
                    record['name'],
                    record['historisch'],
                    record['source_hash'],
                    record['sec_id'],
                    record['gilt_bis'],
                    record['created_at'],
                    record['modified_at']
                ))
            
            conn.commit()
            conn.close()
            
            print(f"      ✅ {len(data)} Datensätze eingefügt")
            
        except Exception as e:
            print(f"      ❌ Fehler beim Schreiben: {e}")
            if conn:
                conn.close()
    
    def migrate_table_to_all_mandanten(self, source_table: str, target_table: str):
        """
        Migriert eine Tabelle zu allen Mandanten
        
        Args:
            source_table: Name der Quell-Tabelle (ohne sys_)
            target_table: Name der Ziel-Tabelle (mit sys_)
        """
        print(f"\n📋 {source_table} → {target_table}")
        
        # Prüfen ob Tabelle in Source existiert
        if not self.table_exists_in_source(source_table):
            print(f"   ⚠️  Tabelle '{source_table}' existiert nicht in alter DB - überspringe")
            return
        
        # Daten aus Source lesen
        print(f"   📖 Lese Daten aus alter DB...")
        data = self.get_table_data(source_table)
        
        if not data:
            print(f"   ⚠️  Keine Daten gefunden - überspringe")
            return
        
        print(f"   ✅ {len(data)} Datensätze gelesen")
        
        # In alle Mandanten schreiben
        mandanten = self.get_all_mandanten()
        
        for mandant in mandanten:
            uid = mandant['uid']
            print(f"   → {uid}")
            self.insert_table_data(uid, target_table, data)
    
    def migrate_all_tables(self):
        """Hauptfunktion: Migriert alle sys_* Tabellen"""
        print("\n" + "="*70)
        print("🚀 DATEN-MIGRATION: PdvmManager.db → Mandanten-DBs")
        print("="*70)
        
        print(f"\n📂 Source: {self.source_db_path}")
        print(f"📂 Target: {self.mandanten_base_path}")
        
        # Mandanten prüfen
        mandanten = self.get_all_mandanten()
        
        if not mandanten:
            print("\n❌ Keine Mandanten in auth.db gefunden!")
            return
        
        print(f"\n📋 Ziel-Mandanten: {len(mandanten)}")
        for m in mandanten:
            print(f"   - {m['uid']}: {m['bezeichnung']}")
        
        # Tabellen migrieren
        print(f"\n🔄 Migriere {len(self.TABLES)} Tabellen...")
        
        for source_table, target_table in self.TABLES.items():
            self.migrate_table_to_all_mandanten(source_table, target_table)
        
        # Zusammenfassung
        print("\n" + "="*70)
        print("✅ MIGRATION ABGESCHLOSSEN")
        print("="*70)
        print(f"   Tabellen: {len(self.TABLES)}")
        print(f"   Mandanten: {len(mandanten)}")
        print("")


def main():
    """Hauptfunktion"""
    # Pfade
    source_db = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\PdvmManager.db"  # PdvmManager.db im Hauptverzeichnis
    auth_db = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\auth.db"
    mandanten_base = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten"
    
    # Prüfen ob Source existiert
    if not os.path.exists(source_db):
        print(f"❌ PdvmManager.db nicht gefunden: {source_db}")
        return
    
    # Migration starten
    migration = PdvmDataMigration(source_db, auth_db, mandanten_base)
    migration.migrate_all_tables()


if __name__ == "__main__":
    main()
