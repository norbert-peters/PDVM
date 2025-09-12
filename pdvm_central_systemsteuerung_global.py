# pdvm_central_systemsteuerung_global.py
# BRÜCKE ZUR FINALEN GCS - KOMPATIBILITÄTS-LAYER
"""
Kompatibilitäts-Layer für bestehende Module wie pdvm_view_dialog.py.

Leitet alle Aufrufe an die finale GCS weiter, um Kompatibilität zu gewährleisten.
"""

import logging

logger = logging.getLogger(__name__)

def initialize_gcs(user_guid: str):
    """
    Kompatibilitäts-Methode - die finale GCS ist bereits initialisiert.
    
    Args:
        user_guid: GUID des eingeloggten Benutzers (wird ignoriert)
    """
    logger.info(f"🔧 Kompatibilitäts-Init für User: {user_guid} - finale GCS bereits verfügbar")

def get_central_systemsteuerung():
    """
    Gibt die finale GCS zurück für Kompatibilität.
    
    Returns:
        PdvmCentralSystemsteuerung: Die finale GCS-Instanz
    """
    try:
        from pdvm_central_systemsteuerung import get_gcs
        
        finale_gcs = get_gcs()
        if finale_gcs:
            return finale_gcs
        else:
            raise RuntimeError("❌ Finale GCS nicht initialisiert!")
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Zugriff auf finale GCS: {e}")
        raise RuntimeError("❌ Zentrale Systemsteuerung nicht verfügbar!")

def is_initialized():
    """
    Prüft ob die finale GCS initialisiert ist.
    
    Returns:
        bool: True wenn finale GCS verfügbar, False sonst
    """
    try:
        from pdvm_central_systemsteuerung import get_gcs
        
        finale_gcs = get_gcs()
        return finale_gcs is not None and finale_gcs._initialized
        
    except Exception as e:
        logger.debug(f"🔍 GCS-Status-Prüfung: {e}")
        return False

# Alias für direkten Zugriff (wie in pdvm_view_dialog.py verwendet)
# Muss ein Objekt sein, keine Funktion, damit gcs.stichtag funktioniert
class GcsAlias:
    """Alias-Klasse für direkten Zugriff auf finale GCS Properties"""
    
    def __getattr__(self, name):
        finale_gcs = get_central_systemsteuerung()
        return getattr(finale_gcs, name)
    
    def __setattr__(self, name, value):
        finale_gcs = get_central_systemsteuerung()
        return setattr(finale_gcs, name, value)

gcs = GcsAlias()

# Legacy Kompatibilität  
_gcs_instance = None

# LEGACY SUPPORT: Alte Funktionsnamen für Kompatibilität
def initialize_after_login(user_guid: str):
    """
    Legacy-Wrapper für initialize_gcs() - für bestehende MainApp Kompatibilität
    
    Prüft ob bereits initialisiert, wenn ja -> verwendet existierende Instanz
    Wenn nein -> initialisiert neu mit initialize_gcs()
    """
    if is_initialized():
        logger.info(f"🔄 Systemsteuerung bereits initialisiert - verwende existierende Instanz")
        return get_central_systemsteuerung()
    else:
        logger.info(f"🔧 Legacy-Initialisierung für User: {user_guid}")
        return initialize_gcs(user_guid)
