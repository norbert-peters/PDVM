"""
PDVM Menu System - Autonomes Menu-Verwaltungs-System V4

ARCHITEKTUR V4 - EINHEITLICHE RENDERING-PIPELINE:
- EINE Pipeline-Funktion für VERTIKAL, GRUND, ZUSATZ
- Holt IMMER Daten aus GCS._menu_system_db
- META definiert Rendering-Mode ('vert', 'hori_1', 'hori_2')
- ULTRA EINFACH: Alle Menüs nutzen dieselbe Rendering-Pipeline

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
from pdvm_menu_rendering_pipeline import render_menu_from_gcs, render_grund_with_zusatz

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
        
        # 🎯 SCHRITT 1: Templates IN GCS expandieren (für alle Gruppen!)
        logger.info("🔧 Expandiere Templates in GCS...")
        for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
            gcs.expand_templates_in_gruppe(gruppe)
        
        # 🎯 SCHRITT 2: Zusatzmenü-GUIDs IN GCS eintragen
        gcs.prepare_menu_with_zusatz()
        
        # 🎯 SCHRITT 3: Aus GCS rendern mit EINHEITLICHER PIPELINE
        logger.info("🎨 Rendere Menüs aus GCS...")
        
        # VERTIKAL rendern
        if vertical_container:
            count = render_menu_from_gcs('VERTIKAL', vertical_container, gcs, menu_handler)
            logger.info(f"✅ VERTIKAL gerendert: {count} Items")
        
        # GRUND rendern (ohne Zusatzmenü beim Start)
        if grund_container:
            count = render_menu_from_gcs('GRUND', grund_container, gcs, menu_handler)
            logger.info(f"✅ GRUND gerendert: {count} Items")
        
        # ZUSATZ-Container bleibt leer (wird bei Button-Klick gefüllt)
        if zusatz_container:
            logger.info("  ℹ️ ZUSATZ-Container bereit (leer beim Start)")
        
        logger.info("✅ Alle System-Menüs geladen")
    
    
    @staticmethod
    def _render_horizontal_menu(gcs, container, active_item_guid, menu_handler):
        """
        Rendert Horizontal-Menü (GRUND + ZUSATZ) mit EINHEITLICHER PIPELINE.
        
        ULTRA EINFACH: Nutzt render_grund_with_zusatz() aus Pipeline!
        
        Args:
            gcs: GCS-Instanz
            container: Horizontal-Container
            active_item_guid: GUID des geklickten VERTIKAL-Items
            menu_handler: Menu-Handler für Commands
        """
        logger.info(f"🔧 Rendere Horizontal-Menü (active_item: {active_item_guid})...")
        
        # EINHEITLICHE PIPELINE nutzen!
        grund_count, zusatz_count = render_grund_with_zusatz(
            container, gcs, active_item_guid, menu_handler
        )
        
        logger.info(f"✅ Horizontal-Menü gerendert: GRUND={grund_count}, ZUSATZ={zusatz_count}")
    
    @staticmethod
    def _render_unified_button_menu(matrix, container, direction, menu_handler, gcs):
        """
        EINHEITLICHES BUTTON-MENÜ-SYSTEM für beide Richtungen.
        
        Args:
            matrix: Menu-Daten (projektierte Matrix)
            container: QFrame Container zum Rendern
            direction: 'vertical' oder 'horizontal'
            menu_handler: Menu-Handler für Command-Execution
            gcs: GCS-Instanz für Zusatzmenü-Zugriff
            
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
                                
                                # LINEARE LOGIK: Button-Klick → Horizontal-Menü neu rendern
                                def button_click_handler(checked=False, cmd=child.get('command'), item_id=child_guid, g=gcs, h=handler):
                                    logger.info(f"🎯 Button geklickt: {child_label} (GUID: {item_id})")
                                    
                                    # Horizontal-Menü NEU RENDERN mit dieser Item-GUID
                                    if hasattr(g, '_menu_containers'):
                                        horizontal_container = g._menu_containers.get('grund')
                                        if horizontal_container:
                                            logger.info(f"  🔧 Rendere Horizontal-Menü neu (active_item: {item_id})")
                                            PdvmMenuSystemAutonomous._render_horizontal_menu(g, horizontal_container, item_id, h)
                                        else:
                                            logger.error("  ❌ GRUND-Container nicht registriert")
                                    
                                    # Command ausführen (falls vorhanden)
                                    if cmd and h:
                                        logger.info(f"  ⚡ Führe Command aus")
                                        h.execute_command(cmd)
                                
                                action.triggered.connect(button_click_handler)
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
                
                # LINEARE LOGIK: Button-Klick → Horizontal-Menü neu rendern
                def button_click_handler(checked=False, cmd=root_item.get('command'), item_id=guid, g=gcs, h=menu_handler):
                    logger.info(f"🎯 Root-Button geklickt: {root_item.get('label')} (GUID: {item_id})")
                    
                    # Horizontal-Menü NEU RENDERN mit dieser Item-GUID
                    if hasattr(g, '_menu_containers'):
                        horizontal_container = g._menu_containers.get('grund')
                        if horizontal_container:
                            logger.info(f"  🔧 Rendere Horizontal-Menü neu (active_item: {item_id})")
                            PdvmMenuSystemAutonomous._render_horizontal_menu(g, horizontal_container, item_id, h)
                        else:
                            logger.error("  ❌ GRUND-Container nicht registriert")
                    
                    # Command ausführen (falls vorhanden)
                    if cmd and h:
                        logger.info(f"  ⚡ Führe Command aus")
                        h.execute_command(cmd)
                
                btn.clicked.connect(button_click_handler)
                menu_layout.addWidget(btn)
                logger.info(f"  ✅ Root-Button '{label}' hinzugefügt")
        
        # Spacer am Ende (nur bei vertikal)
        if direction == 'vertical':
            menu_layout.addStretch()
        
        layout.addWidget(menu_widget)
        logger.info(f"✅ Unified button menu gerendert ({direction})")
    
    @staticmethod
    def render_horizontal_combined(grund_matrix, zusatz_matrix, container, menu_handler, gcs):
        """
        Rendert GRUND + ZUSATZ als einheitliches horizontales Menü.
        
        Alle Buttons haben gleiche Breite (orientiert am längsten Label).
        
        Args:
            grund_matrix: Menu-Matrix für GRUND-Menü
            zusatz_matrix: Menu-Matrix für ZUSATZ-Menü (kann leer sein)
            container: QFrame Container zum Rendern
            menu_handler: Menu-Handler für Command-Execution
            gcs: GCS-Instanz für Zusatzmenü-Mapping
        
        Features:
            - Gleiche Button-Breiten (kein Springen beim Wechsel)
            - GRUND links, Separator, ZUSATZ rechts
            - Nur Root-Items (keine Submenus inline, nur Popup)
        """
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QFrame, QMenu, QAction
        from PyQt5.QtCore import Qt, QPoint
        
        logger.info("🔧 Rendering horizontal combined menu (GRUND + ZUSATZ)...")
        
        # Layout holen oder erstellen
        layout = container.layout()
        if layout is None:
            logger.info("  📦 Erstelle neues Layout für Container")
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
        
        # Container-Widget für gesamtes horizontales Menü
        menu_widget = QFrame()
        menu_layout = QHBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(5)
        
        # === PHASE 1: Längsten Text finden (GRUND + ZUSATZ) ===
        all_labels = []
        
        # GRUND Root-Items
        grund_root_items = [item for item in grund_matrix if item.get('parent_guid') is None]
        grund_root_items.sort(key=lambda x: x.get('sort_order', 0))
        for item in grund_root_items:
            label = item.get('label', '')
            if item.get('type') == 'SUBMENU':
                label = f"▶ {label}"  # Pfeil berücksichtigen
            all_labels.append(label)
        
        # ZUSATZ Root-Items (falls vorhanden)
        zusatz_root_items = []
        if zusatz_matrix:
            zusatz_root_items = [item for item in zusatz_matrix if item.get('parent_guid') is None]
            zusatz_root_items.sort(key=lambda x: x.get('sort_order', 0))
            for item in zusatz_root_items:
                label = item.get('label', '')
                if item.get('type') == 'SUBMENU':
                    label = f"▶ {label}"
                all_labels.append(label)
        
        # Längsten Text ermitteln (mit Font-Metriken)
        from PyQt5.QtGui import QFont, QFontMetrics
        font = QFont("Segoe UI", 13)
        font.setBold(True)
        fm = QFontMetrics(font)
        
        max_width = 0
        for label in all_labels:
            width = fm.horizontalAdvance(label) if hasattr(fm, 'horizontalAdvance') else fm.width(label)
            if width > max_width:
                max_width = width
        
        # Mindestbreite + Padding (15px links + 15px rechts + 10px Reserve)
        button_width = max_width + 40
        logger.info(f"  📏 Button-Breite: {button_width}px (längster Text: {max_width}px)")
        
        # === PHASE 2: GRUND-Buttons rendern ===
        for root_item in grund_root_items:
            item_type = root_item.get('type', 'BUTTON')
            label = root_item.get('label', 'Menu')
            guid = root_item.get('guid')
            
            if item_type == 'SUBMENU':
                # SUBMENU → Popup
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
                
                # Popup-Funktion (wie in _render_unified_button_menu)
                def show_submenu_popup(checked=False, parent_widget=btn, matrix=grund_matrix, guid=guid, handler=menu_handler):
                    popup_menu = QMenu(parent_widget)
                    popup_menu.setStyleSheet("""
                        QMenu {
                            background-color: #2c3e50;
                            color: white;
                            border: 1px solid #34495e;
                        }
                        QMenu::item {
                            padding: 8px 20px;
                        }
                        QMenu::item:selected {
                            background-color: #3498db;
                        }
                    """)
                    
                    # Rekursive Funktion zum Hinzufügen aller Ebenen
                    def add_menu_items_recursive(parent_menu, parent_guid):
                        children = [item for item in matrix if item.get('parent_guid') == parent_guid]
                        children.sort(key=lambda x: x.get('sort_order', 0))
                        
                        for child in children:
                            child_type = child.get('type', 'BUTTON')
                            child_label = child.get('label', 'Item')
                            child_guid = child.get('guid')
                            
                            if child_type == 'SUBMENU':
                                submenu = parent_menu.addMenu(child_label)
                                submenu.setStyleSheet(parent_menu.styleSheet())
                                add_menu_items_recursive(submenu, child_guid)
                            elif child_type == 'BUTTON':
                                action = QAction(child_label, parent_menu)
                                command = child.get('command')
                                if command and handler:
                                    # WICHTIG: item_guid für Zusatzmenü-Wechsel mitgeben!
                                    action.triggered.connect(
                                        lambda checked=False, cmd=command, item_id=child_guid: handler.execute_command_with_zusatz(cmd, item_id)
                                    )
                                parent_menu.addAction(action)
                            elif child_type == 'SEPARATOR':
                                parent_menu.addSeparator()
                    
                    add_menu_items_recursive(popup_menu, guid)
                    button_pos = parent_widget.mapToGlobal(QPoint(0, parent_widget.height()))
                    popup_menu.exec_(button_pos)
                
                btn.clicked.connect(show_submenu_popup)
                
            elif item_type == 'BUTTON':
                # BUTTON → Direkter Klick
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
                    # WICHTIG: item_guid für Zusatzmenü-Wechsel mitgeben!
                    btn.clicked.connect(
                        lambda checked=False, cmd=command, item_id=guid: menu_handler.execute_command_with_zusatz(cmd, item_id)
                    )
            else:
                continue  # SEPARATOR/SPACER überspringen
            
            # Feste Breite setzen
            btn.setFixedWidth(button_width)
            menu_layout.addWidget(btn)
        
        logger.info(f"  ✅ GRUND-Buttons: {len(grund_root_items)}")
        
        # === PHASE 3: Separator (nur wenn ZUSATZ vorhanden) ===
        if zusatz_root_items:
            separator = QFrame()
            separator.setFrameShape(QFrame.VLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #bdc3c7;")
            separator.setFixedWidth(2)
            menu_layout.addWidget(separator)
        
        # === PHASE 4: ZUSATZ-Buttons rendern ===
        for root_item in zusatz_root_items:
            item_type = root_item.get('type', 'BUTTON')
            label = root_item.get('label', 'Menu')
            guid = root_item.get('guid')
            
            if item_type == 'BUTTON':
                btn = QPushButton(label)
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 10px 15px;
                        background-color: #16a085;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: 13px;
                    }
                    QPushButton:hover {
                        background-color: #1abc9c;
                    }
                    QPushButton:pressed {
                        background-color: #0e8c73;
                    }
                """)
                command = root_item.get('command')
                if command and menu_handler:
                    btn.clicked.connect(
                        lambda checked=False, cmd=command: menu_handler.execute_command(cmd)
                    )
                
                btn.setFixedWidth(button_width)
                menu_layout.addWidget(btn)
        
        logger.info(f"  ✅ ZUSATZ-Buttons: {len(zusatz_root_items)}")
        
        # Spacer am Ende
        menu_layout.addStretch()
        
        layout.addWidget(menu_widget)
        logger.info(f"✅ Horizontales kombiniertes Menü gerendert: {len(grund_root_items)} GRUND + {len(zusatz_root_items)} ZUSATZ")


