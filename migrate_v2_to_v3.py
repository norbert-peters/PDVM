"""
Migration V2 → V3 Menu System
==============================
Migriert bestehende V2-Menüs ins neue lineare V3-Format

V2: MenuContainer mit separaten MenuItem/MenuCommand Objekten
V3: PdvmCentralDatenbank mit integriertem Command

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import logging
import sqlite3
import json
from typing import Dict, List, Any

from v3_menu_system import MenuItem, ItemType, create_menu_item
from pdvm_central_datenbank import PdvmCentralDatenbank

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


class V2ToV3Migrator:
    """Migriert V2-Menüs ins V3-Format"""
    
    def __init__(self, db_path: str):
        """
        Args:
            db_path: Pfad zur Mandanten-Datenbank
        """
        self.db_path = db_path
        self.conn = None
        
        logger.info(f"🔧 Migrator initialisiert für: {db_path}")
    
    def migrate_all_menus(self):
        """Migriert alle Menüs in der Datenbank"""
        logger.info("=" * 80)
        logger.info("🚀 MIGRATION V2 → V3 GESTARTET")
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
        
        # V3-Datenbank erstellen
        v3_db = PdvmCentralDatenbank('menudaten', uid)
        
        # Meta-Daten setzen
        v3_db.set_value('META', 'name', name)
        v3_db.set_value('META', 'version', 'V3')
        v3_db.set_value('META', 'migrated_from', 'V2')
        
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
        for gruppe in ['VERTIKAL', 'GRUND', 'ZUSATZ']:
            v2_items = v2_data.get(gruppe, [])
            logger.info(f"   📂 {gruppe}: {len(v2_items)} Items")
            
            for v2_item in v2_items:
                # V2-Item zu V3-Item konvertieren
                v3_item = self._convert_item(v2_item, commands_map)
                
                # In V3-DB speichern
                v3_db.set_value(gruppe, v3_item.guid, v3_item.to_json())
        
        # Alle Werte speichern
        v3_db.save_all_values()
        
        # Statistik
        vertikal_count = len(v2_data.get('VERTIKAL', []))
        grund_count = len(v2_data.get('GRUND', []))
        zusatz_count = len(v2_data.get('ZUSATZ', []))
        
        logger.info(f"\n   ✅ Migriert:")
        logger.info(f"      VERTIKAL: {vertikal_count}")
        logger.info(f"      GRUND: {grund_count}")
        logger.info(f"      ZUSATZ: {zusatz_count}")
    
    def _convert_item(
        self, 
        v2_item: Dict[str, Any], 
        commands_map: Dict[str, Dict[str, Any]]
    ) -> MenuItem:
        """
        Konvertiert V2-Item zu V3-Item
        
        Args:
            v2_item: V2-Item-Daten
            commands_map: Mapping COMMAND_GUID → Command-Daten
            
        Returns:
            V3-MenuItem mit integriertem Command
        """
        guid = v2_item.get('GUID')
        item_type = v2_item.get('TYPE')
        label = v2_item.get('LABEL', '')
        sort_order = v2_item.get('SORT_ORDER', 0)
        parent_guid = v2_item.get('PARENT_GUID')
        template_guid = v2_item.get('TEMPLATE_GUID')
        icon = v2_item.get('ICON')
        visible = v2_item.get('VISIBLE', True)
        enabled = v2_item.get('ENABLED', True)
        tooltip = v2_item.get('TOOLTIP')
        
        # Command integrieren (wenn vorhanden)
        command = None
        command_guid = v2_item.get('COMMAND_GUID')
        if command_guid and command_guid in commands_map:
            command = commands_map[command_guid]
        
        # MenuItem erstellen
        return MenuItem(
            guid=guid,
            type=item_type,
            label=label,
            sort_order=sort_order,
            parent_guid=parent_guid,
            template_guid=template_guid,
            icon=icon,
            visible=visible,
            enabled=enabled,
            tooltip=tooltip,
            command=command
        )


def migrate_mandant(mandant_num: int):
    """
    Migriert alle Menüs eines Mandanten
    
    Args:
        mandant_num: Mandanten-Nummer (1 oder 2)
    """
    db_path = f"C:\\Users\\norbe\\OneDrive\\Dokumente\\MyApplication\\Daten\\mandant_00{mandant_num}\\datenbank.db"
    
    migrator = V2ToV3Migrator(db_path)
    migrator.migrate_all_menus()


if __name__ == "__main__":
    print("=" * 80)
    print("🔄 MENU MIGRATION V2 → V3")
    print("=" * 80)
    print("\nMigriert alle Menüs von V2 (MenuContainer) zu V3 (PdvmCentralDatenbank)")
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
