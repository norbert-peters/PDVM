"""
PDVM Menu System - Autonomes Menu-Verwaltungs-System V3

ARCHITEKTUR V3 - EINHEITLICHES BUTTON-MENÜ-SYSTEM:
- EINE Render-Methode für beide Richtungen (vertikal/horizontal)
- Root-Items: vertikal=untereinander, horizontal=nebeneinander
- Root-Label: ERSTE 4 BUCHSTABEN anzeigen
- Submenu-Items: Initial zugeklappt, klappbar mit Einrückung
- Hierarchie: Rekursiv mit Einrückung (indent_level * 20px)

VERWENDUNG:
    from pdvm_menu_system_autonomous import PdvmMenuSystemAutonomous
    
    # Container in GCS registrieren (macht Systemstart)
    gcs.register_menu_containers(
        vertical=vertical_menu_container,
        grund=grund_menu_container,
        zusatz=zusatz_menu_container
    )
    
    # Autonomes Menü-Laden
    PdvmMenuSystemAutonomous.load_startmenu(startmenu_guid)
"""

import logging
from pdvm_menu_system import PdvmMenuLoader
from pdvm_menu_pipeline import get_menu_pipeline

logger = logging.getLogger(__name__)


class PdvmMenuSystemAutonomous:
    """
    Autonomes Menü-System V3 - rendert VERTIKAL/GRUND/ZUSATZ einheitlich.
    
    Container-Referenzen werden aus GCS geholt (vom Systemstart registriert).
    """
    
    @staticmethod
    def load_startmenu(startmenu_guid, menu_handler=None):
        """
        Lädt Startmenü autonom in Container.
        
        Args:
            startmenu_guid: GUID des Startmenüs aus sys_menudaten
            menu_handler: Optional - Menu-Handler für Command-Execution
            
        Returns:
            None (Menüs werden direkt in Container gerendert)
        """
        logger.info(f"🚀 PdvmMenuSystemAutonomous.load_startmenu({startmenu_guid})...")
        
        # GCS holen (autonom!)
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar - kann Menüs nicht laden")
            return
        
        # Container-Referenzen aus GCS holen
        if not hasattr(gcs, '_menu_containers'):
            logger.error("❌ Menu-Container nicht in GCS registriert!")
            logger.error("   Systemstart muss gcs.register_menu_containers() aufrufen!")
            return
        
        containers = gcs._menu_containers
        vertical_container = containers.get('vertical')
        grund_container = containers.get('grund')
        zusatz_container = containers.get('zusatz')  # Kann None sein
        
        if not all([vertical_container, grund_container]):  # ZUSATZ optional!
            logger.error("❌ Nicht alle Menu-Container registriert!")
            return
        
        logger.info("✅ Alle Menu-Container gefunden")
        
        # Menü-Gruppen laden (nur wenn Container vorhanden)
        menu_groups = {
            'VERTIKAL': vertical_container,
            'GRUND': grund_container,
        }
        
        if zusatz_container:
            menu_groups['ZUSATZ'] = zusatz_container
            logger.info("  🔧 ZUSATZ-Container verfügbar")
        else:
            logger.warning("  ⚠️ ZUSATZ-Container nicht registriert (übersprungen)")
        
        for gruppe, container in menu_groups.items():
            try:
                logger.info(f"🎯 Lade Menü: {gruppe}")
                
                # Pipeline holen/erstellen (menu_db aus GCS!)
                pipeline = get_menu_pipeline(gruppe, gcs._menu_system_db)
                pipeline.run('BASIS')  # Basis-Daten laden
                
                # Projektierte Matrix holen
                matrix, _ = pipeline.get_projected_data()
                
                if not matrix:
                    logger.warning(f"⚠️ Keine Menü-Daten für {gruppe}")
                    continue
                
                logger.info(f"✅ Menü '{gruppe}' geladen: {len(matrix)} Items")
                
                # 🎯 RENDERING-STRATEGIE AUS PIPELINE (META-gesteuert!)
                rendering_mode = pipeline.rendering_mode
                logger.info(f"  🎯 Rendering-Mode: {rendering_mode}")
                
                # Richtung bestimmen: vert = vertikal, hori_1/hori_2 = horizontal
                direction = 'vertical' if rendering_mode == 'vert' else 'horizontal'
                
                # Einheitliches Button-Menü rendern
                logger.info(f"  🔧 Rendere {gruppe} als {direction.upper()} Button-Menü")
                PdvmMenuSystemAutonomous._render_unified_button_menu(
                    matrix, container, direction, menu_handler
                )
                
                logger.info(f"✅ Menü '{gruppe}' gerendert")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden von {gruppe}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info("✅ Alle System-Menüs geladen")
    
    @staticmethod
    def _render_unified_button_menu(matrix, container, direction, menu_handler):
        """
        EINHEITLICHES BUTTON-MENÜ-SYSTEM für beide Richtungen.
        
        Args:
            matrix: Menu-Daten (projektierte Matrix)
            container: QFrame Container zum Rendern
            direction: 'vertical' oder 'horizontal'
            menu_handler: Menu-Handler für Command-Execution
            
        Verhalten:
            - Root-Items: vertikal=untereinander, horizontal=nebeneinander
            - Root-Label: ERSTE 4 BUCHSTABEN anzeigen
            - Submenu-Items: Initial zugeklappt, klappbar mit Einrückung
            - Hierarchie: Rekursiv mit Einrückung (indent_level * 20px)
        """
        from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QFrame
        from PyQt5.QtCore import Qt
        
        logger.info(f"🔧 Rendering unified button menu ({direction})...")
        
        # Layout holen oder erstellen
        layout = container.layout()
        if layout is None:
            logger.info("  📦 Erstelle neues Layout für Container")
            if direction == 'vertical':
                layout = QVBoxLayout(container)
            else:
                layout = QHBoxLayout(container)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)
        else:
            # Altes Layout clearen
            logger.info("  ♻️ Cleane existierendes Layout")
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        # Container-Widget für Menü-Items
        menu_widget = QFrame()
        if direction == 'vertical':
            menu_layout = QVBoxLayout(menu_widget)
        else:
            menu_layout = QHBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(5)
        
        # Root-Items finden (parent_guid = None)
        root_items = [item for item in matrix if item.get('parent_guid') is None]
        root_items.sort(key=lambda x: x.get('sort_order', 0))
        
        # Expandable State für Submenus (GUID → expanded Bool)
        expanded_state = {}
        
        # Root-Items rendern
        for root_item in root_items:
            item_type = root_item.get('type', 'BUTTON')
            label = root_item.get('label', 'Menu')
            guid = root_item.get('guid')
            
            if item_type == 'SUBMENU':
                # Root-Submenu-Button (mit Popup)
                btn = QPushButton(f"▶ {label}")
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 10px 15px;
                        background-color: #34495e;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 13px;
                        font-weight: bold;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #3498db;
                    }
                    QPushButton:pressed {
                        background-color: #2980b9;
                    }
                """)
                
                # Toggle-Funktion für Popup-Menü (REKURSIV für alle Ebenen!)
                def show_submenu_popup(checked=False, parent_widget=btn, matrix=matrix, guid=guid, handler=menu_handler, label=label):
                    from PyQt5.QtWidgets import QMenu, QAction
                    from PyQt5.QtCore import QPoint
                    
                    # QMenu erstellen (Popup vor Rest der Oberfläche)
                    popup_menu = QMenu(parent_widget)
                    popup_menu.setStyleSheet("""
                        QMenu {
                            background-color: white;
                            border: 2px solid #34495e;
                            padding: 5px;
                        }
                        QMenu::item {
                            padding: 8px 30px;
                            color: #2c3e50;
                            font-size: 12px;
                            background-color: transparent;
                        }
                        QMenu::item:selected {
                            background-color: #3498db;
                            color: white;
                            border-radius: 3px;
                        }
                        QMenu::separator {
                            height: 1px;
                            background-color: #bdc3c7;
                            margin: 5px 10px;
                        }
                    """)
                    
                    # REKURSIVE Funktion zum Hinzufügen aller Ebenen
                    def add_menu_items_recursive(parent_menu, parent_guid):
                        """Fügt alle Kinder rekursiv zum Menü hinzu"""
                        children = [item for item in matrix if item.get('parent_guid') == parent_guid]
                        children.sort(key=lambda x: x.get('sort_order', 0))
                        
                        for child in children:
                            child_type = child.get('type', 'BUTTON')
                            child_label = child.get('label', 'Item')
                            child_guid = child.get('guid')
                            
                            if child_type == 'SUBMENU':
                                # Submenu → Rekursiv weitere Ebene hinzufügen
                                submenu = parent_menu.addMenu(child_label)
                                submenu.setStyleSheet(parent_menu.styleSheet())  # Gleicher Style
                                add_menu_items_recursive(submenu, child_guid)  # REKURSION!
                                logger.debug(f"    📁 Submenu '{child_label}' hinzugefügt (rekursiv)")
                            elif child_type == 'BUTTON':
                                # Button → Action hinzufügen
                                action = QAction(child_label, parent_menu)
                                command = child.get('command')
                                if command and handler:
                                    action.triggered.connect(
                                        lambda checked=False, cmd=command: handler.execute_command(cmd)
                                    )
                                parent_menu.addAction(action)
                            elif child_type == 'SEPARATOR':
                                parent_menu.addSeparator()
                            elif child_type == 'SPACER':
                                # Spacer ignorieren (nur im Editor sichtbar)
                                pass
                    
                    # Rekursiv alle Ebenen hinzufügen
                    add_menu_items_recursive(popup_menu, guid)
                    
                    # Popup unter dem Button anzeigen
                    button_pos = parent_widget.mapToGlobal(QPoint(0, parent_widget.height()))
                    popup_menu.exec_(button_pos)
                
                btn.clicked.connect(show_submenu_popup)
                
                # Zu Layout hinzufügen
                menu_layout.addWidget(btn)
                logger.info(f"  ✅ Root-Submenu '{label}' hinzugefügt (Popup)")
                
            elif item_type == 'BUTTON':
                # Root-Button (ohne Submenu)
                btn = QPushButton(label)
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 10px 15px;
                        background-color: #2c3e50;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #34495e;
                    }
                    QPushButton:pressed {
                        background-color: #1abc9c;
                    }
                """)
                command = root_item.get('command')
                if command and menu_handler:
                    btn.clicked.connect(
                        lambda checked=False, cmd=command: menu_handler.execute_command(cmd)
                    )
                menu_layout.addWidget(btn)
                logger.info(f"  ✅ Root-Button '{label}' hinzugefügt")
        
        # Spacer am Ende (nur bei vertikal)
        if direction == 'vertical':
            menu_layout.addStretch()
        
        layout.addWidget(menu_widget)
        logger.info(f"✅ Unified button menu gerendert: {len(root_items)} Root-Items ({direction})")

