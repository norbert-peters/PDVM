"""
PDVM Menü Matrix Builder
=========================
Einheitliche Matrix-Struktur für Menü-Darstellung

KONZEPT:
--------
1. MenuItem-Daten aus DB → Matrix-Struktur (hierarchisch)
2. Matrix → Renderer (horizontal/vertikal) → UI
3. IDENTISCH für Editor und System

Autor: PDVM V2.0
Datum: 08.11.2025
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pdvm_menu_schema import MenuItem, MenuItemType

logger = logging.getLogger(__name__)


@dataclass
class MenuNode:
    """
    Ein Knoten in der Menü-Hierarchie
    
    Attributes:
        item: Das MenuItem-Objekt
        children: Liste der Kind-Knoten (sortiert nach SORT_ORDER)
        level: Hierarchie-Ebene (0 = Top-Level)
    """
    item: MenuItem
    children: List['MenuNode']
    level: int
    
    def __repr__(self):
        indent = "  " * self.level
        return f"{indent}[{self.level}] {self.item.LABEL} ({self.item.TYPE.value}) - {len(self.children)} children"


class MenuMatrixBuilder:
    """
    Baut hierarchische Matrix-Struktur aus flachen MenuItem-Listen
    
    PRINZIP:
    --------
    Input:  Liste von MenuItem (flach, mit PARENT_GUID + SORT_ORDER)
    Output: Hierarchische MenuNode-Struktur (Baum)
    
    VERWENDUNG:
    -----------
    # System-Menü
    builder = MenuMatrixBuilder(menu_items)
    tree = builder.build_tree()
    renderer.render_horizontal(tree)  # oder render_vertical(tree)
    
    # Editor
    builder = MenuMatrixBuilder(menu_items)
    tree = builder.build_tree()
    editor.show_tree(tree)  # Drag & Drop nur für SORT_ORDER
    """
    
    def __init__(self, items: List[MenuItem]):
        """
        Initialisiert Builder mit MenuItem-Liste
        
        Args:
            items: Liste von MenuItem-Objekten (flach)
        """
        self.items = items
        self._guid_map: Dict[str, MenuItem] = {}
        self._build_guid_map()
    
    def _build_guid_map(self):
        """Erstellt GUID → MenuItem Mapping für schnellen Zugriff"""
        self._guid_map = {item.GUID: item for item in self.items if item.VISIBLE}
        logger.info(f"📊 GUID-Map erstellt: {len(self._guid_map)} Items")
    
    def build_tree(self) -> List[MenuNode]:
        """
        Baut hierarchische Baum-Struktur
        
        Returns:
            Liste der Top-Level MenuNodes (mit rekursiven children)
        """
        # 1. Finde Top-Level Items (PARENT_GUID = None)
        top_level_items = [
            item for item in self.items 
            if item.PARENT_GUID is None and item.VISIBLE
        ]
        
        # 2. Sortiere nach SORT_ORDER
        top_level_items.sort(key=lambda x: x.SORT_ORDER)
        
        # 3. Baue rekursiv Knoten
        tree = []
        for item in top_level_items:
            node = self._build_node_recursive(item, level=0)
            tree.append(node)
        
        logger.info(f"✅ Menü-Baum gebaut: {len(tree)} Top-Level Items")
        self._log_tree(tree)
        
        return tree
    
    def _build_node_recursive(self, item: MenuItem, level: int) -> MenuNode:
        """
        Rekursiv Knoten bauen mit allen Kindern
        
        Args:
            item: MenuItem-Objekt
            level: Hierarchie-Ebene
            
        Returns:
            MenuNode mit allen Kindern (rekursiv)
        """
        # Finde alle direkten Kinder
        children_items = [
            child for child in self.items
            if child.PARENT_GUID == item.GUID and child.VISIBLE
        ]
        
        # Sortiere nach SORT_ORDER
        children_items.sort(key=lambda x: x.SORT_ORDER)
        
        # Baue Kind-Knoten rekursiv
        children_nodes = []
        for child in children_items:
            child_node = self._build_node_recursive(child, level + 1)
            children_nodes.append(child_node)
        
        # Erstelle Knoten
        node = MenuNode(
            item=item,
            children=children_nodes,
            level=level
        )
        
        return node
    
    def _log_tree(self, tree: List[MenuNode], indent: int = 0):
        """Loggt Baum-Struktur (rekursiv) für Debugging"""
        for node in tree:
            prefix = "  " * indent
            logger.debug(f"{prefix}📁 [{node.level}] {node.item.LABEL} ({node.item.TYPE.value})")
            if node.children:
                self._log_tree(node.children, indent + 1)
    
    def get_flat_list_with_levels(self) -> List[tuple[MenuItem, int]]:
        """
        Gibt flache Liste mit Level-Info zurück (für Editor-Ansicht)
        
        Returns:
            Liste von (MenuItem, level) Tupeln
        """
        tree = self.build_tree()
        flat_list = []
        
        def traverse(nodes: List[MenuNode]):
            for node in nodes:
                flat_list.append((node.item, node.level))
                if node.children:
                    traverse(node.children)
        
        traverse(tree)
        return flat_list
    
    def get_parent_choices(self) -> List[tuple[str, str, int]]:
        """
        Gibt alle möglichen Parents zurück (für Parent-Auswahl-Dropdown)
        
        Returns:
            Liste von (guid, label, level) Tupeln
            Enthält auch "Keine (Top-Level)" Option
        """
        choices = [("", "📌 Keine (Top-Level)", 0)]
        
        # Baue Baum für Level-Info
        tree = self.build_tree()
        
        def traverse(nodes: List[MenuNode]):
            for node in nodes:
                # Nur SUBMENUs können Parents sein
                if node.item.TYPE == MenuItemType.SUBMENU:
                    indent = "  " * node.level
                    label = f"{indent}📁 {node.item.LABEL}"
                    choices.append((node.item.GUID, label, node.level))
                
                if node.children:
                    traverse(node.children)
        
        traverse(tree)
        return choices


# ===== TEST =====
if __name__ == "__main__":
    from pdvm_menu_schema import create_menu_item
    
    print("🧪 Menu Matrix Builder Test")
    print("=" * 60)
    
    # Test-Daten: 3-Ebenen Hierarchie
    items = [
        # Top-Level
        create_menu_item("item-1", "Stammdaten", MenuItemType.SUBMENU, 0, PARENT_GUID=None),
        create_menu_item("item-2", "Berichte", MenuItemType.SUBMENU, 1, PARENT_GUID=None),
        
        # Ebene 2 unter Stammdaten
        create_menu_item("item-3", "Personen", MenuItemType.SUBMENU, 0, PARENT_GUID="item-1"),
        create_menu_item("item-4", "Firmen", MenuItemType.BUTTON, 1, PARENT_GUID="item-1"),
        
        # Ebene 3 unter Personen
        create_menu_item("item-5", "Alle Personen", MenuItemType.BUTTON, 0, PARENT_GUID="item-3"),
        create_menu_item("item-6", "Neue Person", MenuItemType.BUTTON, 1, PARENT_GUID="item-3"),
        
        # Ebene 2 unter Berichte
        create_menu_item("item-7", "Umsatz", MenuItemType.BUTTON, 0, PARENT_GUID="item-2"),
    ]
    
    # Baue Matrix
    builder = MenuMatrixBuilder(items)
    tree = builder.build_tree()
    
    print(f"\n✅ Baum gebaut: {len(tree)} Top-Level Items")
    print("\n📊 Hierarchie:")
    for node in tree:
        print(node)
        for child in node.children:
            print(child)
            for grandchild in child.children:
                print(grandchild)
    
    # Flache Liste
    flat = builder.get_flat_list_with_levels()
    print(f"\n📋 Flache Liste ({len(flat)} Items):")
    for item, level in flat:
        indent = "  " * level
        print(f"{indent}[{level}] {item.LABEL}")
    
    # Parent Choices
    choices = builder.get_parent_choices()
    print(f"\n🎯 Parent-Auswahl ({len(choices)} Optionen):")
    for guid, label, level in choices:
        print(f"  {label} (Level {level})")
    
    print("\n" + "=" * 60)
    print("🎯 Matrix Builder Complete!")
