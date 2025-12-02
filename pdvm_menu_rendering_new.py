"""
PDVM Menu Rendering - ULTRA EINFACH

LIEST NUR VON GCS UND RENDERT!

KEINE KOMPLIZIERTEN KAPRIOLEN!
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


def render_menu_simple(matrix, container, direction, menu_handler, gcs):
    """
    Ultra-einfaches Rendering.
    
    matrix: Liste von Items aus GCS (bereits sortiert)
    container: QWidget Container
    direction: 'vertical' oder 'horizontal'
    """
    logger.info(f"🎨 Rendere Menü ({direction}, {len(matrix)} Items)...")
    
    # Container clearen
    _clear_container(container)
    
    # Layout erstellen
    if direction == 'vertical':
        layout = QVBoxLayout()
    else:
        layout = QHBoxLayout()
    
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    
    # Root-Items finden (parent_guid=None)
    root_items = [item for item in matrix if item.get('parent_guid') is None]
    
    logger.info(f"  ✅ {len(root_items)} Root-Items gefunden")
    
    # DEBUG: Root-Items anzeigen
    for item in root_items:
        logger.info(f"     - Root: {item.get('label')} (Type={item.get('type')}, GUID={item.get('guid')[:8]}...)")
    
    # Für jeden Root-Item: Button erstellen
    for item in root_items:
        button = _create_menu_button(item, matrix, menu_handler, gcs)
        if button:
            layout.addWidget(button)
        else:
            logger.warning(f"  ⚠️ Kein Button für: {item.get('label')}")
    
    # Spacer am Ende (für schöne Verteilung)
    if direction == 'vertical':
        layout.addStretch()
    else:
        layout.addStretch()
    
    # Layout setzen
    container.setLayout(layout)
    
    logger.info(f"✅ Menü gerendert ({len(root_items)} Root-Buttons)")


def _create_menu_button(item, matrix, menu_handler, gcs):
    """
    Erstellt Button für Menu-Item.
    
    WICHTIG:
    - SUBMENU → IMMER Popup (auch wenn Root!)
    - BUTTON mit Kindern → Popup
    - BUTTON ohne Kinder → Click-Handler
    """
    item_type = item.get('type')
    # DB verwendet 'label', nicht 'caption'!
    caption = item.get('label', item.get('caption', '???'))
    
    # Spacer/Separator überspringen (nur als Separator in Submenü)
    if item_type in ('SPACER', 'SEPARATOR'):
        return None
    
    # Button erstellen
    button = QPushButton(caption)
    button.setMinimumHeight(35)
    button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    
    # Kinder finden (NUR in Matrix, KEIN Zusatzmenü hier!)
    item_guid = item.get('guid')
    children = [child for child in matrix if child.get('parent_guid') == item_guid]
    
    # DEBUG: Zeige Kinder-Info
    logger.info(f"  🔍 Item '{caption}' (Type={item_type}, GUID={item_guid[:8] if item_guid else 'None'}...): {len(children)} Kinder gefunden")
    if children:
        for child in children[:3]:  # Nur erste 3 anzeigen
            logger.info(f"       - Kind: {child.get('label')} (Type={child.get('type')})")
    
    # WICHTIG: SUBMENU hat IMMER Popup (auch wenn Root!)
    has_submenu = (item_type == 'SUBMENU' or len(children) > 0)
    
    if has_submenu:
        # Item hat Submenu → Popup-Menü erstellen
        logger.info(f"  🔽 Item {caption} (Type={item_type}) hat {len(children)} Kinder → Popup-Menü")
        
        # QMenu erstellen mit LESBAREM Styling!
        menu = QMenu(button)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
            }
            QMenu::item {
                background-color: transparent;
                color: black;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QMenu::item:disabled {
                color: #999;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ccc;
                margin: 3px 0px;
            }
        """)
        
        # Kinder sortieren
        children.sort(key=lambda x: x.get('sort_order', 0))
        
        # Actions hinzufügen
        for child in children:
            _add_child_to_menu(child, menu, matrix, menu_handler, gcs)
        
        # Button mit Menü verbinden
        button.setMenu(menu)
    
    else:
        # Kein Submenu → Click-Handler
        zusatz_guid = item.get('zusatz_guid')
        command = item.get('command')
        
        if zusatz_guid:
            # Button hat Zusatzmenü → Bei Click: GRUND+ZUSATZ neu rendern!
            def load_grund_mit_zusatz():
                logger.info(f"🔄 Lade GRUND+ZUSATZ für Button: {caption}")
                logger.info(f"   Zusatz-GUID: {zusatz_guid}")
                # TODO: Menu-Handler soll GRUND+ZUSATZ neu laden!
                # menu_handler.load_grund_with_zusatz(zusatz_guid)
            
            button.clicked.connect(load_grund_mit_zusatz)
        
        elif command and menu_handler:
            # Normaler Command
            button.clicked.connect(lambda: menu_handler.execute_command(command))
    
    return button


def _add_child_to_menu(item, parent_menu, matrix, menu_handler, gcs):
    """Fügt Child zu QMenu hinzu (rekursiv für Submenüs)"""
    item_type = item.get('type')
    caption = item.get('label', item.get('caption', '???'))
    
    # Separator als Trennlinie (SEPARATOR statt SPACER in DB!)
    if item_type in ('SPACER', 'SEPARATOR'):
        parent_menu.addSeparator()
        return
    
    # Kinder finden (NUR in Matrix - KEIN Zusatzmenü in Submenüs!)
    item_guid = item.get('guid')
    children = [child for child in matrix if child.get('parent_guid') == item_guid]
    
    if children:
        # Item hat Kinder → Sub-Menü erstellen
        submenu = parent_menu.addMenu(caption)
        
        # Kinder sortieren
        children.sort(key=lambda x: x.get('sort_order', 0))
        
        # Rekursiv: Kinder hinzufügen
        for child in children:
            _add_child_to_menu(child, submenu, matrix, menu_handler, gcs)
    
    else:
        # Kein Submenu → Action erstellen
        action = QAction(caption, parent_menu)
        
        command = item.get('command')
        if command and menu_handler:
            action.triggered.connect(lambda: menu_handler.execute_command(command))
        
        parent_menu.addAction(action)


def _get_zusatz_children(zusatz_guid, gcs):
    """
    Holt Kinder eines Zusatzmenüs aus GCS.
    
    Zusatzmenü-Struktur:
    - Kopf: SUBMENU mit parent_guid=None, GUID=zusatz_guid (ÜBERSPRINGEN!)
    - Kinder: parent_guid=zusatz_guid (direkte Kinder des Kopfes)
    """
    zusatz_data = gcs._menu_system_db.get_value_by_group('ZUSATZ')
    if not zusatz_data:
        return []
    
    import json
    children = []
    
    # Alle Items mit parent_guid=zusatz_guid
    for guid, item_str in zusatz_data.items():
        try:
            item = json.loads(item_str) if isinstance(item_str, str) else item_str
            
            # Kind wenn parent_guid = zusatz_guid
            # ABER: NICHT der Kopf selbst (guid == zusatz_guid)
            if item.get('parent_guid') == zusatz_guid and guid != zusatz_guid:
                item['guid'] = guid
                children.append(item)
        except:
            pass
    
    return children


def _clear_container(container):
    """Cleart Container vollständig"""
    if container.layout():
        # Altes Layout entfernen
        old_layout = container.layout()
        while old_layout.count():
            child = old_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Layout selbst entfernen
        QWidget().setLayout(old_layout)
