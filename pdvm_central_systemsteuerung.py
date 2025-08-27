# pdvm_central_systemsteuerung.py
"""
PDVM Zentrale Systemsteuerung - Wrapper für PdvmCentralDatenbank
================================================================

Bietet benutzerfreundliche Properties und Methoden für häufig verwendete
Systemeinstellungen ohne die PdvmCentralDatenbank mit speziellen Features zu überladen.

Architektur:
- Nutzt PdvmCentralDatenbank für Persistierung
- Bietet elegante Properties für häufige Settings
- Hält die Datenbankschicht sauber und generisch
"""

import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmCentralSystemsteuerung:
    """
    Zentrale Systemsteuerung mit eleganten Properties
    
    Wrapper um PdvmCentralDatenbank für benutzerfreundliche Settings-Verwaltung.
    """
    
    def __init__(self, user_guid, db_name="PdvmManager.db"):
        """
        Initialisiert die zentrale Systemsteuerung
        
        Args:
            user_guid (str): GUID des Benutzers
            db_name (str): Name der Datenbank
        """
        self.user_guid = user_guid
        
        # PdvmCentralDatenbank für Persistierung
        self._db = PdvmCentralDatenbank(
            db_name=db_name,
            table_name="systemsteuerung",
            guid=user_guid
        )
        
        logger.info(f"🎛️ CentralSystemsteuerung initialisiert für User: {user_guid}")

        # Sicherstellen, dass ExpertMode immer initialisiert ist
        try:
            expert_mode_data = self._db.get_value(
                gruppe=self.user_guid,
                feld="ExpertMode",
                ab_zeit=None
            )
            if expert_mode_data is None or "wert" not in expert_mode_data:
                logger.info("🔧 Initialisiere ExpertMode für neuen User auf False")
                self._db.set_value(
                    gruppe=self.user_guid,
                    feld="ExpertMode",
                    wert=False,
                    ab_zeit=1001.0
                )
                self._db.save_values()
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Initialisierung von ExpertMode: {e}")

    # =================================================================
    # EXPERT MODE PROPERTY - Elegant und linear
    # =================================================================
    
    @property
    def global_expert_mode(self):
        """
        🎯 ELEGANT: ExpertMode aus Systemsteuerung lesen
        
        Returns:
            bool: True wenn ExpertMode aktiv, sonst False
        """
        try:
            expert_mode_data = self._db.get_value(
                gruppe=self.user_guid,
                feld="ExpertMode",
                ab_zeit=None
            )
            
            if expert_mode_data is None:
                logger.debug("🔧 ExpertMode nicht gesetzt - verwende Standard: False")
                return False
            
            # Wert extrahieren und zu Boolean konvertieren
            wert = expert_mode_data.get("wert", False)
            if isinstance(wert, str):
                result = wert.upper() == "TRUE"
            else:
                result = bool(wert)
            
            logger.debug(f"✅ ExpertMode geladen: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden von ExpertMode: {e}")
            return False

    @global_expert_mode.setter
    def global_expert_mode(self, value):
        """
        🎯 ELEGANT: ExpertMode in Systemsteuerung speichern
        
        Args:
            value (bool): Neuer ExpertMode-Status
        """
        try:
            bool_value = bool(value)
            
            # In Datenbank speichern
            self._db.set_value(
                gruppe=self.user_guid,
                feld="ExpertMode",
                wert=bool_value,
                ab_zeit=1001.0  # Standard-Zeitstempel
            )
            
            # Sofort persistieren
            self._db.save_values()
            
            logger.info(f"✅ ExpertMode gespeichert: {bool_value}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern von ExpertMode: {e}")

    # =================================================================
    # LANGUAGE PROPERTY - Für Vollständigkeit
    # =================================================================
    
    @property
    def language(self):
        """Aktuelle Sprache des Benutzers"""
        try:
            language_data = self._db.get_value(
                gruppe=self.user_guid,
                feld="language",
                ab_zeit=None
            )
            return language_data.get("wert", "DE") if language_data else "DE"
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Sprache: {e}")
            return "DE"

    @language.setter
    def language(self, value):
        """Sprache setzen"""
        try:
            self._db.set_value(
                gruppe=self.user_guid,
                feld="language",
                wert=str(value),
                ab_zeit=1001.0
            )
            self._db.save_values()
            logger.info(f"✅ Sprache gespeichert: {value}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Sprache: {e}")

    # =================================================================
    # GENERISCHE METHODEN - Für spezielle Fälle
    # =================================================================
    
    def get_setting(self, key, default=None):
        """
        Generische Methode zum Lesen eines Settings
        
        Args:
            key (str): Setting-Name
            default: Default-Wert falls Setting nicht existiert
            
        Returns:
            Setting-Wert oder default
        """
        try:
            data = self._db.get_value(
                gruppe=self.user_guid,
                feld=key,
                ab_zeit=None
            )
            return data.get("wert", default) if data else default
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden von Setting '{key}': {e}")
            return default

    def set_setting(self, key, value):
        """
        Generische Methode zum Setzen eines Settings
        
        Args:
            key (str): Setting-Name  
            value: Setting-Wert
        """
        try:
            self._db.set_value(
                gruppe=self.user_guid,
                feld=key,
                wert=value,
                ab_zeit=1001.0
            )
            self._db.save_values()
            logger.debug(f"✅ Setting '{key}' gespeichert: {value}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern von Setting '{key}': {e}")

    # =================================================================
    # DELEGATION AN PdvmCentralDatenbank - Für Kompatibilität
    # =================================================================
    
    def get_value(self, gruppe, feld, ab_zeit=None):
        """Delegiert an PdvmCentralDatenbank"""
        return self._db.get_value(gruppe, feld, ab_zeit)
    
    def set_value(self, gruppe, feld, wert, ab_zeit):
        """Delegiert an PdvmCentralDatenbank"""
        return self._db.set_value(gruppe, feld, wert, ab_zeit)
    
    def save_values(self):
        """Delegiert an PdvmCentralDatenbank"""
        return self._db.save_values()
    
    def lesen(self):
        """Delegiert an PdvmCentralDatenbank"""
        return self._db.lesen()

    # =================================================================
    # DEBUG UND INFO
    # =================================================================
    
    def debug_info(self):
        """Debug-Informationen über die Systemsteuerung"""
        try:
            all_data = self._db.lesen()
            user_data = all_data.get(self.user_guid, {})
            
            info = {
                "user_guid": self.user_guid,
                "expert_mode": self.global_expert_mode,
                "language": self.language,
                "total_settings": len(user_data),
                "available_settings": list(user_data.keys()) if user_data else []
            }
            
            logger.info(f"🔍 DEBUG CentralSystemsteuerung: {info}")
            return info
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Debug: {e}")
            return {"error": str(e)}


