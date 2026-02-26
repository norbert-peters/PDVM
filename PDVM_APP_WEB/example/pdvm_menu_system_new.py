"""
PDVM Menu System - ULTRA LINEAR & EINFACH

ABLAUF:
1. Menü in GCS laden (no_save)
2. Templates auflösen
3. Zusatzmenüs identifizieren & verknüpfen
4. Rendern (einheitlich für alle)

KEINE KOMPLIZIERTEN KAPRIOLEN!
"""

import logging
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class PdvmMenuSystemNew:
    """Ultra-lineares Menu-System"""
    
    def __init__(self, menu_handler=None):
        self.menu_handler = menu_handler
        self.gcs = get_gcs()
        self.current_menu_guid = None
    
    def set_guid(self, menu_guid):
        """
        Menü-GUID setzen und Pipeline durchlaufen.
        
        Pipeline:
        1. Menü in GCS laden (no_save)
        2. Templates auflösen
        3. Zusatzmenüs identifizieren
        4. zusatz_guid eintragen
        """
        logger.info(f"🚀 Lade Menü: {menu_guid}")
        self.current_menu_guid = menu_guid
        
        # 1. Menü in GCS laden
        self._load_menu_to_gcs(menu_guid)
        
        # 2. Templates auflösen
        self._expand_templates()
        
        # 3. Zusatzmenüs verknüpfen
        self._link_zusatzmenues()
        
        logger.info(f"✅ Menü-Pipeline abgeschlossen: {menu_guid}")
    
    def _load_menu_to_gcs(self, menu_guid):
        """Schritt 1: Menü in GCS laden"""
        logger.info(f"📂 Lade Menü {menu_guid} in GCS...")
        
        # GCS initialisiert menu_system_db mit no_save
        self.gcs.set_menu_system_db_guid(menu_guid)
        
        logger.info(f"✅ Menü in GCS geladen")
    
    def _expand_templates(self):
        """Schritt 2: Templates in Struktur auflösen - NUTZE GCS BOARDMITTEL!"""
        logger.info(f"🔧 Expandiere Templates...")
        
        # GCS hat bereits die Funktion - BOARDMITTEL verwenden!
        for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
            logger.info(f"  🔧 Expandiere Templates in {gruppe}...")
            try:
                self.gcs.expand_templates_in_gruppe(gruppe)
                logger.info(f"    ✅ Templates in {gruppe} expandiert")
            except Exception as e:
                logger.warning(f"    ⚠️ Fehler beim Expandieren in {gruppe}: {e}")
        
        logger.info(f"✅ Templates expanded")
    
    def _link_zusatzmenues(self):
        """
        Schritt 3+4: Zusatzmenüs identifizieren und zusatz_guid eintragen.
        
        Ein Zusatzmenü ist:
        - In ZUSATZ-Gruppe
        - Type='SUBMENU'
        - parent_guid=None (Kopf des Zusatzmenüs)
        
        Key des SUBMENU = key des Menu-Items zu dem es gehört
        """
        logger.info(f"🔗 Verknüpfe Zusatzmenüs...")
        
        # ZUSATZ-Gruppe laden
        zusatz_data = self.gcs._menu_system_db.get_value_by_group('ZUSATZ')
        if not zusatz_data:
            logger.info(f"  ℹ️ Keine Zusatzmenüs vorhanden")
            return
        
        import json
        
        # Zusatzmenü-Köpfe finden (SUBMENU mit parent_guid=None)
        # WICHTIG: GUID des Kopfes = GUID des Menu-Items zu dem es gehört!
        zusatz_heads = []
        for guid, item_str in zusatz_data.items():
            try:
                item = json.loads(item_str) if isinstance(item_str, str) else item_str
                if item.get('type') == 'SUBMENU' and item.get('parent_guid') is None:
                    # GUID selbst ist der Key!
                    zusatz_heads.append((guid, guid))
                    logger.info(f"  📎 Zusatzmenü gefunden: GUID={guid}")
            except:
                pass
        
        if not zusatz_heads:
            logger.info(f"  ℹ️ Keine Zusatzmenü-Köpfe gefunden")
            return
        
        # Für jedes Zusatzmenü: zusatz_guid in allen Kindern eintragen
        for menu_item_key, zusatz_head_guid in zusatz_heads:
            logger.info(f"  🔗 Verknüpfe Zusatzmenü {zusatz_head_guid} mit Item {menu_item_key}")
            
            # Alle Kinder des Zusatzmenüs finden (rekursiv)
            children = self._find_all_children_recursive('ZUSATZ', zusatz_head_guid)
            
            # zusatz_guid in jedem Kind eintragen
            for child_guid in children:
                child_str = zusatz_data.get(child_guid)
                if child_str:
                    child = json.loads(child_str) if isinstance(child_str, str) else child_str
                    child['zusatz_guid'] = zusatz_head_guid
                    self.gcs._menu_system_db.set_value('ZUSATZ', child_guid, json.dumps(child))
            
            logger.info(f"    ✅ zusatz_guid eingetragen in {len(children)} Kinder")
            
            # Zusatzmenü mit Menu-Item verknüpfen (in VERTIKAL/GRUND)
            for gruppe in ['VERTIKAL', 'GRUND']:
                gruppe_data = self.gcs._menu_system_db.get_value_by_group(gruppe)
                if gruppe_data and menu_item_key in gruppe_data:
                    item_str = gruppe_data[menu_item_key]
                    item = json.loads(item_str) if isinstance(item_str, str) else item_str
                    item['zusatz_guid'] = zusatz_head_guid
                    self.gcs._menu_system_db.set_value(gruppe, menu_item_key, json.dumps(item))
                    logger.info(f"    ✅ Zusatzmenü verknüpft mit {gruppe}-Item {menu_item_key}")
        
        logger.info(f"✅ Zusatzmenüs verknüpft")
    
    def _find_all_children_recursive(self, gruppe, parent_guid):
        """Findet alle Kinder rekursiv"""
        gruppe_data = self.gcs._menu_system_db.get_value_by_group(gruppe)
        if not gruppe_data:
            return []
        
        import json
        children = []
        
        for guid, item_str in gruppe_data.items():
            try:
                item = json.loads(item_str) if isinstance(item_str, str) else item_str
                if item.get('parent_guid') == parent_guid:
                    children.append(guid)
                    # Rekursiv: Kinder der Kinder
                    children.extend(self._find_all_children_recursive(gruppe, guid))
            except:
                pass
        
        return children
    
    def render_all(self):
        """Rendert alle Menüs (VERTIKAL + GRUND + Zusatz wenn vorhanden)"""
        logger.info(f"🎨 Rendere alle Menüs...")
        
        # Container aus GCS holen (BOARDMITTEL!)
        vertical_container = self.gcs._menu_containers.get('vertical')
        grund_container = self.gcs._menu_containers.get('grund')
        
        if not vertical_container or not grund_container:
            logger.error("❌ Container nicht gefunden!")
            logger.error(f"   Verfügbare Container: {list(self.gcs._menu_containers.keys())}")
            return
        
        logger.info(f"✅ Container gefunden: vertical={vertical_container}, grund={grund_container}")
        
        # VERTIKAL rendern
        self._render_gruppe('VERTIKAL', vertical_container, 'vertical')
        
        # GRUND rendern (mit Zusatzmenüs)
        self._render_gruppe('GRUND', grund_container, 'horizontal')
        
        logger.info(f"✅ Alle Menüs gerendert")
    
    def _render_gruppe(self, gruppe, container, direction):
        """
        Rendert eine Menü-Gruppe einheitlich.
        
        Wenn ein Item zusatz_guid hat → Zusatzmenü mit rendern
        """
        logger.info(f"🎨 Rendere {gruppe} ({direction})...")
        
        # Matrix aus GCS holen
        from pdvm_menu_rendering_new import render_menu_simple
        
        gruppe_data = self.gcs._menu_system_db.get_value_by_group(gruppe)
        if not gruppe_data:
            logger.warning(f"⚠️ Keine Daten für {gruppe}")
            return
        
        # Zu Matrix konvertieren
        import json
        matrix = []
        for guid, item_str in gruppe_data.items():
            try:
                item = json.loads(item_str) if isinstance(item_str, str) else item_str
                item['guid'] = guid
                matrix.append(item)
            except:
                pass
        
        # Nach sort_order sortieren
        matrix.sort(key=lambda x: x.get('sort_order', 0))
        
        logger.info(f"  ✅ {len(matrix)} Items aus GCS geladen")
        
        # Rendern
        render_menu_simple(matrix, container, direction, self.menu_handler, self.gcs)
        
        logger.info(f"✅ {gruppe} gerendert")


def get_menu_system(menu_handler=None):
    """Singleton"""
    if not hasattr(get_menu_system, '_instance'):
        get_menu_system._instance = PdvmMenuSystemNew(menu_handler)
    return get_menu_system._instance
