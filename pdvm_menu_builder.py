"""
V2 Menu Builder
===============
Erstellt PyQt5-Widgets aus Menu-Container-Daten

3-Teil-Menü:
- VERTIKAL: Links (vertikale Button-Leiste)
- GRUND: Oben (horizontale Menüleiste)
- ZUSATZ: Oben rechts (dynamisch, kontextabhängig)

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QLabel, QScrollArea, QSizePolicy, QToolButton, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

from pdvm_menu_schema import MenuItem, MenuItemType, MenuContainer
from pdvm_menu_storage import get_menu_storage

logger = logging.getLogger(__name__)


class V2MenuButton(QPushButton):
    """
    Benutzerdefinierter Menü-Button
    
    Features:
    - Icon + Text
    - Tooltip
    - Click-Signal mit item_guid
    - Styling
    """
    
    item_clicked = pyqtSignal(str)  # item_guid
    
    def __init__(self, item: MenuItem, parent=None):
        super().__init__(parent)
        
        self.item = item
        self.item_guid = item.GUID
        
        # Setup
        self._setup_appearance()
        self._setup_signals()
    
    def _setup_appearance(self):
        """Konfiguriert Button-Aussehen"""
        # Text
        self.setText(self.item.LABEL)
        
        # Icon (falls vorhanden)
        if self.item.ICON:
            icon_path = Path(self.item.ICON)
            if icon_path.exists():
                self.setIcon(QIcon(str(icon_path)))
                self.setIconSize(QSize(24, 24))
        
        # Tooltip
        if self.item.TOOLTIP:
            self.setToolTip(self.item.TOOLTIP)
        
        # Enabled/Disabled
        self.setEnabled(self.item.ENABLED)
        
        # Size Policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(35)
        
        # Style
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e8f4ff;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #d0e8ff;
            }
            QPushButton:disabled {
                color: #999;
                background-color: #f5f5f5;
            }
        """)
    
    def _setup_signals(self):
        """Verbindet Signals"""
        self.clicked.connect(lambda: self.item_clicked.emit(self.item_guid))


class V2VerticalMenuWidget(QWidget):
    """
    Vertikales Menü (links)
    
    Features:
    - Scrollbar bei vielen Items
    - Button-Leiste
    - Click-Signal
    """
    
    item_clicked = pyqtSignal(str)  # item_guid
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.buttons: List[V2MenuButton] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Erstellt UI-Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container für Buttons
        container = QWidget()
        self.button_layout = QVBoxLayout(container)
        self.button_layout.setContentsMargins(5, 5, 5, 5)
        self.button_layout.setSpacing(5)
        self.button_layout.addStretch()
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Styling
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f0f0;
            }
        """)
        
        # Fixed Width
        self.setFixedWidth(200)
    
    def set_items(self, items: List[MenuItem]):
        """
        Setzt Menü-Items
        
        Args:
            items: Liste von MenuItem (bereits sortiert)
        """
        # Clear alte Buttons
        self.clear()
        
        # Erstelle neue Buttons
        for item in items:
            if not item.VISIBLE:
                continue
            
            if item.TYPE == MenuItemType.SEPARATOR:
                self._add_separator()
            elif item.TYPE == MenuItemType.SPACER:
                self._add_spacer()
            else:
                self._add_button(item)
        
        logger.info(f"✅ Vertikalmenü: {len(self.buttons)} Buttons erstellt")
    
    def _add_button(self, item: MenuItem):
        """Fügt Button hinzu"""
        button = V2MenuButton(item)
        button.item_clicked.connect(self.item_clicked.emit)
        
        # Füge vor Stretch ein
        self.button_layout.insertWidget(self.button_layout.count() - 1, button)
        self.buttons.append(button)
    
    def _add_separator(self):
        """Fügt Trennlinie hinzu"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ccc;")
        self.button_layout.insertWidget(self.button_layout.count() - 1, line)
    
    def _add_spacer(self):
        """Fügt Abstand hinzu"""
        spacer = QLabel()
        spacer.setFixedHeight(20)
        self.button_layout.insertWidget(self.button_layout.count() - 1, spacer)
    
    def clear(self):
        """Entfernt alle Items"""
        for button in self.buttons:
            button.deleteLater()
        
        # Clear Layout
        while self.button_layout.count() > 1:  # Keep stretch
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.buttons.clear()


