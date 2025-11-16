"""
PDVM Menu Rendering Pipeline V6 - KORREKTE ARCHITEKTUR

PRINZIPIEN:
1. ✅ VERTIKAL und GRUND sind IDENTISCHE Menü-Systeme (nur Richtung unterschiedlich)
2. ✅ Beide rendern rekursiv beliebig tief (Loop-Sperre bei 50 Ebenen)
3. ✅ Root-Items: VERTIKAL=vertikal, GRUND=horizontal
4. ✅ Children: Immer in Popup (QMenu) - rekursiv
5. ✅ JEDES Element (VERTIKAL oder GRUND) kann zusatz_guid haben
6. ✅ Klick mit zusatz_guid → GRUND wird neu gerendert als: GRUND + ZUSATZ

VERWENDUNG:
    # Menü rendern (VERTIKAL oder GRUND)
    render_menu('VERTIKAL', container, gcs, menu_handler)
    render_menu('GRUND', container, gcs, menu_handler)
    
    # GRUND mit Zusatz rendern (bei Klick auf Item mit zusatz_guid)
    render_grund_with_zusatz(container, gcs, clicked_item_guid, menu_handler)
"""

import logging
import json
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenu
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

# Loop-Sperre
MAX_RECURSION_DEPTH = 50


def render_menu(gruppe, container, gcs, menu_handler=None):
    """
    Rendert Menü aus GCS-Gruppe.
    
    VERTIKAL: Root-Items vertikal, Children in Popup
    GRUND: Root-Items horizontal, Children in Popup
    
    Args:
        gruppe: 'VERTIKAL' oder 'GRUND'
        container: Qt-Container
        gcs: GCS-Instanz
        menu_handler: Menu-Handler für Commands
    
    Returns:
        int: Anzahl gerenderter Root-Items
    """
    logger.info(f"🎯 render_menu({gruppe})...")
    
    # Daten aus GCS laden
    gruppe_data = gcs._menu_system_db.get_gruppe(gruppe)
    if not gruppe_data:
        logger.warning(f"⚠️ Keine Daten für {gruppe}")
        return 0
    
    # Zu Matrix konvertieren
    matrix = _convert_to_matrix(gruppe_data)
    if not matrix:
        logger.warning(f"⚠️ Keine Items für {gruppe}")
        return 0
    
    logger.info(f"  📊 {len(matrix)} Items aus {gruppe} geladen")
    
    # Richtung bestimmen
    direction = 'vertical' if gruppe == 'VERTIKAL' else 'horizontal'
    
    # Rendern
    root_count = _render_menu_recursive(matrix, container, direction, menu_handler, gcs)
    
    logger.info(f"✅ {gruppe} gerendert: {root_count} Root-Items ({direction})")
    return root_count


def render_grund_with_zusatz(container, gcs, clicked_item_guid, menu_handler=None):
    """
    Rendert GRUND + ZUSATZ kombiniert horizontal.
    
    ABLAUF:
    1. GRUND-Items aus GCS laden
    2. zusatz_guid vom geklickten Item holen (aus VERTIKAL oder GRUND!)
    3. Falls zusatz_guid: ZUSATZ-Children laden
    4. Kombinieren: GRUND + ZUSATZ
    5. Horizontal rendern
    
    Args:
        container: Qt-Container für horizontales Menü
        gcs: GCS-Instanz
        clicked_item_guid: GUID des geklickten Items (aus VERTIKAL oder GRUND)
        menu_handler: Menu-Handler für Commands
    
    Returns:
        tuple: (grund_count, zusatz_count)
    """
    logger.info(f"🎯 render_grund_with_zusatz(clicked_item: {clicked_item_guid})...")
    
    # SCHRITT 1: GRUND laden
    grund_data = gcs._menu_system_db.get_gruppe('GRUND')
    grund_matrix = _convert_to_matrix(grund_data) if grund_data else []
    logger.info(f"  📊 GRUND: {len(grund_matrix)} Items")
    
    # SCHRITT 2: zusatz_guid vom geklickten Item holen
    # Das Item kann in VERTIKAL oder GRUND sein!
    zusatz_guid = _get_zusatz_guid_from_item(gcs, clicked_item_guid)
    
    if zusatz_guid:
        logger.info(f"  📎 zusatz_guid gefunden: {zusatz_guid}")
    else:
        logger.info(f"  ℹ️ Kein zusatz_guid für Item {clicked_item_guid}")
    
    # SCHRITT 3: ZUSATZ laden (falls vorhanden)
    zusatz_matrix = []
    if zusatz_guid:
        zusatz_matrix = gcs.load_zusatzmenu_data(zusatz_guid)
        logger.info(f"  📊 ZUSATZ: {len(zusatz_matrix)} Items")
        
        # KRITISCH: ZUSATZ-Children zu Root-Items machen!
        # Sie haben parent_guid gesetzt (auf ZUSATZ-Root), aber sollen als Root gerendert werden
        zusatz_root_items = []
        for item in zusatz_matrix:
            if item.get('parent_guid') == zusatz_guid:
                # Direktes Child vom ZUSATZ-Root → zu Root machen
                item_copy = item.copy()
                item_copy['parent_guid'] = None
                zusatz_root_items.append(item_copy)
            else:
                # Tiefere Ebene → unverändert lassen
                zusatz_root_items.append(item)
        
        zusatz_matrix = zusatz_root_items
        logger.info(f"  ✅ ZUSATZ-Root-Items vorbereitet")
    
    # SCHRITT 4: Kombinieren
    combined_matrix = grund_matrix + zusatz_matrix
    logger.info(f"  📊 KOMBINIERT: {len(combined_matrix)} Items")
    
    # SCHRITT 5: Horizontal rendern
    _render_menu_recursive(combined_matrix, container, 'horizontal', menu_handler, gcs)
    
    logger.info(f"✅ GRUND+ZUSATZ gerendert ({len(grund_matrix)}+{len(zusatz_matrix)})")
    return (len(grund_matrix), len(zusatz_matrix))


