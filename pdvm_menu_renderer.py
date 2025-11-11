"""
PDVM Menü Renderer
==================
Rendert MenuNode-Struktur zu Qt-Widgets

KONZEPT:
--------
Input:  MenuNode-Baum (von MenuMatrixBuilder)
Output: Qt-Widget (horizontal/vertikal)

EINFACH: Nur Darstellung, keine Logik!

Autor: PDVM V2.0
Datum: 08.11.2025
"""

import logging
from typing import List, Optional, Callable
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolButton, QPushButton, 
    QMenu, QAction, QFrame, QLabel, QScrollArea
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon

from pdvm_menu_matrix_builder import MenuNode
from pdvm_menu_schema import MenuItemType

logger = logging.getLogger(__name__)


class MenuRenderer:
    """
    Statischer Renderer für Menü-Strukturen
    
    VERWENDUNG:
    -----------
    # Horizontal
    widget = MenuRenderer.render_horizontal(tree, on_click_callback)
    
    # Vertikal
    widget = MenuRenderer.render_vertical(tree, on_click_callback)
    """
    
    @staticmethod
    def render_horizontal(
        tree: List[MenuNode], 
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> QWidget:
        """
        Rendert horizontales Menü (Menü-Leiste oben)
        
        Args:
            tree: MenuNode-Baum (Top-Level Knoten)
            on_item_click: Callback(item_guid) bei Klick
            
        Returns:
            QWidget mit horizontalem Menü
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Rendere jeden Top-Level Knoten
        for node in tree:
            MenuRenderer._add_horizontal_item(node, layout, on_item_click)
        
        # Stretch am Ende
        layout.addStretch()
        
        # Styling
        widget.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #34495e;
                border-radius: 3px;
            }
            QToolButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
        
        widget.setFixedHeight(50)
        
        logger.info(f"✅ Horizontales Menü gerendert: {len(tree)} Top-Level Items")
        return widget
    
    @staticmethod
    def _add_horizontal_item(
        node: MenuNode, 
        layout: QHBoxLayout, 
        on_item_click: Optional[Callable[[str], None]]
    ):
        """Fügt Item zum horizontalen Layout hinzu"""
        item = node.item
        
        if item.TYPE == MenuItemType.SEPARATOR:
            # Trennlinie
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #ccc;")
            line.setFixedWidth(2)
            layout.addWidget(line)
        
        elif item.TYPE == MenuItemType.SPACER:
            # Abstand
            layout.addSpacing(20)
        
        elif item.TYPE == MenuItemType.SUBMENU:
            # Button mit Dropdown
            button = QToolButton()
            button.setText(item.LABEL)
            button.setPopupMode(QToolButton.InstantPopup)
            
            # Icon
            if item.ICON:
                icon_path = Path(item.ICON)
                if icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
            
            # Tooltip
            if item.TOOLTIP:
                button.setToolTip(item.TOOLTIP)
            
            # Menü rekursiv erstellen
            menu = MenuRenderer._create_menu_recursive(node.children, on_item_click)
            button.setMenu(menu)
            
            layout.addWidget(button)
        
        else:
            # Normaler Button
            button = QToolButton()
            button.setText(item.LABEL)
            
            # Icon
            if item.ICON:
                icon_path = Path(item.ICON)
                if icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
            
            # Tooltip
            if item.TOOLTIP:
                button.setToolTip(item.TOOLTIP)
            
            # Click-Signal
            if on_item_click:
                button.clicked.connect(lambda: on_item_click(item.GUID))
            
            layout.addWidget(button)
    
    @staticmethod
    def render_vertical(
        tree: List[MenuNode],
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> QWidget:
        """
        Rendert vertikales Menü (Sidebar links)
        
        Args:
            tree: MenuNode-Baum (Top-Level Knoten)
            on_item_click: Callback(item_guid) bei Klick
            
        Returns:
            QWidget mit vertikalem Menü
        """
        # Hauptwidget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container für Buttons
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Rendere jeden Top-Level Knoten
        for node in tree:
            MenuRenderer._add_vertical_item(node, layout, on_item_click)
        
        # Stretch am Ende
        layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Styling
        main_widget.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 8px;
                text-align: left;
                font-size: 13px;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 16px;
                height: 16px;
            }
        """)
        
        main_widget.setFixedWidth(200)
        
        logger.info(f"✅ Vertikales Menü gerendert: {len(tree)} Top-Level Items")
        return main_widget
    
    @staticmethod
    def _add_vertical_item(
        node: MenuNode,
        layout: QVBoxLayout,
        on_item_click: Optional[Callable[[str], None]]
    ):
        """Fügt Item zum vertikalen Layout hinzu"""
        item = node.item
        
        if item.TYPE == MenuItemType.SEPARATOR:
            # Trennlinie
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("background-color: #ccc;")
            layout.addWidget(line)
        
        elif item.TYPE == MenuItemType.SPACER:
            # Abstand
            spacer = QLabel()
            spacer.setFixedHeight(20)
            layout.addWidget(spacer)
        
        elif item.TYPE == MenuItemType.SUBMENU:
            # Button mit Dropdown
            button = QPushButton(item.LABEL)
            
            # Icon
            if item.ICON:
                icon_path = Path(item.ICON)
                if icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
            
            # Tooltip
            if item.TOOLTIP:
                button.setToolTip(item.TOOLTIP)
            
            # Menü rekursiv erstellen
            menu = MenuRenderer._create_menu_recursive(node.children, on_item_click)
            button.setMenu(menu)
            
            layout.addWidget(button)
        
        else:
            # Normaler Button
            button = QPushButton(item.LABEL)
            
            # Icon
            if item.ICON:
                icon_path = Path(item.ICON)
                if icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
            
            # Tooltip
            if item.TOOLTIP:
                button.setToolTip(item.TOOLTIP)
            
            # Click-Signal
            if on_item_click:
                button.clicked.connect(lambda: on_item_click(item.GUID))
            
            layout.addWidget(button)
    
    @staticmethod
    def _create_menu_recursive(
        children: List[MenuNode],
        on_item_click: Optional[Callable[[str], None]]
    ) -> QMenu:
        """
        Erstellt QMenu rekursiv aus Kindknoten
        
        Args:
            children: Liste von MenuNode (Kindknoten)
            on_item_click: Callback bei Klick
            
        Returns:
            QMenu mit allen Einträgen (rekursiv)
        """
        menu = QMenu()
        
        for node in children:
            item = node.item
            
            if item.TYPE == MenuItemType.SEPARATOR:
                menu.addSeparator()
            
            elif item.TYPE == MenuItemType.SUBMENU:
                # Rekursiv: Unter-Submenü
                submenu = MenuRenderer._create_menu_recursive(node.children, on_item_click)
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
                # Normaler Eintrag
                action = QAction(item.LABEL, menu)
                
                # Icon
                if item.ICON:
                    icon_path = Path(item.ICON)
                    if icon_path.exists():
                        action.setIcon(QIcon(str(icon_path)))
                
                # Tooltip
                if item.TOOLTIP:
                    action.setToolTip(item.TOOLTIP)
                
                # Click-Signal
                if on_item_click:
                    action.triggered.connect(lambda checked=False, guid=item.GUID: on_item_click(guid))
                
                menu.addAction(action)
        
        return menu


