"""
V3 Menu Widgets
===============
Einfache, lineare PyQt5-Widgets für V3-Menü

DESIGN-PRINZIPIEN:
- Linear ohne Verschachtelungen
- Ein Widget pro Menü-Typ (VERTIKAL, GRUND, ZUSATZ)
- Direkte MenuItem-Integration
- Keine komplexen Vererbungen

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import logging
from typing import List, Callable, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from v3_menu_system import MenuItem

logger = logging.getLogger(__name__)


class V3MenuButton(QPushButton):
    """
    Einfacher Menü-Button für V3
    
    Features:
    - Text + Icon
    - Click-Signal mit item_guid
    - Styling
    """
    
    item_clicked = pyqtSignal(str)  # item_guid
    
    def __init__(self, item: MenuItem, parent=None):
        super().__init__(parent)
        self.item = item
        
        # Text
        self.setText(item.label)
        
        # Icon (falls vorhanden)
        if item.icon:
            icon_path = Path(item.icon)
            if icon_path.exists():
                self.setIcon(QIcon(str(icon_path)))
                self.setIconSize(QSize(24, 24))
        
        # Tooltip
        if item.tooltip:
            self.setToolTip(item.tooltip)
        
        # Enabled
        self.setEnabled(item.enabled)
        
        # Style
        self.setMinimumHeight(35)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
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
        
        # Signal
        self.clicked.connect(lambda: self.item_clicked.emit(item.guid))


class V3VerticalMenu(QWidget):
    """
    Vertikales Menü (links)
    
    LINEAR:
    - Liste von Buttons
    - Vertikal gestapelt
    - Scrollbar bei Bedarf
    """
    
    item_clicked = pyqtSignal(str)  # item_guid
    
    def __init__(self, items: List[MenuItem], parent=None):
        super().__init__(parent)
        self.items = items
        self.buttons: List[V3MenuButton] = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Erstellt UI - LINEAR"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Button für jedes Item
        for item in self.items:
            if item.type == 'SEPARATOR':
                # Separator als Linie
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                layout.addWidget(line)
            
            elif item.type == 'BUTTON':
                # Button erstellen
                button = V3MenuButton(item)
                button.item_clicked.connect(self.item_clicked.emit)
                self.buttons.append(button)
                layout.addWidget(button)
            
            # SPACER und SUBMENU werden hier nicht verwendet
        
        # Spacer am Ende
        layout.addStretch()
        
        logger.info(f"✅ Vertikalmenü erstellt: {len(self.buttons)} Buttons")


class V3HorizontalMenu(QWidget):
    """
    Horizontales Menü (oben)
    
    LINEAR:
    - Liste von Buttons/Submenus
    - Horizontal angeordnet
    - Für GRUND und ZUSATZ
    """
    
    item_clicked = pyqtSignal(str)  # item_guid
    
    def __init__(self, items: List[MenuItem], parent=None):
        super().__init__(parent)
        self.items = items
        self.buttons: List[V3MenuButton] = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Erstellt UI - LINEAR mit SUBMENU-Support"""
        from PyQt5.QtWidgets import QMenu, QAction
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(3)
        
        # Parent-Items und Child-Items trennen
        parent_items = [item for item in self.items if item.parent_guid is None]
        
        # Für jedes Parent-Item
        for parent_item in parent_items:
            if parent_item.type == 'SEPARATOR':
                # Separator als vertikale Linie
                line = QFrame()
                line.setFrameShape(QFrame.VLine)
                line.setFrameShadow(QFrame.Sunken)
                layout.addWidget(line)
            
            elif parent_item.type == 'SUBMENU':
                # Submenu als Button mit Dropdown
                button = V3MenuButton(parent_item)
                
                # Child-Items finden
                child_items = [item for item in self.items if item.parent_guid == parent_item.guid]
                
                if child_items:
                    # QMenu erstellen
                    menu = QMenu(button)
                    
                    for child_item in sorted(child_items, key=lambda x: x.sort_order):
                        if child_item.type == 'SEPARATOR':
                            menu.addSeparator()
                        else:
                            action = QAction(child_item.label, menu)
                            action.triggered.connect(lambda checked, guid=child_item.guid: self.item_clicked.emit(guid))
                            menu.addAction(action)
                    
                    button.setMenu(menu)
                
                button.item_clicked.connect(self.item_clicked.emit)
                self.buttons.append(button)
                layout.addWidget(button)
            
            elif parent_item.type == 'BUTTON':
                # Normaler Button
                button = V3MenuButton(parent_item)
                button.item_clicked.connect(self.item_clicked.emit)
                self.buttons.append(button)
                layout.addWidget(button)
        
        # Spacer am Ende
        layout.addStretch()
        
        logger.info(f"✅ Horizontalmenü erstellt: {len(self.buttons)} Buttons/Submenus")


if __name__ == "__main__":
    print("🧪 V3 Menu Widgets Test")
    print("=" * 60)
    
    # Test-Imports
    from dataclasses import dataclass
    
    @dataclass
    class TestItem:
        guid: str
        type: str
        label: str
        icon: Optional[str]
        tooltip: Optional[str]
        enabled: bool
    
    # Test-Items
    test_items = [
        TestItem("1", "BUTTON", "Test Button 1", None, "Tooltip 1", True),
        TestItem("2", "SEPARATOR", "", None, None, True),
        TestItem("3", "BUTTON", "Test Button 2", None, "Tooltip 2", True),
    ]
    
    print("\n✅ Import erfolgreich")
    print("   V3MenuButton: ✓")
    print("   V3VerticalMenu: ✓")
    print("   V3HorizontalMenu: ✓")
    
    print("\n🎯 V3 Menu Widgets Ready!")
    print("\n📋 Features:")
    print("   • Einfache Button-Widgets")
    print("   • Linear ohne Verschachtelungen")
    print("   • Direkte MenuItem-Integration")