def _convert_to_matrix(gruppe_data):
    """Konvertiert GCS-Gruppendaten zu Matrix."""
    matrix = []
    for guid, item_value in gruppe_data.items():
        try:
            if isinstance(item_value, str):
                item_data = json.loads(item_value)
            else:
                item_data = item_value
            
            if isinstance(item_data, dict):
                item_data['guid'] = guid
                matrix.append(item_data)
        except:
            continue
    
    matrix.sort(key=lambda x: x.get('sort_order', 0))
    return matrix


def _get_zusatz_guid_from_item(gcs, item_guid):
    """
    Holt zusatz_guid vom Item - sucht in VERTIKAL und GRUND.
    
    Args:
        gcs: GCS-Instanz
        item_guid: GUID des Items
    
    Returns:
        str oder None: zusatz_guid des Items
    """
    # Erst in VERTIKAL suchen
    vertikal_data = gcs._menu_system_db.get_gruppe('VERTIKAL')
    if vertikal_data and item_guid in vertikal_data:
        item = vertikal_data[item_guid]
        if isinstance(item, str):
            item = json.loads(item)
        zusatz_guid = item.get('zusatz_guid')
        if zusatz_guid:
            return zusatz_guid
    
    # Dann in GRUND suchen
    grund_data = gcs._menu_system_db.get_gruppe('GRUND')
    if grund_data and item_guid in grund_data:
        item = grund_data[item_guid]
        if isinstance(item, str):
            item = json.loads(item)
        zusatz_guid = item.get('zusatz_guid')
        if zusatz_guid:
            return zusatz_guid
    
    return None


def _render_menu_recursive(matrix, container, direction, menu_handler, gcs):
    """
    Rendert Menü rekursiv mit beliebiger Tiefe.
    
    Root-Items: Nach direction (vertical/horizontal)
    Children: Immer in Popup (QMenu)
    
    Args:
        matrix: Menu-Items (alle Ebenen)
        container: Qt-Container
        direction: 'vertical' oder 'horizontal'
        menu_handler: Menu-Handler
        gcs: GCS-Instanz
    
    Returns:
        int: Anzahl gerenderter Root-Items
    """
    # Layout holen/erstellen
    layout = container.layout()
    
    if not layout:
        if direction == 'vertical':
            layout = QVBoxLayout(container)
        else:
            layout = QHBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
    else:
        # Alte Widgets löschen
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    # Root-Items finden
    root_items = [item for item in matrix if item.get('parent_guid') is None]
    
    # Root-Items rendern
    for item in root_items:
        _render_item(item, matrix, layout, menu_handler, gcs, depth=0)
    
    # Stretch für kompakte Anordnung
    layout.addStretch()
    
    logger.info(f"  ✅ {len(root_items)} Root-Items gerendert")
    return len(root_items)


