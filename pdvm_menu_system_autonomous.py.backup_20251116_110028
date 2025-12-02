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
    Autonomes Menü-System V4 - nutzt EINHEITLICHE RENDERING-PIPELINE.
    
    Container-Referenzen werden aus GCS geholt (vom Systemstart registriert).
    """
    
    @staticmethod
    def load_startmenu(startmenu_guid, menu_handler=None):
        """
        Lädt Startmenü autonom in Container mit EINHEITLICHER PIPELINE.
        
        ULTRA EINFACH:
        1. Templates in GCS expandieren
        2. Zusatzmenü-GUIDs vorbereiten
        3. VERTIKAL, GRUND mit Pipeline rendern
        
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
        
        # 🎯 SCHRITT 1: Templates IN GCS expandieren (für alle Gruppen!)
        logger.info("🔧 Expandiere Templates in GCS...")
        for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
            gcs.expand_templates_in_gruppe(gruppe)
        
        # 🎯 SCHRITT 2: Zusatzmenü-GUIDs IN GCS eintragen
        gcs.prepare_menu_with_zusatz()
        
        # 🎯 SCHRITT 3: Aus GCS rendern mit EINHEITLICHER PIPELINE
        logger.info("🎨 Rendere Menüs aus GCS mit Pipeline...")
        
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


# Für Kompatibilität: Alte Class-Alias
PdvmMenuSystem = PdvmMenuSystemAutonomous