class V2HorizontalMenuWidget(QWidget):
    """
    Horizontales Menü (oben)
    
    Für GRUND und ZUSATZ
    
    Features:
    - Menüleiste-Stil
    - Submenüs
    - Click-Signal
    """
    
    item_clicked = pyqtSignal(str)  # item_guid
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.buttons: List[V2MenuButton] = []
        self.submenus: Dict[str, QMenu] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Erstellt UI-Layout"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.layout.addStretch()
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 1px solid #ccc;
            }
        """)
        
        self.setFixedHeight(50)
    
    def set_items(self, items: List[MenuItem], container: Optional[MenuContainer] = None):
        """
        Setzt Menü-Items
        
        Args:
            items: Liste von MenuItem (bereits sortiert)
            container: MenuContainer für Submenü-Lookup
        """
        # Clear alte Buttons
        self.clear()
        
        # Erstelle neue Buttons
        for item in items:
            if not item.VISIBLE:
                continue
            
            if item.TYPE == MenuItemType.SEPARATOR:
                self._add_separator()
            elif item.TYPE == MenuItemType.SPACER:
                self._add_spacer()
            elif item.TYPE == MenuItemType.SUBMENU:
                self._add_submenu_button(item, container)
            else:
                self._add_button(item)
        
        logger.info(f"✅ Horizontalmenü: {len(self.buttons)} Items erstellt")
    
    def _add_button(self, item: MenuItem):
        """Fügt Button hinzu"""
        button = V2MenuButton(item)
        button.item_clicked.connect(self.item_clicked.emit)
        
        # Style für horizontales Menü
        button.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: transparent;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8f4ff;
            }
            QPushButton:pressed {
                background-color: #d0e8ff;
            }
        """)
        
        # Size Policy
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        # Füge vor Stretch ein
        self.layout.insertWidget(self.layout.count() - 1, button)
        self.buttons.append(button)
    
    def _add_submenu_button(self, item: MenuItem, container: Optional[MenuContainer]):
        """Fügt Button mit Submenü hinzu"""
        # Erstelle Tool Button (für Dropdown)
        button = QToolButton()
        button.setText(item.LABEL)
        button.setToolTip(item.TOOLTIP or "")
        button.setPopupMode(QToolButton.InstantPopup)
        
        # Icon
        if item.ICON:
            icon_path = Path(item.ICON)
            if icon_path.exists():
                button.setIcon(QIcon(str(icon_path)))
                button.setIconSize(QSize(24, 24))
        
        # Erstelle Submenü
        submenu = QMenu()
        
        # Hole Child-Items aus Container
        if container:
            child_items = [
                child for child in container.GRUND + container.VERTIKAL
                if child.PARENT_GUID == item.GUID and child.VISIBLE
            ]
            child_items.sort(key=lambda x: x.SORT_ORDER)
            
            for child in child_items:
                action = QAction(child.LABEL, self)
                if child.ICON:
                    icon_path = Path(child.ICON)
                    if icon_path.exists():
                        action.setIcon(QIcon(str(icon_path)))
                
                action.triggered.connect(
                    lambda checked=False, guid=child.GUID: self.item_clicked.emit(guid)
                )
                submenu.addAction(action)
        
        button.setMenu(submenu)
        self.submenus[item.GUID] = submenu
        
        # Style
        button.setStyleSheet("""
            QToolButton {
                text-align: center;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: transparent;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #e8f4ff;
            }
            QToolButton::menu-indicator {
                subcontrol-position: right center;
                subcontrol-origin: padding;
                left: -2px;
            }
        """)
        
        # Füge vor Stretch ein
        self.layout.insertWidget(self.layout.count() - 1, button)
    
    def _add_separator(self):
        """Fügt Trennlinie hinzu"""
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ccc;")
        line.setFixedWidth(2)
        self.layout.insertWidget(self.layout.count() - 1, line)
    
    def _add_spacer(self):
        """Fügt Abstand hinzu"""
        spacer = QLabel()
        spacer.setFixedWidth(20)
        self.layout.insertWidget(self.layout.count() - 1, spacer)
    
    def clear(self):
        """Entfernt alle Items"""
        for button in self.buttons:
            button.deleteLater()
        
        # Clear Layout
        while self.layout.count() > 1:  # Keep stretch
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.buttons.clear()
        self.submenus.clear()


