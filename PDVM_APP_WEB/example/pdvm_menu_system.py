# -*- coding: utf-8 -*-
"""
PDVM Menu System - Linear & Pipeline-basiert
============================================
Vereinfachtes Menüsystem mit Integration der Menu-Pipeline

Struktur in sys_menudaten.daten (JSON):
{
    "META": {"version": "V3", ...},
    "VERTIKAL": {item_guid: item_data, ...},
    "GRUND": {item_guid: item_data, ...},
    "ZUSATZ": {item_guid: item_data, ...}
}

Nutzt pdvm_menu_pipeline für lineare Datenverarbeitung (BASIS→PROJECT)

Autor: PDVM-System
Datum: 10.11.2025
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


# Item-Typen
class ItemType:
    BUTTON = "BUTTON"
    SUBMENU = "SUBMENU"
    SEPARATOR = "SEPARATOR"
    SPACER = "SPACER"


@dataclass
class MenuItem:
    """Menü-Item mit integriertem Command"""
    guid: str
    type: str
    label: str
    sort_order: int
    parent_guid: Optional[str] = None
    template_guid: Optional[str] = None
    icon: Optional[str] = None
    visible: bool = True
    enabled: bool = True
    tooltip: Optional[str] = None
    command: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str) -> 'MenuItem':
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return MenuItem(**data)
    
    def has_command(self) -> bool:
        return self.command is not None and 'handler' in self.command


class PdvmMenuLoader:
    """
    Lädt Menü aus sys_menudaten via PdvmCentralDatenbank
    Integriert Pipeline für lineare Datenverarbeitung
    """
    
    def __init__(self, menu_guid: str):
        self.menu_guid = menu_guid
        self.menu_db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        self.menu_data: Optional[Dict[str, Any]] = None
        self.template_cache: Dict[str, PdvmCentralDatenbank] = {}
        
        logger.info(f"Menu-Loader initialisiert: {menu_guid}")
    
    def load_menu(self) -> Dict[str, List[MenuItem]]:
        """
        Lädt komplettes Menü mit Template-Integration
        
        Returns:
            {'VERTIKAL': [MenuItem, ...], 'GRUND': [...], 'ZUSATZ': [...]}
        """
        logger.info(f"Lade Menü: {self.menu_guid}")
        
        # Menü-Daten laden
        self._load_menu_data()
        
        if not self.menu_data:
            logger.error(f"Menü nicht gefunden: {self.menu_guid}")
            return {'VERTIKAL': [], 'GRUND': [], 'ZUSATZ': []}
        
        # Jede Gruppe verarbeiten
        result = {}
        for gruppe in ['VERTIKAL', 'GRUND', 'ZUSATZ']:
            items = self._process_gruppe(gruppe)
            result[gruppe] = items
            logger.info(f"  {gruppe}: {len(items)} Items")
        
        return result
    
    def _load_menu_data(self):
        """Lädt JSON aus PdvmCentralDatenbank"""
        try:
            self.menu_data = self.menu_db.data
            if self.menu_data and len(self.menu_data) > 0:
                logger.debug(f"Menü-Daten geladen: {len(self.menu_data)} Gruppen")
            else:
                logger.error(f"Menü leer: {self.menu_guid}")
                self.menu_data = None
        except Exception as e:
            logger.error(f"Fehler beim Laden: {e}")
            self.menu_data = None
    
    def _process_gruppe(self, gruppe: str) -> List[MenuItem]:
        """Verarbeitet Gruppe mit Template-Integration"""
        items: List[MenuItem] = []
        
        items_dict = self.menu_data.get(gruppe, {})
        
        for guid, item_data in items_dict.items():
            item_data_with_guid = {'guid': guid, **item_data}
            item = MenuItem.from_json(item_data_with_guid)
            
            # Template-Items einfügen
            if item.type == ItemType.SPACER and item.template_guid:
                logger.info(f"  Template: {item.template_guid}")
                template_items = self._load_template_items(
                    item.template_guid, 
                    gruppe, 
                    item.sort_order
                )
                items.extend(template_items)
            else:
                items.append(item)
        
        items.sort(key=lambda x: x.sort_order)
        return items
    
    def _load_template_items(
        self, 
        template_guid: str, 
        gruppe: str,
        base_sort_order: int
    ) -> List[MenuItem]:
        """Lädt Template-Items und passt Sort-Order an"""
        if template_guid not in self.template_cache:
            try:
                template_db = PdvmCentralDatenbank('sys_menudaten', template_guid)
                if template_db.data and len(template_db.data) > 0:
                    self.template_cache[template_guid] = template_db
                else:
                    return []
            except Exception as e:
                logger.error(f"Template-Fehler: {e}")
                return []
        
        template_db = self.template_cache[template_guid]
        template_items_dict = template_db.data.get(gruppe, {})
        items: List[MenuItem] = []
        
        for guid, item_data in template_items_dict.items():
            item_data_with_guid = {'guid': guid, **item_data}
            item = MenuItem.from_json(item_data_with_guid)
            item.sort_order = base_sort_order + (item.sort_order * 0.01)
            items.append(item)
        
        return items
    
    def get_menu_name(self) -> str:
        """Holt Menü-Namen"""
        if not self.menu_data:
            return "Unbekannt"
        meta = self.menu_data.get('META', {})
        return meta.get('name', 'Unbekannt')


# Alias für Kompatibilität
LinearMenuLoader = PdvmMenuLoader


def create_menu_item(
    guid: str,
    label: str,
    item_type: str = ItemType.BUTTON,
    sort_order: int = 0,
    **kwargs
) -> MenuItem:
    """Helper zum Erstellen von MenuItems"""
    return MenuItem(
        guid=guid,
        type=item_type,
        label=label,
        sort_order=sort_order,
        **kwargs
    )