def _render_item(item, matrix, parent_layout, menu_handler, gcs, depth=0):
    """
    Rendert ein einzelnes Item rekursiv.
    
    Args:
        item: Menu-Item
        matrix: Komplette Matrix (für Children-Suche)
        parent_layout: Parent-Layout
        menu_handler: Menu-Handler
        gcs: GCS-Instanz
        depth: Rekursions-Tiefe (Loop-Sperre)
    """
    # Loop-Sperre
    if depth >= MAX_RECURSION_DEPTH:
        logger.warning(f"⚠️ Max Recursion Depth erreicht: {depth}")
        return
    
    item_type = item.get('type')
    label = item.get('label', 'Unbenannt')
    guid = item.get('guid')
    command = item.get('command')
    zusatz_guid = item.get('zusatz_guid')
    
    # SEPARATOR
    if item_type == 'SEPARATOR' or item_type == 'SPACER':
        # Separator rendern (einfache Linie)
        return
    
    # SUBMENU: Button mit Popup
    if item_type == 'SUBMENU':
        children = [m for m in matrix if m.get('parent_guid') == guid]
        
        # Button erstellen
        button = QPushButton(f"{label} ▼")
        button.setMinimumHeight(35)
        button.setMinimumWidth(100)
        button.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        
        if children:
            # QMenu erstellen
            popup_menu = QMenu(button)
            popup_menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #bdc3c7;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 20px;
                }
                QMenu::item:selected {
                    background-color: #3498db;
                    color: white;
                }
            """)
            
            # Children als Actions hinzufügen (rekursiv!)
            for child in sorted(children, key=lambda x: x.get('sort_order', 0)):
                _add_popup_item(child, matrix, popup_menu, menu_handler, gcs, depth+1)
            
            button.setMenu(popup_menu)
        
        parent_layout.addWidget(button)
        return
    
    # BUTTON: Normaler Button
    if item_type == 'BUTTON':
        button = QPushButton(label)
        button.setMinimumHeight(35)
        button.setMinimumWidth(100)
        button.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6391;
            }
        """)
        
        # Click-Handler: GRUND immer neu rendern (mit/ohne Zusatz)
        def make_handler(item_guid, cmd, zusatz):
            def on_click():
                logger.info(f"🖱️ Button geklickt: {label} (guid={item_guid})")
                
                # 1. GRUND neu rendern (mit Zusatz falls vorhanden, sonst nur GRUND)
                grund_container = gcs.get_container('grund')
                if grund_container:
                    if zusatz:
                        logger.info(f"  🔍 Aktiviere Zusatzmenü: {zusatz}")
                        render_grund_with_zusatz(grund_container, gcs, item_guid, menu_handler)
                    else:
                        logger.info(f"  🔍 Kein Zusatzmenü - nur GRUND rendern")
                        render_menu('GRUND', grund_container, gcs, menu_handler)
                
                # 2. Command ausführen (NACH Menü-Update!)
                if cmd and menu_handler:
                    logger.info(f"  🔍 Führe Command aus: {cmd}")
                    menu_handler.execute_command(cmd)
                
                # Platzhalter
                if not cmd and not zusatz:
                    logger.info(f"  ℹ️ Platzhalter (kein Command/Zusatz)")
            
            return on_click
        
        button.clicked.connect(make_handler(guid, command, zusatz_guid))
        parent_layout.addWidget(button)


def _add_popup_item(item, matrix, popup_menu, menu_handler, gcs, depth):
    """
    Fügt Item zu Popup hinzu (rekursiv für Sub-Submenus).
    
    Args:
        item: Menu-Item
        matrix: Komplette Matrix
        popup_menu: QMenu
        menu_handler: Menu-Handler
        gcs: GCS-Instanz
        depth: Rekursions-Tiefe
    """
    # Loop-Sperre
    if depth >= MAX_RECURSION_DEPTH:
        logger.warning(f"⚠️ Max Recursion Depth in Popup erreicht: {depth}")
        return
    
    item_type = item.get('type')
    label = item.get('label', 'Unbenannt')
    guid = item.get('guid')
    command = item.get('command')
    zusatz_guid = item.get('zusatz_guid')
    
    # SEPARATOR
    if item_type == 'SEPARATOR' or item_type == 'SPACER':
        popup_menu.addSeparator()
        return
    
    # SUBMENU: Rekursiv Sub-Submenu
    if item_type == 'SUBMENU':
        children = [m for m in matrix if m.get('parent_guid') == guid]
        if children:
            sub_menu = popup_menu.addMenu(f"{label} ▶")
            for child in sorted(children, key=lambda x: x.get('sort_order', 0)):
                _add_popup_item(child, matrix, sub_menu, menu_handler, gcs, depth+1)
        return
    
    # BUTTON: Action in Popup
    if item_type == 'BUTTON':
        action = popup_menu.addAction(label)
        
        def make_handler(item_guid, cmd, zusatz, lbl):
            def on_trigger():
                logger.info(f"🖱️ Popup-Item geklickt: {lbl} (guid={item_guid})")
                
                # 1. GRUND neu rendern (mit Zusatz falls vorhanden, sonst nur GRUND)
                grund_container = gcs.get_container('grund')
                if grund_container:
                    if zusatz:
                        logger.info(f"  🔍 Aktiviere Zusatzmenü: {zusatz}")
                        render_grund_with_zusatz(grund_container, gcs, item_guid, menu_handler)
                    else:
                        logger.info(f"  🔍 Kein Zusatzmenü - nur GRUND rendern")
                        render_menu('GRUND', grund_container, gcs, menu_handler)
                
                # 2. Command ausführen (NACH Menü-Update!)
                if cmd and menu_handler:
                    logger.info(f"  🔍 Führe Command aus: {cmd}")
                    menu_handler.execute_command(cmd)
                
                # Platzhalter
                if not cmd and not zusatz:
                    logger.info(f"  ℹ️ Platzhalter (kein Command/Zusatz)")
            
            return on_trigger
        
        action.triggered.connect(make_handler(guid, command, zusatz_guid, label))


# ALIAS für Kompatibilität
render_menu_from_gcs = render_menu
