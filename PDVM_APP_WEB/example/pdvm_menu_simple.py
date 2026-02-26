"""
PDVM Menü - ULTRA EINFACH
==========================
EINE Methode für ALLES

KONZEPT:
- MenuItem-Liste → QMenu (rekursiv)
- Egal ob Editor oder System
- Nur Click-Handler unterschiedlich

Autor: PDVM V2.0
Datum: 08.11.2025
"""

import logging
from typing import List, Callable, Optional
from pathlib import Path
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QIcon

from pdvm_menu_schema import MenuItem, MenuItemType

logger = logging.getLogger(__name__)


def create_menu_from_items(
    items: List[MenuItem],
    parent_guid: Optional[str],
    on_click: Callable[[str], None]
) -> QMenu:
    """
    EINZIGE Methode die aus MenuItem-Liste ein QMenu erstellt
    
    VERWENDUNG:
    -----------
    # System: Führt Command aus
    menu = create_menu_from_items(items, None, lambda guid: execute_command(guid))
    
    # Editor: Öffnet Item-Editor
    menu = create_menu_from_items(items, None, lambda guid: open_editor(guid))
    
    Args:
        items: Liste ALLER MenuItems (flach)
        parent_guid: Nur Items mit diesem Parent (None = Top-Level)
        on_click: Callback(item_guid) bei Klick
        
    Returns:
        QMenu mit kompletter Hierarchie (rekursiv)
    """
    menu = QMenu()
    
    # Filtere Items mit passendem Parent
    children = [
        item for item in items
        if item.PARENT_GUID == parent_guid and item.VISIBLE
    ]
    
    # Sortiere nach SORT_ORDER
    children.sort(key=lambda x: x.SORT_ORDER)
    
    # Erstelle Menü-Einträge
    for item in children:
        if item.TYPE == MenuItemType.SEPARATOR:
            # Separator
            menu.addSeparator()
            
        elif item.TYPE == MenuItemType.SUBMENU:
            # Submenu (REKURSIV!)
            submenu = create_menu_from_items(items, item.GUID, on_click)
            submenu_action = menu.addMenu(submenu)
            submenu_action.setText(item.LABEL)
            
            # Icon
            if item.ICON:
                icon_path = Path(item.ICON)
                if icon_path.exists():
                    submenu_action.setIcon(QIcon(str(icon_path)))
            
            # Tooltip
            if item.TOOLTIP:
                submenu_action.setToolTip(item.TOOLTIP)
                
        else:
            # Button/Action
            action = QAction(item.LABEL, menu)
            
            # Icon
            if item.ICON:
                icon_path = Path(item.ICON)
                if icon_path.exists():
                    action.setIcon(QIcon(str(icon_path)))
            
            # Tooltip
            if item.TOOLTIP:
                action.setToolTip(item.TOOLTIP)
            
            # Click-Handler
            action.triggered.connect(lambda checked=False, guid=item.GUID: on_click(guid))
            
            menu.addAction(action)
    
    return menu


# ===== TEST =====
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar
    from pdvm_menu_schema import create_menu_item
    import sys
    
    print("🧪 ULTRA EINFACHES Menü-System Test")
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
        create_menu_item("item-7", "VIP Kunden", MenuItemType.SUBMENU, 2, PARENT_GUID="item-3"),
        
        # Ebene 4 unter VIP Kunden
        create_menu_item("item-8", "Gold Kunden", MenuItemType.BUTTON, 0, PARENT_GUID="item-7"),
        create_menu_item("item-9", "Platin Kunden", MenuItemType.BUTTON, 1, PARENT_GUID="item-7"),
        
        # Ebene 2 unter Berichte
        create_menu_item("item-10", "Umsatz", MenuItemType.BUTTON, 0, PARENT_GUID="item-2"),
    ]
    
    # Callback
    def on_click(guid: str):
        item = next((i for i in items if i.GUID == guid), None)
        if item:
            print(f"🔘 Clicked: {item.LABEL} ({guid})")
    
    # Qt Application
    app = QApplication(sys.argv)
    
    # Hauptfenster
    window = QMainWindow()
    window.setWindowTitle("Ultra Einfaches Menü")
    window.setGeometry(100, 100, 800, 600)
    
    # Menüleiste
    menubar = window.menuBar()
    
    # Erstelle Menüs mit EINER Methode!
    stammdaten_menu = create_menu_from_items(items, "item-1", on_click)
    menubar.addMenu(stammdaten_menu).setText("Stammdaten")
    
    berichte_menu = create_menu_from_items(items, "item-2", on_click)
    menubar.addMenu(berichte_menu).setText("Berichte")
    
    window.show()
    
    print("✅ Menüs erstellt mit EINER Methode!")
    print("   - Stammdaten (mit 3-Ebenen Verschachtelung)")
    print("   - Berichte")
    print("=" * 60)
    
    sys.exit(app.exec_())
