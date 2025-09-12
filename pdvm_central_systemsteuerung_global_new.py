"""
PdvmCentralSystemsteuerungGlobalNew - Neue globale Systemsteuerung
Vereinfachte Architektur mit der neuen Systemsteuerung
"""

import logging
from pdvm_central_systemsteuerung_new import PdvmCentralSystemsteuerungNew

logger = logging.getLogger(__name__)

# =============================================================================
# GLOBALE VARIABLEN
# =============================================================================
_gcs_instance = None
_is_initialized = False

# =============================================================================
# GCS PROXY CLASS für direkten Property-Zugriff
# =============================================================================
class GcsProxyNew:
    """
    Proxy-Objekt für direkten Zugriff auf die globale Systemsteuerung.
    Ermöglicht: gcs.country, gcs.stichtag, gcs.expert_mode, etc.
    """
    
    def __getattr__(self, name):
        """Leitet alle Attribut-Zugriffe an die globale Systemsteuerung weiter"""
        global _gcs_instance
        
        if _gcs_instance is None:
            raise RuntimeError(
                "❌ Globale Systemsteuerung nicht initialisiert! "
                "Rufe initialize_gcs(user_guid) auf."
            )
        
        if hasattr(_gcs_instance, name):
            return getattr(_gcs_instance, name)
        
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """Leitet alle Attribut-Setzungen an die globale Systemsteuerung weiter"""
        global _gcs_instance
        
        if _gcs_instance is None:
            raise RuntimeError(
                "❌ Globale Systemsteuerung nicht initialisiert! "
                "Rufe initialize_gcs(user_guid) auf."
            )
        
        if hasattr(_gcs_instance, name):
            setattr(_gcs_instance, name, value)
        else:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __str__(self):
        """String-Repräsentation"""
        global _gcs_instance
        if _gcs_instance:
            return f"GcsProxyNew({_gcs_instance})"
        return "GcsProxyNew(not initialized)"

# =============================================================================
# GLOBALER PROXY
# =============================================================================
gcs = GcsProxyNew()

# =============================================================================
# INITIALISIERUNG
# =============================================================================
def initialize_gcs(user_guid, user_daten=None):
    """
    Initialisiert die globale Systemsteuerung mit der neuen Architektur.
    
    Args:
        user_guid (str): GUID des eingeloggten Benutzers
        user_daten (dict): Login-Daten des Benutzers (OPTIONAL)
    
    Returns:
        PdvmCentralSystemsteuerungNew: Die initialisierte Systemsteuerung
    """
    global _gcs_instance, _is_initialized
    
    try:
        logger.info(f"🎯 Initialisiere neue globale Systemsteuerung für User: {user_guid}")
        if user_daten:
            logger.info(f"📋 User-Daten werden direkt bei Initialisierung übergeben")
        
        # Erstelle neue Systemsteuerung mit user_daten
        _gcs_instance = PdvmCentralSystemsteuerungNew(user_guid, user_daten)
        _is_initialized = True
        
        logger.info("✅ Neue globale Systemsteuerung erfolgreich initialisiert")
        logger.info(f"📋 Status: {_gcs_instance}")
        
        return _gcs_instance
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Initialisierung der neuen GCS: {e}")
        _gcs_instance = None
        _is_initialized = False
        raise

def is_initialized():
    """Prüft ob die globale Systemsteuerung initialisiert ist"""
    return _is_initialized and _gcs_instance is not None

def get_instance():
    """Gibt die globale Systemsteuerung-Instanz zurück"""
    if not is_initialized():
        raise RuntimeError("❌ Globale Systemsteuerung nicht initialisiert!")
    return _gcs_instance

def reset():
    """Setzt die globale Systemsteuerung zurück (für Tests)"""
    global _gcs_instance, _is_initialized
    _gcs_instance = None
    _is_initialized = False
    logger.info("🔄 Globale Systemsteuerung zurückgesetzt")

# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================
def initialize_after_login():
    """
    Legacy-Wrapper für Kompatibilität mit bestehenden initialize_after_login() Aufrufen.
    
    WICHTIG: Diese Funktion sollte NICHT mehr verwendet werden.
    Verwende stattdessen initialize_gcs(user_guid) direkt.
    """
    logger.warning(
        "⚠️ initialize_after_login() ist deprecated! "
        "Verwende initialize_gcs(user_guid) stattdessen."
    )
    
    if not is_initialized():
        raise RuntimeError(
            "❌ Kann initialize_after_login() nicht ausführen: "
            "Systemsteuerung muss zuerst mit initialize_gcs(user_guid) initialisiert werden!"
        )
