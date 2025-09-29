#!/usr/bin/env python3
"""
MIGRATION TOOL: ALTE field_* STRUKTUR → NEUE SAUBERE SPALTENNAME-STRUKTUR
===========================================================================

Migriert alle alten field_* Einträge zur neuen sauberen Struktur wo:
- Spaltenname wird direkt als Key verwendet (ohne field_ prefix)
- Jeder Key enthält: {"simple_search": "wert", "conditions": [...]}
- Einheitlicher Zugriff über get_value(view_guid, spaltenname)
"""

import logging
import sqlite3
import json
from typing import Dict, Any, List, Tuple

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructureMigrator:
    """Migriert von alter field_* Struktur zur neuen sauberen Struktur"""
    
    def __init__(self, db_path: str = "PdvmManager.db"):
        self.db_path = db_path
        self.migration_stats = {
            'total_examined': 0,
            'field_entries_found': 0,
            'migrated_simple': 0,
            'migrated_complex': 0,
            'errors': 0
        }
    
    def run_migration(self):
        """Führe komplette Migration durch"""
        try:
            logger.info("🚀 Starte Migration zur sauberen Spaltenname-Struktur")
            
            # 1. Analysiere aktuelle Struktur
            field_entries = self.analyze_current_structure()
            
            # 2. Migriere zu neuer Struktur
            self.migrate_entries(field_entries)
            
            # 3. Bereinige alte Einträge
            self.cleanup_old_entries(field_entries)
            
            # 4. Statistiken ausgeben
            self.print_migration_stats()
            
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler bei Migration: {e}")
            raise
    
    def analyze_current_structure(self) -> Dict[str, List[Tuple]]:
        """Analysiere aktuelle Datenbankstruktur"""
        logger.info("🔍 Analysiere aktuelle Datenbankstruktur...")
        
        field_entries = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Alle anwendungsdaten durchsuchen - richtige Spaltenstruktur verwenden
                cursor.execute("SELECT uid, name, daten FROM anwendungsdaten")
                
                for row in cursor.fetchall():
                    uid, name, daten = row
                    self.migration_stats['total_examined'] += 1
                    
                    # Parse daten JSON um field_* keys zu finden
                    try:
                        data_dict = json.loads(daten) if daten else {}
                        if isinstance(data_dict, dict):
                            for feld, werte in data_dict.items():
                                if feld.startswith('field_'):
                                    self.migration_stats['field_entries_found'] += 1
                                    
                                    # Extrahiere echten Spaltenname
                                    column_name = feld.replace('field_', '')
                                    
                                    # Gruppiere nach UID (entspricht view_guid)
                                    if uid not in field_entries:
                                        field_entries[uid] = []
                                    
                                    field_entries[uid].append({
                                        'old_field': feld,
                                        'column_name': column_name,
                                        'data': werte,
                                        'name': name
                                    })
                                    
                                    logger.debug(f"📋 Gefunden: {uid} -> {feld} -> {column_name}")
                    except:
                        # Wenn JSON parsing fehlschlägt, überspringe
                        continue
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Strukturanalyse: {e}")
            raise
        
        logger.info(f"✅ {self.migration_stats['field_entries_found']} field_* Einträge in {len(field_entries)} UIDs gefunden")
        return field_entries
    
    def migrate_entries(self, field_entries: Dict[str, List]):
        """Migriere Einträge zur neuen Struktur"""
        logger.info("🔄 Starte Migration zur neuen Struktur...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for uid, entries in field_entries.items():
                    logger.info(f"📂 Migriere UID: {uid}")
                    
                    # Aktuelle daten laden
                    cursor.execute("SELECT daten FROM anwendungsdaten WHERE uid=?", (uid,))
                    result = cursor.fetchone()
                    
                    if result:
                        current_data = json.loads(result[0]) if result[0] else {}
                    else:
                        current_data = {}
                    
                    # Für jeden field_* Eintrag
                    for entry in entries:
                        column_name = entry['column_name']
                        data = entry['data']
                        old_field = entry['old_field']
                        
                        # Neue Struktur erstellen
                        new_data = {}
                        
                        if isinstance(data, dict):
                            # Komplexe Struktur mit conditions
                            if 'conditions' in data:
                                new_data['conditions'] = data['conditions']
                                self.migration_stats['migrated_complex'] += 1
                                logger.info(f"  🔧 Komplex migriert: {column_name} -> {len(data['conditions'])} Bedingungen")
                            
                            # Einfacher Wert
                            if 'value' in data:
                                new_data['simple_search'] = data['value']
                            else:
                                new_data['simple_search'] = str(data) if data else ''
                        
                        elif isinstance(data, str):
                            # Einfacher String-Wert
                            new_data['simple_search'] = data
                            new_data['conditions'] = []
                            self.migration_stats['migrated_simple'] += 1
                            logger.info(f"  📝 Einfach migriert: {column_name} -> '{data}'")
                        
                        else:
                            # Unbekanntes Format - leere Struktur
                            new_data['simple_search'] = str(data) if data else ''
                            new_data['conditions'] = []
                            logger.warning(f"  ⚠️ Unbekanntes Format für {column_name}: {type(data)}")
                        
                        # Neue Struktur in current_data einsetzen
                        current_data[column_name] = new_data
                        
                        # Alte field_* Struktur entfernen
                        if old_field in current_data:
                            del current_data[old_field]
                            logger.debug(f"    🗑️ Entfernt: {old_field}")
                    
                    # Aktualisierte daten zurückschreiben
                    cursor.execute(
                        "UPDATE anwendungsdaten SET daten=? WHERE uid=?",
                        (json.dumps(current_data), uid)
                    )
                    logger.debug(f"    ✅ Updated UID: {uid}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Migration: {e}")
            self.migration_stats['errors'] += 1
            raise
    
    def cleanup_old_entries(self, field_entries: Dict[str, List]):
        """Bereinigung erfolgt bereits während der Migration (in-place)"""
        logger.info("🧹 Bereinigung bereits während Migration durchgeführt")
        
        # Statistik für gelöschte Einträge
        deleted_count = sum(len(entries) for entries in field_entries.values())
        logger.info(f"✅ {deleted_count} alte field_* Einträge während Migration bereinigt")
    
    def print_migration_stats(self):
        """Ausgabe Migrations-Statistiken"""
        logger.info("📊 MIGRATIONS-STATISTIKEN:")
        logger.info(f"   Geprüfte Einträge: {self.migration_stats['total_examined']}")
        logger.info(f"   Field_* gefunden:  {self.migration_stats['field_entries_found']}")
        logger.info(f"   Einfach migriert:  {self.migration_stats['migrated_simple']}")
        logger.info(f"   Komplex migriert:  {self.migration_stats['migrated_complex']}")
        logger.info(f"   Fehler:            {self.migration_stats['errors']}")
        
        if self.migration_stats['errors'] == 0:
            logger.info("🎉 Migration erfolgreich abgeschlossen!")
        else:
            logger.warning(f"⚠️ Migration mit {self.migration_stats['errors']} Fehlern abgeschlossen")


def main():
    """Hauptfunktion"""
    print("🔧 STRUKTUR-MIGRATION: field_* → Saubere Spaltenname-Struktur")
    print("=" * 70)
    
    migrator = StructureMigrator()
    
    try:
        migrator.run_migration()
        
        print("\n✅ Migration erfolgreich!")
        print("Neue Struktur:")
        print("  - Spaltenname als direkter Key")
        print("  - Format: {\"simple_search\": \"wert\", \"conditions\": [...]}")
        print("  - Einheitlicher Zugriff: get_value(view_guid, spaltenname)")
        
    except Exception as e:
        print(f"\n❌ Migration fehlgeschlagen: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())