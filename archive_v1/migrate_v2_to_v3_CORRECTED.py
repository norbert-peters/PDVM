"""
Migration V2 → V3 Menu System (KORRIGIERT)
==========================================
Migriert bestehende V2-Menüs ins neue lineare V3-Format

WICHTIG: Migriert in die RICHTIGEN Mandanten-Datenbanken!
         Umgeht PdvmInit.json und setzt DB-Pfad direkt

V2: MenuContainer mit separaten MenuItem/MenuCommand Objekten
V3: PdvmCentralDatenbank mit integriertem Command

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import logging
import sqlite3
import json
import os
from typing import Dict, List, Any, Optional

from v3_menu_system import MenuItem, ItemType, create_menu_item

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class V2ToV3MigratorCorrected:
    """Migriert V2-Menüs ins V3-Format (KORRIGIERT für richtige Mandanten-DB)"""
    
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
        """Migriert alle Menüs in der Datenbank"""
        logger.info("=" * 80)
        logger.info("🚀 MIGRATION V2 → V3 GESTARTET (KORRIGIERT)")
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
        logger.info(f"\n📂 Gefunden: {len(menus)} Menüs")
        
        success_count = 0
        error_count = 0
        
        for uid, name, daten_json in menus:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"📋 Migriere: {name} ({uid})")
                logger.info(f"{'='*80}")
                
                self._migrate_menu(uid, name, daten_json)
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
    
    def _migrate_menu(self, uid: str, name: str, daten_json: str):
        """
        Migriert ein einzelnes Menü
        
        Args:
            uid: Menü-GUID
            name: Menü-Name
            daten_json: V2-Daten als JSON-String
        """
        # V2-Daten parsen
        v2_data = json.loads(daten_json)
        
        # Tabelle direkt in der aktuellen Datenbank erstellen
        table_name = f"menudaten.{uid}"
        self._create_v3_table(table_name)
        
        # Meta-Daten speichern
        self._save_value(table_name, 'META', 'name', name)
        self._save_value(table_name, 'META', 'version', 'V3')
        self._save_value(table_name, 'META', 'migrated_from', 'V2')
        
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
        
        # Für jede Gruppe migrieren
        item_counts = {}
        for gruppe in ['VERTIKAL', 'GRUND', 'ZUSATZ']:
            v2_items = v2_data.get(gruppe, [])
            item_counts[gruppe] = len(v2_items)
            logger.info(f"   📂 {gruppe}: {len(v2_items)} Items")
            
            for v2_item in v2_items:
                # V2-Item zu V3-Item konvertieren
                v3_item = self._convert_item(v2_item, commands_map)
                
                # In V3-DB speichern
                self._save_value(table_name, gruppe, v3_item.guid, v3_item.to_json())
        
        # Statistik
        logger.info(f"\n   ✅ Migriert:")
        logger.info(f"      VERTIKAL: {item_counts.get('VERTIKAL', 0)}")
        logger.info(f"      GRUND: {item_counts.get('GRUND', 0)}")
        logger.info(f"      ZUSATZ: {item_counts.get('ZUSATZ', 0)}")
    
    def _create_v3_table(self, table_name: str):
        """
        Erstellt eine V3-Tabelle für Menüdaten
        
        Struktur: gruppe (VERTIKAL/GRUND/ZUSATZ/META), feld (GUID), wert (JSON)
        """
        cursor = self.conn.cursor()
        
        # Tabelle erstellen (quoted für GUID-Punkte)
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                gruppe TEXT NOT NULL,
                feld TEXT NOT NULL,
                wert TEXT,
                PRIMARY KEY (gruppe, feld)
            )
        ''')
        
        self.conn.commit()
        logger.debug(f"   📦 Tabelle erstellt: {table_name}")
    
    def _save_value(self, table_name: str, gruppe: str, feld: str, wert: str):
        """Speichert einen Wert in die V3-Tabelle"""
        cursor = self.conn.cursor()
        
        cursor.execute(f'''
            INSERT OR REPLACE INTO "{table_name}" (gruppe, feld, wert)
            VALUES (?, ?, ?)
        ''', (gruppe, feld, wert))
        
        self.conn.commit()
    
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
    
    migrator = V2ToV3MigratorCorrected(db_path)
    migrator.migrate_all_menus()


if __name__ == "__main__":
    print("=" * 80)
    print("🔄 MENU MIGRATION V2 → V3 (KORRIGIERT)")
    print("=" * 80)
    print("\nMigriert alle Menüs in die RICHTIGEN Mandanten-Datenbanken!")
    print("\nVorteile V3:")
    print("  - Linear & PDVM-konform")
    print("  - Command direkt im Item integriert")
    print("  - Einfache Template-Integration")
    print("  - Einheitliche Datenstruktur")
    print("\n" + "=" * 80)
    
    # Mandant 1 migrieren
    print("\n🎯 Migriere Mandant 1...")
    migrate_mandant(1)
    
    print("\n\n🎯 Migriere Mandant 2...")
    migrate_mandant(2)
    
    print("\n" + "=" * 80)
    print("✅ MIGRATION ABGESCHLOSSEN")
    print("=" * 80)
