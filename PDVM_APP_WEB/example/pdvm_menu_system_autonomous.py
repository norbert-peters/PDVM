"""
PDVM Menu System - Autonomes Menu-Verwaltungs-System V6

ARCHITEKTUR V6 - KORREKTE IDENTISCHE MENÜ-SYSTEME:
- VERTIKAL und GRUND sind IDENTISCHE Menü-Systeme (nur Richtung unterschiedlich)
- Beide rendern rekursiv beliebig tief (Loop-Sperre bei 50 Ebenen)
- Root-Items: VERTIKAL=vertikal, GRUND=horizontal
- Children: Immer in Popup (QMenu) - rekursiv
- JEDES Element kann zusatz_guid haben → GRUND wird neu gerendert

VERWENDUNG:
    from pdvm_menu_system_autonomous import PdvmMenuSystemAutonomous
    
    # Container in GCS registrieren (macht Systemstart)
    gcs.register_menu_containers(
        vertical=vertical_menu_container,
        grund=grund_menu_container
    )
    
    # Autonomes Menü-Laden
    PdvmMenuSystemAutonomous.load_startmenu(startmenu_guid)
"""

import logging
from pdvm_menu_rendering_pipeline import render_menu, render_grund_with_zusatz

logger = logging.getLogger(__name__)


class PdvmMenuSystemAutonomous:
    """
    Autonomes Menü-System V4 - nutzt EINHEITLICHE RENDERING-PIPELINE.
    
    Container-Referenzen werden aus GCS geholt (vom Systemstart registriert).
    """
    
    @staticmethod
    def load_startmenu(startmenu_guid, menu_handler=None):
        """
        Lädt Startmenü autonom - VERTIKAL und GRUND identisch rendern.
        
        ABLAUF:
        1. Templates in GCS expandieren
        2. Zusatzmenü-GUIDs vorbereiten
        3. VERTIKAL rendern (vertikal, rekursiv)
        4. GRUND rendern (horizontal, rekursiv)
        
        Args:
            startmenu_guid: GUID des Startmenüs aus sys_menudaten
            menu_handler: Optional - Menu-Handler für Command-Execution
        """
        logger.info(f"🚀 PdvmMenuSystemAutonomous.load_startmenu({startmenu_guid})...")
        
        # GCS holen
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar")
            return
        
        # Container-Referenzen aus GCS holen
        if not hasattr(gcs, '_menu_containers'):
            logger.error("❌ Menu-Container nicht in GCS registriert!")
            return
        
        containers = gcs._menu_containers
        vertical_container = containers.get('vertical')
        grund_container = containers.get('grund')
        
        if not all([vertical_container, grund_container]):
            logger.error("❌ Nicht alle Menu-Container registriert!")
            return
        
        logger.info("✅ Alle Menu-Container gefunden")
        
        # SCHRITT 1: Templates IN GCS expandieren
        logger.info("🔧 Expandiere Templates in GCS...")
        for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
            gcs.expand_templates_in_gruppe(gruppe)
        
        # SCHRITT 2: Zusatzmenü-GUIDs IN GCS eintragen
        gcs.prepare_menu_with_zusatz()
        
        # SCHRITT 3: Menüs rendern - IDENTISCH aber unterschiedliche Richtung
        logger.info("🎨 Rendere Menüs...")
        
        # VERTIKAL: Root-Items vertikal, Children in Popup
        vertikal_count = render_menu('VERTIKAL', vertical_container, gcs, menu_handler)
        logger.info(f"✅ VERTIKAL: {vertikal_count} Root-Items (vertikal, rekursiv)")
        
        # GRUND: Root-Items horizontal, Children in Popup
        grund_count = render_menu('GRUND', grund_container, gcs, menu_handler)
        logger.info(f"✅ GRUND: {grund_count} Root-Items (horizontal, rekursiv)")
        
        logger.info("✅ Alle System-Menüs geladen")
    
    @staticmethod
    def _render_horizontal_menu(gcs, container, active_item_guid, menu_handler):
        """
        Rendert Horizontal-Menü (GRUND + ZUSATZ).
        
        WIRD NICHT MEHR GEBRAUCHT - Click-Handler ruft direkt render_grund_with_zusatz() auf!
        Diese Methode bleibt nur für Kompatibilität.
        
        Args:
            gcs: GCS-Instanz
            container: Horizontal-Container
            active_item_guid: GUID des geklickten Items
            menu_handler: Menu-Handler
        """
        logger.info(f"🔧 _render_horizontal_menu (DEPRECATED - nutze render_grund_with_zusatz direkt)")
        render_grund_with_zusatz(container, gcs, active_item_guid, menu_handler)


# Für Kompatibilität: Alte Class-Alias
PdvmMenuSystem = PdvmMenuSystemAutonomous
