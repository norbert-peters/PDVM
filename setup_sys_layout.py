"""
System-Setup: Erstellt sys_layout Tabelle

Wird aus dem PDVM-System heraus aufgerufen (z.B. über Menü).
GCS ist dann bereits initialisiert.

AUTOR: Norbert Peters  
DATUM: 28.11.2025
"""

import logging

logger = logging.getLogger(__name__)


def setup_sys_layout():
    """
    Erstellt sys_layout Tabelle mit Template und Default.
    
    WICHTIG: Muss aus laufender Anwendung aufgerufen werden (GCS muss existieren)!
    """
    logger.info("🎨 === SYS_LAYOUT SETUP START ===")
    
    try:
        # Import hier, damit GCS bereits initialisiert ist
        from create_sys_layout_table import create_sys_layout_table
        
        success = create_sys_layout_table()
        
        if success:
            logger.info("✅ === SYS_LAYOUT SETUP ERFOLGREICH ===")
            return True
        else:
            logger.error("❌ === SYS_LAYOUT SETUP FEHLGESCHLAGEN ===")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Setup: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    # Standalone-Test (funktioniert nur wenn GCS läuft)
    from pdvm_central_systemsteuerung import get_gcs
    
    gcs = get_gcs()
    if not gcs:
        print("❌ GCS nicht verfügbar - Skript muss aus laufender Anwendung aufgerufen werden!")
    else:
        print(f"✅ GCS verfügbar: User={gcs.user_guid}")
        success = setup_sys_layout()
        if success:
            print("✅ Setup erfolgreich!")
        else:
            print("❌ Setup fehlgeschlagen!")
