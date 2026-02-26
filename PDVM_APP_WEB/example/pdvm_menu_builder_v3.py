"""
PDVM Menu Builder V3
====================
EINFACHE Integration: Matrix → Renderer → UI

Autor: PDVM V2.0
Datum: 08.11.2025
"""

import logging
from typing import Optional, Callable
from PyQt5.QtWidgets import QWidget

from pdvm_menu_storage import get_menu_storage
from pdvm_menu_matrix_builder import MenuMatrixBuilder
from pdvm_menu_renderer import MenuRenderer

logger = logging.getLogger(__name__)


class V3MenuBuilder:
    """
    EINFACHER Menu Builder
    
    WORKFLOW:
    1. Lade Items aus DB (V2MenuStorage)
    2. Baue Matrix (MenuMatrixBuilder)
    3. Rendere UI (MenuRenderer)
    
    FERTIG!
    """
    
    def __init__(self):
        """Initialisiert Builder mit Storage"""
        self.storage = get_menu_storage()
        if not self.storage:
            raise RuntimeError("❌ Menu Storage nicht verfügbar")
        
        logger.info("✅ V3MenuBuilder initialisiert")
    
    def create_vertical_menu(
        self,
        menu_guid: str,
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> Optional[QWidget]:
        """
        Erstellt vertikales Menü (Sidebar links)
        
        Args:
            menu_guid: GUID des Menüs
            on_item_click: Callback(item_guid) bei Klick
            
        Returns:
            QWidget mit vertikalem Menü oder None
        """
        try:
            # 1. Lade Container
            container = self.storage.get_menu(menu_guid)
            if not container:
                logger.warning(f"⚠️ Menü nicht gefunden: {menu_guid}")
                return None
            
            # 2. Baue Matrix
            builder = MenuMatrixBuilder(container.VERTIKAL)
            tree = builder.build_tree()
            
            # 3. Rendere UI
            widget = MenuRenderer.render_vertical(tree, on_item_click)
            
            logger.info(f"✅ Vertikalmenü erstellt: {len(tree)} Top-Level Items")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen Vertikalmenü: {e}", exc_info=True)
            return None
    
    def create_horizontal_menu(
        self,
        menu_guid: str,
        on_item_click: Optional[Callable[[str], None]] = None
    ) -> Optional[QWidget]:
        """
        Erstellt horizontales Menü (Menüleiste oben)
        
        Args:
            menu_guid: GUID des Menüs
            on_item_click: Callback(item_guid) bei Klick
            
        Returns:
            QWidget mit horizontalem Menü oder None
        """
        try:
            # 1. Lade Container
            container = self.storage.get_menu(menu_guid)
            if not container:
                logger.warning(f"⚠️ Menü nicht gefunden: {menu_guid}")
                return None
            
            # 2. Baue Matrix
            builder = MenuMatrixBuilder(container.GRUND)
            tree = builder.build_tree()
            
            # 3. Rendere UI
            widget = MenuRenderer.render_horizontal(tree, on_item_click)
            
            logger.info(f"✅ Horizontales Menü erstellt: {len(tree)} Top-Level Items")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen Horizontalmenü: {e}", exc_info=True)
            return None


# ===== SINGLETON =====
_builder_instance = None

def get_v3_menu_builder() -> V3MenuBuilder:
    """
    Singleton Getter für V3MenuBuilder
    
    Returns:
        V3MenuBuilder Instanz
    """
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = V3MenuBuilder()
    return _builder_instance


# ===== TEST =====
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    import sys
    
    print("🧪 V3 Menu Builder Test")
    print("=" * 60)
    
    # Callback
    def on_click(guid: str):
        print(f"🔘 Clicked: {guid}")
    
    # Qt Application
    app = QApplication(sys.argv)
    
    # Hauptfenster
    window = QMainWindow()
    window.setWindowTitle("V3 Menu Builder Test")
    window.setGeometry(100, 100, 1200, 600)
    
    # Central Widget
    central = QWidget()
    layout = QVBoxLayout(central)
    
    # Builder
    builder = get_v3_menu_builder()
    
    # Test: Lade tatsächliches Menü aus DB
    # HINWEIS: Ersetze mit echter menu_guid aus deiner DB
    test_menu_guid = "54073c2c-0efa-4979-8900-2bd1c53d5014"  # Deine Menu GUID
    
    # Horizontal Menu
    h_menu = builder.create_horizontal_menu(test_menu_guid, on_click)
    if h_menu:
        layout.addWidget(h_menu)
        print("✅ Horizontales Menü geladen")
    else:
        print("❌ Horizontales Menü konnte nicht geladen werden")
    
    # Vertikal Menu
    v_menu = builder.create_vertical_menu(test_menu_guid, on_click)
    if v_menu:
        layout.addWidget(v_menu)
        print("✅ Vertikales Menü geladen")
    else:
        print("❌ Vertikales Menü konnte nicht geladen werden")
    
    layout.addStretch()
    
    window.setCentralWidget(central)
    window.show()
    
    print("=" * 60)
    print("🎯 V3 Builder Test läuft - Fenster anzeigen")
    
    sys.exit(app.exec_())