# =============================================================================
# GLOBALER INSTANCE MANAGER  
# =============================================================================

# Globale Variable für die PdvmCentralSystemsteuerung Instanz
_global_central_systemsteuerung = None

def get_global_central_systemsteuerung():
    """
    Liefert die globale PdvmCentralSystemsteuerung Instanz
    
    Returns:
        PdvmCentralSystemsteuerung: Die globale Instanz
        
    Raises:
        RuntimeError: Wenn noch nicht initialisiert (Login erforderlich)
    """
    global _global_central_systemsteuerung
    
    if _global_central_systemsteuerung is None:
        raise RuntimeError(
            "❌ Globale Central-Systemsteuerung noch nicht initialisiert! Login erforderlich."
        )
    
    return _global_central_systemsteuerung

def gcs():
    """
    Get Central Systemsteuerung - Eleganter Zugriff auf globale PdvmCentralSystemsteuerung
            # Sofort persistieren (save statt save_values, damit Dirty-Flag korrekt behandelt wird)
            self._db.save()
        PdvmCentralSystemsteuerung: Die globale Instanz
        
    Raises:
        RuntimeError: Wenn noch nicht initialisiert (Login erforderlich)
        
    Usage:
        gcs().global_expert_mode = True
        mode = gcs().global_expert_mode
    """
    return get_global_central_systemsteuerung()
