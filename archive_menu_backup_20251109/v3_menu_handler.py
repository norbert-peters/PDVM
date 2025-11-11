"""
V3 Menu Handler - ULTRA EINFACH
================================
EINE Routine create_menu_from_items() für ALLES!

Autor: PDVM V3.0
Datum: 08.11.2025
"""

import logging
from typing import Optional, List
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton, QMenu, QAction

from v3_menu_system import LinearMenuLoader, MenuItem
from pdvm_central_systemsteuerung import get_gcs
from pdvm_command_handler import get_command_handler

logger = logging.getLogger(__name__)


class V3MenuHandler:
    """V3 Menu Handler - ULTRA EINFACH mit EINER rekursiven Routine"""
    
    def __init__(self, 
                 vertical_container: QWidget,
                 grund_container: QWidget,
                 zusatz_container: QWidget):
        """Initialisiert V3 Menu Handler"""
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("GCS nicht initialisiert - Login erforderlich!")
        
        self.command_handler = get_command_handler()
        if not self.command_handler:
            raise RuntimeError("Command Handler nicht initialisiert!")
        
        # Container
        self.vertical_container = vertical_container
        self.grund_container = grund_container
        self.zusatz_container = zusatz_container
        
        # Current State
        self.current_menu_guid: Optional[str] = None
        self.current_items: List[MenuItem] = []
        
        logger.info("✅ V3MenuHandler initialisiert (ULTRA EINFACH)")
    
    def load_menu(self, menu_guid: str) -> bool:
        """Lädt komplettes Menü (VERTIKAL + GRUND)"""
        try:
            logger.info(f"🎯 Lade V3-Menü: {menu_guid}")
            
            # Clear
            self._clear_all_containers()
            
            # Lade Items via LinearMenuLoader
            loader = LinearMenuLoader(menu_guid)
            menu_structure = loader.load_menu()
            
            if not menu_structure:
                logger.error("❌ Menü-Struktur nicht geladen")
                return False
            
            # Items extrahieren
            vertikal_items = menu_structure.get('VERTIKAL', [])
            grund_items = menu_structure.get('GRUND', [])
            
            # EINE Routine für beide!
            if vertikal_items:
                self._create_vertical_menu(vertikal_items)
            if grund_items:
                self._create_horizontal_menu(grund_items)
            
            self.current_menu_guid = menu_guid
            self.current_items = vertikal_items + grund_items
            
            logger.info(f"✅ V3-Menü komplett geladen: {menu_guid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von V3-Menü {menu_guid}: {e}", exc_info=True)
            return False
    
    def load_startmenu(self) -> bool:
        """
        Lädt Startmenü
        
        Wrapper für load_menu() mit Standard-Menü-GUID
        """
        # TODO: Hole Startmenü-GUID aus GCS
        # Für jetzt: Lade das AdminTestmenü
        start_menu_guid = "54073c2c-0efa-4979-8900-2bd1c53d5014"
        return self.load_menu(start_menu_guid)
    
    def _create_vertical_menu(self, items: List):
        """Erstellt vertikales Menü (links) mit EINER Routine"""
        logger.info(f"🔵 Erstelle Vertikal-Menü mit {len(items)} Items")
        
        # Top-Level Items
        top_items = [i for i in items if i.parent_guid is None and i.visible]
        top_items.sort(key=lambda x: x.sort_order)
        
        layout = self.vertical_container.layout()
        if not layout:
            layout = QVBoxLayout(self.vertical_container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
        
        for item in top_items:
            if item.type == 'SUBMENU':
                # Button mit Menü (EINE Routine!)
                button = QPushButton(item.label)
                button.setFixedHeight(40)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2c3e50;
                        color: white;
                        border: none;
                        padding: 8px;
                        text-align: left;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #34495e;
                    }
                """)
                
                # EINE Routine!
                menu = self._create_qmenu_recursive(items, item.guid)
                button.setMenu(menu)
                layout.addWidget(button)
                
            else:
                # Normaler Button
                button = QPushButton(item.label)
                button.setFixedHeight(40)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2c3e50;
                        color: white;
                        border: none;
                        padding: 8px;
                        text-align: left;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #34495e;
                    }
                """)
                button.clicked.connect(lambda checked=False, guid=item.guid: self._on_item_click(guid))
                layout.addWidget(button)
        
        layout.addStretch()
        logger.info(f"✅ Vertikalmenü angezeigt")
    
    def _create_horizontal_menu(self, items: List):
        """Erstellt horizontales Menü (oben) mit EINER Routine"""
        logger.info(f"🔴 Erstelle Horizontal-Menü mit {len(items)} Items")
        
        # Top-Level Items
        top_items = [i for i in items if i.parent_guid is None and i.visible]
        top_items.sort(key=lambda x: x.sort_order)
        
        logger.info(f"📊 {len(top_items)} Top-Level Items gefunden")
        
        # Menüleiste
        menubar = QMenuBar()
        menubar.setFixedHeight(45)
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                color: white;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QMenuBar::item:selected {
                background-color: #34495e;
                border-radius: 3px;
            }
        """)
        
        for item in top_items:
            logger.info(f"  📌 {item.label} ({item.type})")
            if item.type == 'SUBMENU':
                # EINE Routine!
                menu = self._create_qmenu_recursive(items, item.guid)
                action = menubar.addMenu(menu)
                action.setText(item.label)
                logger.info(f"     ✅ Submenu '{item.label}' hinzugefügt")
            else:
                # Direct Action
                action = menubar.addAction(item.label)
                action.triggered.connect(lambda checked=False, guid=item.guid: self._on_item_click(guid))
                logger.info(f"     ✅ Action '{item.label}' hinzugefügt")
        
        # Füge zu Container hinzu
        layout = self.grund_container.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout(self.grund_container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        
        layout.addWidget(menubar)
        self.grund_container.updateGeometry()
        menubar.show()
        
        logger.info(f"✅ Grundmenü angezeigt (Menüleiste mit {len(top_items)} Einträgen)")
    
    def _create_qmenu_recursive(self, all_items: List, parent_guid: str):
        """EINE Routine für rekursive Menü-Erstellung"""
        menu = QMenu()
        
        # Filtere Kinder
        children = [i for i in all_items if i.parent_guid == parent_guid and i.visible]
        children.sort(key=lambda x: x.sort_order)
        
        for child in children:
            if child.type == 'SEPARATOR':
                menu.addSeparator()
            elif child.type == 'SUBMENU':
                # REKURSIV!
                submenu = self._create_qmenu_recursive(all_items, child.guid)
                submenu_action = menu.addMenu(submenu)
                submenu_action.setText(child.label)
            else:
                # Button
                action = QAction(child.label, menu)
                action.triggered.connect(lambda checked=False, guid=child.guid: self._on_item_click(guid))
                menu.addAction(action)
        
        return menu
    
    def _on_item_click(self, item_guid: str):
        """Handler für Item-Klick"""
        try:
            logger.info(f"🔘 Item geklickt: {item_guid}")
            
            # Finde Item
            item = next((i for i in self.current_items if i.guid == item_guid), None)
            if not item:
                logger.warning(f"⚠️ Item nicht gefunden: {item_guid}")
                return
            
            # Führe Command aus
            if item.command and self.command_handler:
                handler_name = item.command.get('handler')
                params = item.command.get('params', {})
                logger.info(f"📞 Führe Command aus: {handler_name}")
                self.command_handler.execute_command(handler_name, params)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Item-Click: {e}", exc_info=True)
    
    def _clear_all_containers(self):
        """Leert alle Container"""
        for container in [self.vertical_container, self.grund_container, self.zusatz_container]:
            if container.layout():
                while container.layout().count():
                    child = container.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()


# ===== SINGLETON =====
_handler_instance = None

def get_v3_menu_handler(
    vertical_container: QWidget = None,
    grund_container: QWidget = None,
    zusatz_container: QWidget = None
) -> Optional[V3MenuHandler]:
    """Singleton Getter für V3MenuHandler"""
    global _handler_instance
    if _handler_instance is None and all([vertical_container, grund_container, zusatz_container]):
        _handler_instance = V3MenuHandler(vertical_container, grund_container, zusatz_container)
    return _handler_instance
