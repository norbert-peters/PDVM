"""
V3 Menu System - Linear & PDVM-Konform
======================================
Vereinfachtes Menüsystem basierend auf V2 PdvmCentralDatenbank

Struktur in sys_menudaten.daten (JSON):
{
    "META": {"version": "V3", ...},
    "VERTIKAL": [MenuItem-JSON, ...],
    "GRUND": [MenuItem-JSON, ...],
    "ZUSATZ": [MenuItem-JSON, ...]
}

Command ist DIREKT im Item integriert (1:1 Beziehung)

WICHTIG: Nutzt v2_pdvm_central_datenbank (V2-Architektur mit GCS)!
         KEIN direkter SQL-Zugriff!

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from v2_pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


# ===== ITEM TYPES =====

class ItemType:
    """Item-Typen (einfache Strings statt Enum)"""
    BUTTON = "BUTTON"
    SUBMENU = "SUBMENU"
    SEPARATOR = "SEPARATOR"
    SPACER = "SPACER"


# ===== MENU ITEM (mit integriertem Command) =====

@dataclass
class MenuItem:
    """
    Menü-Item mit integriertem Command
    
    Struktur wird als JSON in PdvmCentralDatenbank gespeichert:
    - Gruppe: VERTIKAL, GRUND oder ZUSATZ
    - Feld: Item-GUID
    - Wert: JSON von diesem Objekt
    """
    # Pflichtfelder
    guid: str
    type: str  # ItemType.BUTTON, SUBMENU, etc.
    label: str
    sort_order: int
    
    # Optionale Felder
    parent_guid: Optional[str] = None
    template_guid: Optional[str] = None  # Für SPACER-Items
    icon: Optional[str] = None
    visible: bool = True
    enabled: bool = True
    tooltip: Optional[str] = None
    
    # Command direkt integriert (1:1 Beziehung)
    command: Optional[Dict[str, Any]] = None  # {"handler": "...", "params": {...}}
    
    def to_json(self) -> str:
        """Konvertiert zu JSON für Speicherung"""
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str) -> 'MenuItem':
        """Erstellt MenuItem aus JSON"""
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return MenuItem(**data)
    
    def has_command(self) -> bool:
        """Prüft ob Item einen Command hat"""
        return self.command is not None and 'handler' in self.command


# ===== MENU LOADER (Linear mit Template-Integration) =====

class LinearMenuLoader:
    """
    Lädt Menü linear aus sys_menudaten via v2_pdvm_central_datenbank
    Integriert Templates automatisch
    
    V3-Struktur in sys_menudaten.daten:
    {
        "META": {"version": "V3", ...},
        "VERTIKAL": [MenuItem-JSON, ...],
        "GRUND": [MenuItem-JSON, ...],
        "ZUSATZ": [MenuItem-JSON, ...]
    }
    
    WICHTIG: Nutzt v2_pdvm_central_datenbank (holt DB-Pfad aus GCS)
             GCS muss initialisiert sein (nach Login)!
    """
    
    def __init__(self, menu_guid: str):
        """
        Initialisiert Loader mit v2_pdvm_central_datenbank
        
        Args:
            menu_guid: GUID des zu ladenden Menüs
            
        Raises:
            ValueError: Wenn GCS nicht initialisiert ist
        """
        self.menu_guid = menu_guid
        
        # v2_pdvm_central_datenbank nutzen (holt DB-Pfad aus GCS)
        self.menu_db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        
        self.menu_data: Optional[Dict[str, Any]] = None
        self.template_cache: Dict[str, PdvmCentralDatenbank] = {}
        
        logger.info(f"🔧 LinearMenuLoader initialisiert für Menü: {menu_guid}")
    
    def load_menu(self) -> Dict[str, List[MenuItem]]:
        """
        Lädt komplettes Menü mit Template-Integration via PdvmCentralDatenbank
        
        Ablauf:
        1. V3-JSON aus PdvmCentralDatenbank laden
        2. Für jede Gruppe (VERTIKAL, GRUND, ZUSATZ):
           - Items durchlaufen
           - SPACER mit TEMPLATE_GUID finden
           - Template-Items einfügen
        3. Fertige Struktur zurückgeben
        
        Returns:
            {
                'VERTIKAL': [MenuItem, ...],
                'GRUND': [MenuItem, ...],
                'ZUSATZ': [MenuItem, ...]
            }
        """
        logger.info(f"📂 Lade Menü: {self.menu_guid}")
        
        # 1. V3-JSON aus PdvmCentralDatenbank laden
        self._load_menu_data()
        
        if not self.menu_data:
            logger.error(f"❌ Menü nicht gefunden: {self.menu_guid}")
            return {'VERTIKAL': [], 'GRUND': [], 'ZUSATZ': []}
        
        # META-Gruppe prüfen (V3 oder VERSION = V3)
        meta = self.menu_data.get('META', {})
        version = meta.get('VERSION') or meta.get('version', 'V3')
        logger.debug(f"   📋 Menü-Version: {version}")
        
        # 2. Für jede Gruppe Template-Integration durchführen
        result = {}
        for gruppe in ['VERTIKAL', 'GRUND', 'ZUSATZ']:
            logger.debug(f"   Verarbeite Gruppe: {gruppe}")
            items = self._process_gruppe(gruppe)
            result[gruppe] = items
            logger.info(f"   ✅ {gruppe}: {len(items)} Items")
        
        logger.info(f"✅ Menü geladen: {len(result['VERTIKAL'])} VERTIKAL, "
                   f"{len(result['GRUND'])} GRUND, {len(result['ZUSATZ'])} ZUSATZ")
        
        return result
    
    def _load_menu_data(self):
        """
        Lädt V3-JSON via v2_pdvm_central_datenbank
        
        PdvmCentralDatenbank lädt automatisch die 'daten'-Spalte als JSON
        """
        try:
            # menu_db.data enthält bereits die geladenen Daten
            self.menu_data = self.menu_db.data
            
            if self.menu_data and len(self.menu_data) > 0:
                logger.debug(f"   📦 Menü-Daten geladen: {len(self.menu_data)} Gruppen")
            else:
                logger.error(f"   ❌ Menü nicht gefunden oder leer: {self.menu_guid}")
                self.menu_data = None
                
        except Exception as e:
            logger.error(f"   ❌ Fehler beim Laden: {e}")
            import traceback
            traceback.print_exc()
            self.menu_data = None
    
    def _process_gruppe(self, gruppe: str) -> List[MenuItem]:
        """
        Verarbeitet eine Gruppe mit Template-Integration
        
        NEUE STRUKTUR: Gruppe ist Dict mit guid → item_data
        
        Args:
            gruppe: VERTIKAL, GRUND oder ZUSATZ
            
        Returns:
            Liste von MenuItems (mit eingefügten Template-Items)
        """
        items: List[MenuItem] = []
        
        # Items aus menu_data holen (jetzt Dict: guid → item_data)
        items_dict = self.menu_data.get(gruppe, {})
        
        # Dict → List mit guid hinzugefügt
        for guid, item_data in items_dict.items():
            # guid zu item_data hinzufügen (wird vom Dict-Key genommen)
            item_data_with_guid = {'guid': guid, **item_data}
            
            # Als MenuItem erstellen
            item = MenuItem.from_json(item_data_with_guid)
            
            # Prüfen ob Template-Item (SPACER mit template_guid)
            if item.type == ItemType.SPACER and item.template_guid:
                logger.info(f"   🔗 Template gefunden: {item.template_guid}")
                # Template-Items einfügen
                template_items = self._load_template_items(
                    item.template_guid, 
                    gruppe, 
                    item.sort_order
                )
                items.extend(template_items)
                logger.info(f"      → {len(template_items)} Template-Items eingefügt")
            else:
                # Normales Item
                items.append(item)
        
        # Nach sort_order sortieren
        items.sort(key=lambda x: x.sort_order)
        
        return items
    
    def _load_template_items(
        self, 
        template_guid: str, 
        gruppe: str,
        base_sort_order: int
    ) -> List[MenuItem]:
        """
        Lädt Template-Items via v2_pdvm_central_datenbank und passt Parent/Order an
        
        Args:
            template_guid: GUID des Templates
            gruppe: Gruppe (VERTIKAL/GRUND/ZUSATZ)
            base_sort_order: Basis-Sort-Order vom SPACER-Item
            
        Returns:
            Liste von angepassten Template-Items
        """
        # Template aus Cache oder neu laden
        if template_guid not in self.template_cache:
            logger.debug(f"      Lade Template: {template_guid}")
            
            try:
                # v2_pdvm_central_datenbank für Template erstellen
                template_db = PdvmCentralDatenbank('sys_menudaten', template_guid)
                
                if template_db.data and len(template_db.data) > 0:
                    self.template_cache[template_guid] = template_db
                    logger.debug(f"      ✅ Template geladen und gecached")
                else:
                    logger.error(f"      ❌ Template nicht gefunden: {template_guid}")
                    return []
                    
            except Exception as e:
                logger.error(f"      ❌ Fehler beim Template-Laden: {e}")
                import traceback
                traceback.print_exc()
                return []
        
        # Template-Datenbank aus Cache holen
        template_db = self.template_cache[template_guid]
        template_data = template_db.data
        
        # Template-Items aus der Gruppe holen (NEUE STRUKTUR: Dict)
        template_items_dict = template_data.get(gruppe, {})
        items: List[MenuItem] = []
        
        # Dict → List mit guid
        for guid, item_data in template_items_dict.items():
            item_data_with_guid = {'guid': guid, **item_data}
            item = MenuItem.from_json(item_data_with_guid)
            
            # Sort-Order anpassen (micro-adjust für Einfüge-Position)
            # Template-Items bekommen Positionen zwischen base_sort_order und base_sort_order+1
            item.sort_order = base_sort_order + (item.sort_order * 0.01)
            
            items.append(item)
        
        logger.debug(f"      ✅ {len(items)} Template-Items geladen")
        return items
    
    def get_menu_name(self) -> str:
        """Holt Menü-Namen aus Metadaten"""
        if not self.menu_data:
            return "Unbekannt"
        
        # Name aus META-Gruppe holen
        meta = self.menu_data.get('META', {})
        return meta.get('name', 'Unbekannt')


# ===== MENU BUILDER (PyQt5 Widgets) =====

class LinearMenuBuilder:
    """
    Baut PyQt5 Menü-Widgets aus MenuItem-Strukturen
    
    Linear und einfach - keine komplexen Container mehr!
    """
    
    def __init__(self):
        """Initialisiert Builder"""
        self.loader: Optional[LinearMenuLoader] = None
        logger.info("✅ LinearMenuBuilder initialisiert")
    
    def build_menu(self, menu_guid: str) -> Dict[str, Any]:
        """
        Baut komplettes Menü
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            {
                'vertikal_widget': QWidget,
                'grund_widget': QWidget,
                'menu_data': {
                    'VERTIKAL': [MenuItem, ...],
                    'GRUND': [MenuItem, ...],
                    'ZUSATZ': [MenuItem, ...]
                }
            }
        """
        logger.info(f"🏗️ Baue Menü: {menu_guid}")
        
        # 1. Menü laden (mit Template-Integration)
        self.loader = LinearMenuLoader(menu_guid)
        menu_data = self.loader.load_menu()
        
        # 2. Widgets erstellen
        # TODO: Hier PyQt5 Widget-Erstellung implementieren
        # Für jetzt nur Datenstruktur zurückgeben
        
        return {
            'menu_guid': menu_guid,
            'menu_name': self.loader.get_menu_name(),
            'menu_data': menu_data
        }


# ===== HELPER FUNCTIONS =====

def create_menu_item(
    guid: str,
    label: str,
    item_type: str = ItemType.BUTTON,
    sort_order: int = 0,
    **kwargs
) -> MenuItem:
    """
    Helper-Funktion zum einfachen Erstellen von MenuItems
    
    Beispiel:
        item = create_menu_item(
            "guid-123",
            "Personen",
            ItemType.BUTTON,
            sort_order=1,
            command={"handler": "open_view", "params": {"view_guid": "..."}}
        )
    """
    return MenuItem(
        guid=guid,
        type=item_type,
        label=label,
        sort_order=sort_order,
        **kwargs
    )


if __name__ == "__main__":
    # ===== TEST =====
    print("🧪 V3 Menu System Test")
    print("=" * 80)
    
    # Test MenuItem
    item = create_menu_item(
        "test-guid-001",
        "Personen anzeigen",
        ItemType.BUTTON,
        sort_order=1,
        command={
            "handler": "open_view",
            "params": {"view_guid": "view-personen-123"}
        },
        icon="person.png"
    )
    
    print("\n✅ MenuItem erstellt:")
    print(f"   Label: {item.label}")
    print(f"   Type: {item.type}")
    print(f"   Command: {item.command}")
    
    # Test JSON Serialisierung
    json_str = item.to_json()
    print(f"\n✅ JSON: {json_str}")
    
    # Test Deserialisierung
    restored = MenuItem.from_json(json_str)
    print(f"\n✅ Restored: {restored.label}")
    
    print("\n" + "=" * 80)
    print("🎯 V3 Menu System Ready!")