class V2MenuBuilder:
    """
    Menu Builder - Erstellt Widgets aus MenuContainer
    
    Features:
    - build_vertical(): Vertikales Menü
    - build_grund(): Grund-Menü (horizontal)
    - build_zusatz(): Zusatz-Menü (horizontal, mit Vererbung)
    """
    
    def __init__(self):
        """Initialisiert Menu Builder"""
        self.storage = get_menu_storage()
        if not self.storage:
            raise RuntimeError("Menu Storage nicht initialisiert")
        
        logger.info("✅ V2MenuBuilder initialisiert")
    
    def build_vertical(
        self, 
        menu_guid: str,
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> Optional[V2VerticalMenuWidget]:
        """
        Erstellt vertikales Menü-Widget
        
        Args:
            menu_guid: GUID des Menüs
            on_item_click: Callback für Item-Clicks (item_guid)
            
        Returns:
            V2VerticalMenuWidget oder None
        """
        try:
            # Lade Items
            items = self.storage.get_vertical_items(menu_guid)
            if not items:
                logger.warning(f"⚠️ Keine VERTIKAL Items für {menu_guid}")
                return None
            
            # Erstelle Widget
            widget = V2VerticalMenuWidget()
            widget.set_items(items)
            
            # Verbinde Signal
            if on_item_click:
                widget.item_clicked.connect(on_item_click)
            
            logger.info(f"✅ Vertikalmenü erstellt: {len(items)} Items")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen Vertikalmenü: {e}")
            return None
    
    def _get_all_resolved_items(self, grund_items: List[MenuItem]) -> List[MenuItem]:
        """
        Holt ALLE Items nach Template-Auflösung (Top-Level + Children)
        
        Args:
            grund_items: Original GRUND Items aus Container
            
        Returns:
            Liste aller Items nach Template-Auflösung (inkl. Template-Children)
        """
        resolved = []
        
        for item in grund_items:
            # Template-Item erkennen
            is_template = (
                item.TYPE == MenuItemType.SPACER and 
                hasattr(item, 'TEMPLATE_GUID') and 
                item.TEMPLATE_GUID
            )
            
            if is_template:
                # Lade Template-Menü und füge ALLE Items ein
                template_container = self.storage.get_menu(item.TEMPLATE_GUID)
                if template_container:
                    # Füge ALLE Template-Items ein (Top-Level + Children)
                    for template_item in template_container.GRUND:
                        resolved.append(template_item)
                else:
                    logger.warning(f"⚠️ Template nicht gefunden: {item.TEMPLATE_GUID}")
            else:
                # Normales Item
                resolved.append(item)
        
        return resolved
    
    def _resolve_template_items(self, items: List[MenuItem], menu_guid: str) -> List[MenuItem]:
        """
        Löst TEMPLATE-Items auf und merged mit Template-Inhalt
        
        TEMPLATE-Items sind SPACER mit gesetzter TEMPLATE_GUID!
        
        Args:
            items: Liste von MenuItems (kann TEMPLATE-Items enthalten)
            menu_guid: GUID des aktuellen Menüs
        
        Returns:
            Liste von MenuItems mit aufgelösten Templates
        """
        logger.info(f"🔍 _resolve_template_items aufgerufen für Menü {menu_guid[:8]}...")
        logger.info(f"   Eingabe: {len(items)} Items")
        
        resolved = []
        
        for item in items:
            logger.debug(f"   Prüfe Item: {item.LABEL} (TYPE={item.TYPE})")
            # Template-Item erkennen: SPACER mit TEMPLATE_GUID gesetzt
            is_template = (
                item.TYPE == MenuItemType.SPACER and 
                hasattr(item, 'TEMPLATE_GUID') and 
                item.TEMPLATE_GUID
            )
            
            if is_template:
                logger.info(f"   🔗 Template-Item erkannt: {item.TEMPLATE_GUID}")
                # Lade Template-Menü
                template_container = self.storage.get_menu(item.TEMPLATE_GUID)
                if template_container:
                    logger.info(f"🔗 Löse Template auf: {item.TEMPLATE_GUID}")
                    logger.info(f"   Template hat {len(template_container.GRUND)} GRUND Items")
                    
                    # Hole ALLE Template-Items (inkl. Children!)
                    # Wichtig: Template enthält komplette Hierarchie
                    template_items = template_container.GRUND
                    
                    logger.info(f"   Übernehme {len(template_items)} Items aus Template")
                    
                    # Füge Template-Items ein (mit angepasster Sort-Order)
                    for template_item in template_items:
                        # Anpasse Sort-Order basierend auf Template-Item Position
                        adjusted_item = MenuItem(
                            GUID=template_item.GUID,
                            TYPE=template_item.TYPE,
                            LABEL=template_item.LABEL,
                            SORT_ORDER=item.SORT_ORDER + template_item.SORT_ORDER * 0.01,  # Micro-Adjust
                            ICON=template_item.ICON,
                            COMMAND_GUID=template_item.COMMAND_GUID,
                            ZUSATZ_GUID=template_item.ZUSATZ_GUID,
                            PARENT_GUID=template_item.PARENT_GUID,
                            TEMPLATE_GUID=template_item.TEMPLATE_GUID,
                            VISIBLE=template_item.VISIBLE,
                            ENABLED=template_item.ENABLED,
                            TOOLTIP=template_item.TOOLTIP
                        )
                        resolved.append(adjusted_item)
                else:
                    logger.warning(f"⚠️ Template nicht gefunden: {item.TEMPLATE_GUID}")
            else:
                # Normales Item
                resolved.append(item)
        
        # Nach Sort-Order sortieren
        resolved.sort(key=lambda x: x.SORT_ORDER)
        
        logger.info(f"✅ Template-Auflösung abgeschlossen: {len(resolved)} Items")
        return resolved
    
    def build_grund(
        self,
        menu_guid: str,
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> Optional[V2HorizontalMenuWidget]:
        """
        Erstellt Grund-Menü Widget
        
        Args:
            menu_guid: GUID des Menüs
            on_item_click: Callback für Item-Clicks
            
        Returns:
            V2HorizontalMenuWidget oder None
        """
        try:
            # Lade Container (für Submenü-Support)
            container = self.storage.get_menu(menu_guid)
            if not container:
                logger.warning(f"⚠️ Menü {menu_guid} nicht gefunden")
                return None
            
            # Filtere nur Top-Level Items (ohne PARENT_GUID)
            top_level_items = [
                item for item in container.GRUND
                if not item.PARENT_GUID
            ]
            top_level_items.sort(key=lambda x: x.SORT_ORDER)
            
            # ⭐ TEMPLATE-Items auflösen
            resolved_top_level = self._resolve_template_items(top_level_items, menu_guid)
            
            # ⚠️ WICHTIG: Container muss ALLE aufgelösten Items kennen!
            # Erstelle temporären Container mit aufgelösten Items
            resolved_container = MenuContainer(
                MENU_GUID=container.MENU_GUID,
                MENU_NAME=container.MENU_NAME,
                VERTIKAL=container.VERTIKAL,
                GRUND=self._get_all_resolved_items(container.GRUND),  # Alle Items nach Template-Auflösung
                ZUSATZ=container.ZUSATZ,
                COMMANDS=container.COMMANDS,
                IS_STARTMENU=container.IS_STARTMENU
            )
            
            # Erstelle Widget mit aufgelöstem Container
            widget = V2HorizontalMenuWidget()
            widget.set_items(resolved_top_level, resolved_container)
            
            # Verbinde Signal
            if on_item_click:
                widget.item_clicked.connect(on_item_click)
            
            logger.info(f"✅ Grundmenü erstellt: {len(resolved_top_level)} Items")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen Grundmenü: {e}")
            return None
    
    def build_zusatz(
        self,
        menu_guid: str,
        parent_item_guid: str,
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> Optional[V2HorizontalMenuWidget]:
        """
        Erstellt Zusatz-Menü Widget (mit Vererbung)
        
        Args:
            menu_guid: GUID des Menüs
            parent_item_guid: GUID des Parent-Items
            on_item_click: Callback für Item-Clicks
            
        Returns:
            V2HorizontalMenuWidget oder None (None wenn kein Zusatzmenü)
        """
        try:
            # Lade Zusatz-Items (mit Vererbung!)
            items = self.storage.get_zusatz_items(menu_guid, parent_item_guid)
            
            if not items:
                logger.info(f"ℹ️ Kein Zusatzmenü für {parent_item_guid}")
                return None
            
            # Lade Container für Submenü-Support
            container = self.storage.get_menu(menu_guid)
            
            # Erstelle Widget
            widget = V2HorizontalMenuWidget()
            widget.set_items(items, container)
            
            # Verbinde Signal
            if on_item_click:
                widget.item_clicked.connect(on_item_click)
            
            logger.info(f"✅ Zusatzmenü erstellt: {len(items)} Items")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen Zusatzmenü: {e}")
            return None


if __name__ == "__main__":
    # ===== TEST =====
    print("🧪 V2 Menu Builder Test")
    print("=" * 60)
    print("⚠️ HINWEIS: GUI-Test benötigt QApplication")
    print("   Führe v2_main.py aus für vollständigen Test")
    print("=" * 60)
    
    # Teste nur Import
    print("\n✅ Import erfolgreich")
    print("   V2MenuButton: ✓")
    print("   V2VerticalMenuWidget: ✓")
    print("   V2HorizontalMenuWidget: ✓")
    print("   V2MenuBuilder: ✓")
    
    print("\n🎯 Menu Builder Module Ready!")
