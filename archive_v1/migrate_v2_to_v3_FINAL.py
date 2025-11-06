"""
Migration V2 → V3 Menu System (FINAL KORREKT)
===============================================
Migriert V2-JSON zu V3-JSON INNERHALB der bestehenden sys_menudaten Tabelle

WICHTIG: 
- Nutzt bestehende Tabelle: sys_menudaten
- Ändert nur die Spalte: daten (V2-JSON → V3-JSON)
- Erstellt KEINE neuen Tabellen!

V2-Format (daten Spalte):
{
    "VERTIKAL": [...items...],
    "GRUND": [...items...],
    "ZUSATZ": [...items...],
    "COMMANDS": [...commands...]
}

V3-Format (daten Spalte):
{
    "META": {
        "version": "V3",
        "migrated_from": "V2"
    },
    "VERTIKAL": [...items mit integriertem command...],
    "GRUND": [...items mit integriertem command...],
    "ZUSATZ": [...items mit integriertem command...]
}

Autor: PDVM V3.0 FINAL
Datum: 02.11.2025
"""

import logging
import sqlite3
import json
import os
from typing import Dict, List, Any

from v3_menu_system import MenuItem, ItemType, create_menu_item

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class V2ToV3MigratorFinal:
    """Migriert V2-JSON zu V3-JSON in bestehender sys_menudaten Tabelle"""
    
    def __init__(self, db_path: str):
        """
        Args:
            db_path: VOLLSTÄNDIGER Pfad zur Mandanten-Datenbank
        """
        self.db_path = os.path.abspath(db_path)
        self.conn = None
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"❌ Datenbank nicht gefunden: {self.db_path}")
        
        logger.info(f"🔧 Migrator initialisiert für: {self.db_path}")
    
    def migrate_all_menus(self):
        """Migriert alle Menüs in der sys_menudaten Tabelle"""
        logger.info("=" * 80)
        logger.info("🚀 MIGRATION V2 → V3 GESTARTET (FINAL - sys_menudaten)")
        logger.info("=" * 80)
        
        # Datenbank öffnen
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Alle Menüs holen
        cursor.execute("""
            SELECT uid, name, daten
            FROM sys_menudaten
            WHERE historisch = 0
        """)
        
        menus = cursor.fetchall()
        logger.info(f"\n📂 Gefunden: {len(menus)} Menüs in sys_menudaten")
        
        success_count = 0
        error_count = 0
        
        for uid, name, daten_json in menus:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"📋 Migriere: {name} ({uid})")
                logger.info(f"{'='*80}")
                
                # V2 → V3 konvertieren
                v3_json = self._convert_v2_to_v3(daten_json, name)
                
                # Zurück in sys_menudaten schreiben
                cursor.execute("""
                    UPDATE sys_menudaten
                    SET daten = ?
                    WHERE uid = ? AND historisch = 0
                """, (v3_json, uid))
                
                self.conn.commit()
                
                success_count += 1
                logger.info(f"✅ Migration erfolgreich: {name}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Fehler bei {name}: {e}")
                import traceback
                traceback.print_exc()
        
        self.conn.close()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 MIGRATION ABGESCHLOSSEN")
        logger.info(f"   Erfolgreich: {success_count}")
        logger.info(f"   Fehler: {error_count}")
        logger.info("=" * 80)
    
    def _convert_v2_to_v3(self, v2_json_string: str, menu_name: str) -> str:
        """
        Konvertiert V2-JSON zu V3-JSON
        
        Args:
            v2_json_string: V2-Format JSON-String
            menu_name: Name des Menüs
            
        Returns:
            V3-Format JSON-String
        """
        # V2-Daten parsen
        v2_data = json.loads(v2_json_string)
        
        # Commands-Mapping erstellen (GUID → Command-Daten)
        commands_map = {}
        for cmd in v2_data.get('COMMANDS', []):
            cmd_guid = cmd.get('GUID')
            if cmd_guid:
                commands_map[cmd_guid] = {
                    'handler': cmd.get('HANDLER'),
                    'params': cmd.get('PARAMS', {})
                }
        
        logger.info(f"   📦 Commands: {len(commands_map)}")
        
        # V3-Struktur erstellen
        v3_data = {
            'META': {
                'version': 'V3',
                'migrated_from': 'V2'
            }
        }
        
        # Für jede Gruppe Items konvertieren
        item_counts = {}
        for gruppe in ['VERTIKAL', 'GRUND', 'ZUSATZ']:
            v2_items = v2_data.get(gruppe, [])
            item_counts[gruppe] = len(v2_items)
            logger.info(f"   📂 {gruppe}: {len(v2_items)} Items")
            
            # Items mit integriertem Command
            v3_items = []
            for v2_item in v2_items:
                v3_item = self._convert_item(v2_item, commands_map)
                v3_items.append(json.loads(v3_item.to_json()))
            
            v3_data[gruppe] = v3_items
        
        # Statistik
        logger.info(f"\n   ✅ Konvertiert:")
        logger.info(f"      VERTIKAL: {item_counts.get('VERTIKAL', 0)}")
        logger.info(f"      GRUND: {item_counts.get('GRUND', 0)}")
        logger.info(f"      ZUSATZ: {item_counts.get('ZUSATZ', 0)}")
        
        # Als JSON-String zurückgeben
        return json.dumps(v3_data, ensure_ascii=False)
    
    def _convert_item(
        self, 
        v2_item: Dict[str, Any], 
        commands_map: Dict[str, Dict[str, Any]]
    ) -> MenuItem:
        """
        Konvertiert V2-Item zu V3-MenuItem
        
        V2: Item + separates Command über COMMAND_GUID
        V3: Item mit integriertem command-Dict
        """
        # Command integrieren falls vorhanden
        command_guid = v2_item.get('COMMAND_GUID')
        command = commands_map.get(command_guid) if command_guid else None
        
        # V3-MenuItem erstellen
        return create_menu_item(
            guid=v2_item.get('GUID'),
            item_type=v2_item.get('TYPE', 'BUTTON'),
            label=v2_item.get('LABEL', ''),
            sort_order=v2_item.get('SORT_ORDER', 0),
            parent_guid=v2_item.get('PARENT_GUID'),
            template_guid=v2_item.get('TEMPLATE_GUID'),
            icon=v2_item.get('ICON'),
            visible=v2_item.get('VISIBLE', True),
            enabled=v2_item.get('ENABLED', True),
            tooltip=v2_item.get('TOOLTIP'),
            command=command
        )


