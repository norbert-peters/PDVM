"""
V2 Menu Storage Manager
=======================
Zugriff auf Menü-Daten in sys_menudaten (man_db)

Speicherstruktur:
- Tabelle: sys_menudaten
- UID: menu_guid
- Daten: JSON mit MenuContainer

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from v2_menu_schema import MenuContainer, MenuItem, MenuCommand, MenuItemType
from v2_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class V2MenuStorage:
    """
    Storage Manager für Menü-Daten
    
    Zugriff auf Mandanten-Datenbank (sys_menudaten Tabelle)
    Speichert MenuContainer als JSON
    """
    
    def __init__(self):
        """Initialisiert Storage mit direktem Zugriff auf Mandanten-DB"""
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("GCS nicht initialisiert - Menu Storage benötigt GCS")
        
        # Direkt auf Mandanten-Datenbank zugreifen (nicht man_db!)
        import sqlite3
        self.db_path = self.gcs.db_path
        logger.info(f"✅ V2MenuStorage initialisiert mit Mandanten-DB: {self.db_path}")
    
    def get_menu(self, menu_guid: str) -> Optional[MenuContainer]:
        """
        Lädt komplettes Menü aus Mandanten-DB (sys_menudaten)
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            MenuContainer oder None wenn nicht gefunden
        """
        import sqlite3
        try:
            # Direkter SQL-Zugriff auf sys_menudaten
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT daten FROM sys_menudaten WHERE uid = ?",
                (menu_guid,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if not row or not row[0]:
                logger.warning(f"⚠️ Menü {menu_guid} nicht gefunden in {self.db_path}")
                return None
            
            # Parse JSON und erstelle MenuContainer
            menu_dict = json.loads(row[0])
            container = MenuContainer.from_dict(menu_dict)
            
            logger.info(f"✅ Menü geladen: {container.MENU_NAME} ({menu_guid})")
            logger.info(f"   VERTIKAL: {len(container.VERTIKAL)} Items")
            logger.info(f"   GRUND: {len(container.GRUND)} Items")
            logger.info(f"   ZUSATZ: {len(container.ZUSATZ)} Items")
            logger.info(f"   COMMANDS: {len(container.COMMANDS)} Items")
            
            return container
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von Menü {menu_guid}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_menu(self, container: MenuContainer) -> bool:
        """
        Speichert komplettes Menü in Mandanten-DB (sys_menudaten)
        
        Args:
            container: MenuContainer mit allen Daten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        import sqlite3
        try:
            # Konvertiere zu Dictionary
            menu_dict = container.to_dict()
            menu_json = json.dumps(menu_dict, ensure_ascii=False, indent=2)
            
            # Direkter SQL-Zugriff
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # UPDATE oder INSERT
            cursor.execute(
                """
                INSERT OR REPLACE INTO sys_menudaten (uid, name, daten)
                VALUES (?, ?, ?)
                """,
                (container.MENU_GUID, container.MENU_NAME, menu_json)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Menü gespeichert: {container.MENU_NAME} ({container.MENU_GUID})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern von Menü {container.MENU_GUID}: {e}")
            return False
    
    def get_vertical_items(self, menu_guid: str) -> List[MenuItem]:
        """
        Lädt nur VERTIKAL-Items eines Menüs
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            Liste von MenuItem (sortiert nach SORT_ORDER)
        """
        container = self.get_menu(menu_guid)
        if not container:
            return []
        
        # Sortiere nach SORT_ORDER
        items = sorted(container.VERTIKAL, key=lambda x: x.SORT_ORDER)
        logger.info(f"📂 VERTIKAL Items für {menu_guid}: {len(items)}")
        return items
    
    def get_grund_items(self, menu_guid: str) -> List[MenuItem]:
        """
        Lädt nur GRUND-Items eines Menüs
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            Liste von MenuItem (sortiert nach SORT_ORDER)
        """
        container = self.get_menu(menu_guid)
        if not container:
            return []
        
        # Sortiere nach SORT_ORDER
        items = sorted(container.GRUND, key=lambda x: x.SORT_ORDER)
        logger.info(f"📂 GRUND Items für {menu_guid}: {len(items)}")
        return items
    
    def get_zusatz_items(self, menu_guid: str, parent_guid: str) -> List[MenuItem]:
        """
        Lädt ZUSATZ-Items für einen Parent
        
        Mit Vererbung: Wenn Item kein eigenes ZUSATZ_GUID hat,
        wird Parent-Kette aufwärts traversiert
        
        Args:
            menu_guid: GUID des Menüs
            parent_guid: GUID des Parent-Items
            
        Returns:
            Liste von MenuItem (sortiert nach SORT_ORDER)
        """
        container = self.get_menu(menu_guid)
        if not container:
            return []
        
        # Nutze Container-Methode für Vererbung
        items = container.get_zusatz_for_item(parent_guid)
        
        logger.info(f"📂 ZUSATZ Items für {parent_guid}: {len(items)}")
        return items
    
    def get_command(self, menu_guid: str, command_guid: str) -> Optional[MenuCommand]:
        """
        Lädt einzelnen Command aus Menü
        
        Args:
            menu_guid: GUID des Menüs
            command_guid: GUID des Commands
            
        Returns:
            MenuCommand oder None
        """
        container = self.get_menu(menu_guid)
        if not container:
            return None
        
        return container.get_command_by_guid(command_guid)
    
    def menu_exists(self, menu_guid: str) -> bool:
        """
        Prüft ob Menü existiert
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            True wenn existiert
        """
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sys_menudaten WHERE uid = ?",
                (menu_guid,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except:
            return False
    
    def list_all_menus(self) -> List[Dict[str, str]]:
        """
        Listet alle verfügbaren Menüs
        
        Returns:
            Liste von {MENU_GUID, MENU_NAME, IS_STARTMENU}
        """
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT uid, name, daten FROM sys_menudaten")
            rows = cursor.fetchall()
            conn.close()
            
            menus = []
            for uid, name, data_json in rows:
                try:
                    data = json.loads(data_json) if data_json else {}
                    menus.append({
                        'MENU_GUID': data.get('MENU_GUID', uid),
                        'MENU_NAME': data.get('MENU_NAME', name),
                        'IS_STARTMENU': data.get('IS_STARTMENU', False)
                    })
                except:
                    menus.append({
                        'MENU_GUID': uid,
                        'MENU_NAME': name,
                        'IS_STARTMENU': False
                    })
            
            logger.info(f"📋 {len(menus)} Menüs gefunden")
            return menus
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Listen der Menüs: {e}")
            return []
    
    def delete_menu(self, menu_guid: str) -> bool:
        """
        Löscht Menü aus Mandanten-DB
        
        Args:
            menu_guid: GUID des zu löschenden Menüs
            
        Returns:
            True bei Erfolg
        """
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sys_menudaten WHERE uid = ?", (menu_guid,))
            conn.commit()
            conn.close()
            
            logger.info(f"🗑️ Menü gelöscht: {menu_guid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen von Menü {menu_guid}: {e}")
            return False


# ===== GLOBAL INSTANCE =====
_storage_instance: Optional[V2MenuStorage] = None


def get_menu_storage() -> Optional[V2MenuStorage]:
    """
    Gibt globale Menu Storage Instanz zurück
    
    Singleton-Pattern für V2MenuStorage
    """
    global _storage_instance
    
    if _storage_instance is None:
        try:
            _storage_instance = V2MenuStorage()
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren von Menu Storage: {e}")
            return None
    
    return _storage_instance


if __name__ == "__main__":
    # ===== TEST (benötigt initialisiertes GCS!) =====
    print("🧪 V2 Menu Storage Test")
    print("=" * 60)
    print("⚠️ HINWEIS: Test benötigt initialisiertes GCS")
    print("   Führe v2_main.py aus für vollständigen Test")
    print("=" * 60)
    
    # Teste nur Schema-Import
    from v2_menu_schema import create_menu_item, create_command
    
    print("\n✅ Import erfolgreich")
    print("   MenuContainer: ✓")
    print("   MenuItem: ✓")
    print("   MenuCommand: ✓")
    print("   V2MenuStorage: ✓")
    
    print("\n🎯 Storage Module Ready!")
