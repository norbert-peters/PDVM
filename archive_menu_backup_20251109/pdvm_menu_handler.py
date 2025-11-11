"""
PDVM Menu Handler - ULTRA EINFACH
==================================
EINE Routine fuer ALLES - Keine Versionen, nur PDVM!

Autor: PDVM 0.9
Datum: 08.11.2025
"""

import logging
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QPushButton, QMenu, QAction

from pdvm_menu_storage import get_menu_storage
from pdvm_central_systemsteuerung import get_gcs
from pdvm_command_handler import get_command_handler

logger = logging.getLogger(__name__)


class PdvmMenuHandler:
    """PDVM Menu Handler - EINFACH!"""
    
    def __init__(self, vertical_container, grund_container, zusatz_container):
        """Initialisiert Menu Handler"""
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("GCS nicht initialisiert!")
        
        self.storage = get_menu_storage()
        if not self.storage:
            raise RuntimeError("Menu Storage nicht initialisiert!")
        
        self.command_handler = get_command_handler()
        if not self.command_handler:
            raise RuntimeError("Command Handler nicht initialisiert!")
        
        self.vertical_container = vertical_container
        self.grund_container = grund_container
        self.zusatz_container = zusatz_container
        
        self.current_menu_guid = None
        self.current_container = None
        
        logger.info("PdvmMenuHandler initialisiert")
    
    def load_startmenu(self):
        """Laedt Startmenue mit Security-Check"""
        try:
            logger.info("Lade Startmenue mit Security-Check")
            
            # Hole User-Apps aus gcs._u_db
            user_data = getattr(self.gcs, '_user_data', {})
            meine_apps = user_data.get('MEINEAPPS', {})
            start_menu_guid = meine_apps.get('START')
            
            if not start_menu_guid:
                logger.error("Kein Startmenue in User-Daten definiert")
                return False
            
            logger.info(f"Startmenue-GUID: {start_menu_guid}")
            
            # Pruefe ob Menue existiert
            if not self.storage.menu_exists(start_menu_guid):
                logger.error(f"Startmenue {start_menu_guid} existiert nicht")
                return False
            
            # Lade Menue
            return self.load_menu(start_menu_guid)
            
        except Exception as e:
            logger.error(f"Fehler beim Laden von Startmenue: {e}", exc_info=True)
            return False
    
    def load_menu(self, menu_guid):
        """Laedt Menue (VERTIKAL + HORIZONTAL)"""
        try:
            logger.info(f"Lade Menue: {menu_guid}")
            
            self._clear_all()
            
            self.current_container = self.storage.get_menu(menu_guid)
            if not self.current_container:
                logger.error(f"Menue nicht gefunden: {menu_guid}")
                return False
            
            if self.current_container.VERTIKAL:
                self._create_vertical(self.current_container.VERTIKAL)
            
            if self.current_container.GRUND:
                self._create_horizontal(self.current_container.GRUND)
            
            self.current_menu_guid = menu_guid
            logger.info(f"Menue geladen: {menu_guid}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden: {e}", exc_info=True)
            return False
    
    def _create_vertical(self, items):
        """Erstellt Vertikal-Menue"""
        logger.info(f"Erstelle Vertikal-Menue ({len(items)} Items)")
        
        layout = self.vertical_container.layout()
        if not layout:
            layout = QVBoxLayout(self.vertical_container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
        
        top = [i for i in items if i.PARENT_GUID is None and i.VISIBLE]
        top.sort(key=lambda x: x.SORT_ORDER)
        
        for item in top:
            btn = QPushButton(item.LABEL)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c3e50;
                    color: white;
                    border: none;
                    padding: 8px;
                    text-align: left;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #34495e; }
            """)
            
            if item.TYPE.value == 'SUBMENU':
                menu = self._create_menu_recursive(items, item.GUID)
                btn.setMenu(menu)
            else:
                btn.clicked.connect(lambda checked=False, g=item.GUID: self._on_click(g))
            
            layout.addWidget(btn)
        
        layout.addStretch()
        logger.info(f"Vertikal-Menue erstellt: {len(top)} Buttons")
    
    def _create_horizontal(self, items):
        """Erstellt Horizontal-Menue"""
        logger.info(f"Erstelle Horizontal-Menue ({len(items)} Items)")
        
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
        
        top = [i for i in items if i.PARENT_GUID is None and i.VISIBLE]
        top.sort(key=lambda x: x.SORT_ORDER)
        
        for item in top:
            logger.info(f"  Horizontal Item: {item.LABEL} ({item.TYPE.value})")
            
            if item.TYPE.value == 'SUBMENU':
                menu = self._create_menu_recursive(items, item.GUID)
                action = menubar.addMenu(menu)
                action.setText(item.LABEL)
            else:
                action = menubar.addAction(item.LABEL)
                action.triggered.connect(lambda checked=False, g=item.GUID: self._on_click(g))
        
        layout = self.grund_container.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            layout = QVBoxLayout(self.grund_container)
            layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(menubar)
        self.grund_container.updateGeometry()
        menubar.show()
        
        logger.info(f"Horizontal-Menue erstellt: {len(top)} Eintraege")
    
    def _create_menu_recursive(self, all_items, parent_guid):
        """EINE Methode - rekursiv fuer alle Ebenen"""
        menu = QMenu()
        
        children = [i for i in all_items if i.PARENT_GUID == parent_guid and i.VISIBLE]
        children.sort(key=lambda x: x.SORT_ORDER)
        
        for child in children:
            if child.TYPE.value == 'SEPARATOR':
                menu.addSeparator()
            elif child.TYPE.value == 'SUBMENU':
                submenu = self._create_menu_recursive(all_items, child.GUID)
                sub_action = menu.addMenu(submenu)
                sub_action.setText(child.LABEL)
            else:
                action = QAction(child.LABEL, menu)
                action.triggered.connect(lambda checked=False, g=child.GUID: self._on_click(g))
                menu.addAction(action)
        
        return menu
    
    def _on_click(self, item_guid):
        """Handler fuer Item-Klick"""
        try:
            logger.info(f"Item geklickt: {item_guid}")
            
            item = self.current_container.get_item_by_guid(item_guid)
            if not item:
                logger.warning(f"Item nicht gefunden: {item_guid}")
                return
            
            if item.COMMAND_GUID:
                command = self.current_container.get_command_by_guid(item.COMMAND_GUID)
                if command:
                    logger.info(f"Fuehre Command aus: {command.HANDLER}")
                    self.command_handler.execute_command(command.HANDLER, command.PARAMS)
            
        except Exception as e:
            logger.error(f"Fehler bei Click: {e}", exc_info=True)
    
    def _clear_all(self):
        """Leert alle Container"""
        for container in [self.vertical_container, self.grund_container, self.zusatz_container]:
            if container.layout():
                while container.layout().count():
                    child = container.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()


# Kompatibilitaet
V2MenuHandler = PdvmMenuHandler
V3MenuHandler = PdvmMenuHandler