def migrate_mandant(mandant_num: int):
    """
    Migriert alle Menüs eines Mandanten
    
    Args:
        mandant_num: Mandanten-Nummer (1 oder 2)
    """
    db_path = f"Daten/mandant_00{mandant_num}/datenbank.db"
    
    migrator = V2ToV3MigratorFinal(db_path)
    migrator.migrate_all_menus()


if __name__ == "__main__":
    print("=" * 80)
    print("🔄 MENU MIGRATION V2 → V3 (FINAL KORREKT)")
    print("=" * 80)
    print("\nMigriert V2-JSON zu V3-JSON in bestehender sys_menudaten Tabelle!")
    print("\nÄnderungen:")
    print("  ✅ Nutzt bestehende Tabelle: sys_menudaten")
    print("  ✅ Ändert nur Spalte: daten")
    print("  ✅ Erstellt KEINE neuen Tabellen")
    print("  ✅ Commands direkt im Item integriert")
    print("\n" + "=" * 80)
    
    # Mandant 1 migrieren
    print("\n🎯 Migriere Mandant 1...")
    migrate_mandant(1)
    
    print("\n\n🎯 Migriere Mandant 2...")
    migrate_mandant(2)
    
    print("\n" + "=" * 80)
    print("✅ MIGRATION ABGESCHLOSSEN")
    print("=" * 80)