# ===== TEST =====
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from pdvm_menu_schema import create_menu_item
    from pdvm_menu_matrix_builder import MenuMatrixBuilder
    import sys
    
    print("🧪 Menu Renderer Test")
    print("=" * 60)
    
    # Test-Daten
    items = [
        create_menu_item("item-1", "Stammdaten", MenuItemType.SUBMENU, 0, PARENT_GUID=None),
        create_menu_item("item-2", "Berichte", MenuItemType.SUBMENU, 1, PARENT_GUID=None),
        create_menu_item("item-3", "Personen", MenuItemType.SUBMENU, 0, PARENT_GUID="item-1"),
        create_menu_item("item-4", "Firmen", MenuItemType.BUTTON, 1, PARENT_GUID="item-1"),
        create_menu_item("item-5", "Alle Personen", MenuItemType.BUTTON, 0, PARENT_GUID="item-3"),
        create_menu_item("item-6", "Neue Person", MenuItemType.BUTTON, 1, PARENT_GUID="item-3"),
        create_menu_item("item-7", "Umsatz", MenuItemType.BUTTON, 0, PARENT_GUID="item-2"),
    ]
    
    # Baue Matrix
    builder = MenuMatrixBuilder(items)
    tree = builder.build_tree()
    
    # Callback
    def on_click(guid: str):
        print(f"🔘 Clicked: {guid}")
    
    # Qt Application
    app = QApplication(sys.argv)
    
    # Test Horizontal
    h_widget = MenuRenderer.render_horizontal(tree, on_click)
    h_widget.setWindowTitle("Horizontal Menü Test")
    h_widget.show()
    
    # Test Vertikal
    v_widget = MenuRenderer.render_vertical(tree, on_click)
    v_widget.setWindowTitle("Vertikal Menü Test")
    v_widget.move(100, 100)
    v_widget.show()
    
    print("✅ Menüs gerendert - Fenster anzeigen")
    print("=" * 60)
    
    sys.exit(app.exec_())
