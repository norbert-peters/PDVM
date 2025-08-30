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
from pdvm_datetime import Pdvm_DateTime, PdvmDateTimeUtils

logger = logging.getLogger(__name__)

class PdvmCentralSystemsteuerung:
    """
    Zentrale Systemsteuerung mit eleganten Properties
    
    Wrapper um PdvmCentralDatenbank für benutzerfreundliche Settings-Verwaltung.
    """
    
    def __init__(self, user_guid, db_name="PdvmManager.db"):
        """
        Initialisiert die zentrale Systemsteuerung für einen Benutzer.
        - Legt immer die Stichtag-Instanz für user_guid an (wird immer benötigt)
        - ExpertMode wird nicht mehr im Init initialisiert, sondern on-demand
        """
        self.user_guid = user_guid
        self._db = PdvmCentralDatenbank(
            db_name=db_name,
            table_name="systemsteuerung",
            guid=user_guid
        )
        logger.info(f"🎛️ CentralSystemsteuerung initialisiert für User: {user_guid}")
        # Stichtag-Instanz immer initialisieren (wird überall benötigt)
        self._init_stichtag_inst()

        # ExpertMode-Konsistenz: Wenn mode != 'admin', setze ExpertMode immer auf False
        mode_data = self._db.get_value(
            gruppe=self.user_guid,
            feld="mode",
            ab_zeit=None
        )
        mode_value = mode_data.get("wert", "user") if mode_data else "user"
        if mode_value != 'admin':
            self._db.set_value(
                gruppe=self.user_guid,
                feld="ExpertMode",
                wert=False,
                ab_zeit=1001.0
            )
            self._db.save_values()
            logger.info("🔒 ExpertMode in Systemsteuerung auf False gesetzt (Init), da mode != 'admin'")

    # =================================================================
    # STICHTAG PROPERTY - Globaler Stichtag für die gesamte Anwendung
    # =================================================================
    def _init_stichtag_inst(self):
        """
        Initialisiert die Stichtag-Instanz für user_guid und legt sie immer an.
        Schützt vor property-Objekten als Wert.
        """
        stichtag_data = self._db.get_value(
            gruppe=self.user_guid,
            feld="stichtag",
            ab_zeit=1001.0
        )
        if stichtag_data is None or stichtag_data.get("wert") is None:
            aktueller_stichtag = PdvmDateTimeUtils.PdvmDateTimeNow
            stichtag_wert = aktueller_stichtag
            self._db.set_value(
                gruppe=self.user_guid,
                feld="stichtag",
                wert=stichtag_wert,
                ab_zeit=1001.0
            )
            self._db.save_values()
            logger.info(f"🔧 Initialisiere Stichtag für neuen User auf {aktueller_stichtag}")
        else:
            stichtag_wert = stichtag_data.get("wert")
        # Schutz: property-Objekte abfangen
        if isinstance(stichtag_wert, property):
            logger.error("Stichtag-Wert ist ein property-Objekt! Setze Default 1001.0.")
            stichtag_wert = 1001.0
        self._global_stichtag_inst = Pdvm_DateTime('DEU')
        self._global_stichtag_inst.PdvmDateTime = stichtag_wert

    @property
    def global_stichtag(self):
        """
        Gibt den aktuellen Stichtag im PdvmFormat (float) zurück.
        Instanz ist garantiert vorhanden (durch __init__).
        """
        return self._global_stichtag_inst.PdvmDateTime

    @property
    def global_stichtag_inst(self):
        """
        Gibt die globale Pdvm_DateTime Instanz zurück (immer vorhanden).
        """
        return self._global_stichtag_inst

    def save_stichtag(self):
        """
        Persistiert den aktuellen Wert der globalen Stichtag-Instanz in der Datenbank.
        Instanz ist garantiert vorhanden. Schützt vor property-Objekten.
        """
        wert = self._global_stichtag_inst.PdvmDateTime
        if isinstance(wert, property):
            logger.error("Stichtag-Wert ist ein property-Objekt beim Speichern! Setze Default 1001.0.")
            wert = 1001.0
        self._db.set_value(
            gruppe=self.user_guid,
            feld="stichtag",
            wert=wert,
            ab_zeit=1001.0
        )
        self._db.save_values()
        logger.info(f"✅ Stichtag gespeichert: {wert}")

    # =================================================================
    # EXPERT MODE PROPERTY - Elegant und linear
    # =================================================================
    
    @property
    def global_expert_mode(self):
        """
        ExpertMode aus Systemsteuerung lesen. Falls nicht vorhanden, wird automatisch auf False gesetzt und zurückgegeben.
        """
        try:
            expert_mode_data = self._db.get_value(
                gruppe=self.user_guid,
                feld="ExpertMode",
                ab_zeit=None
            )
            if expert_mode_data is None or "wert" not in expert_mode_data:
                # Wert anlegen, falls nicht vorhanden
                self._db.set_value(
                    gruppe=self.user_guid,
                    feld="ExpertMode",
                    wert=False,
                    ab_zeit=1001.0
                )
                self._db.save_values()
                logger.debug("🔧 ExpertMode nicht gesetzt - lege False an und gebe False zurück")
                return False
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
        ExpertMode in Systemsteuerung speichern. Legt Wert immer an, falls nicht vorhanden.
        """
        try:
            bool_value = bool(value)
            self._db.set_value(
                gruppe=self.user_guid,
                feld="ExpertMode",
                wert=bool_value,
                ab_zeit=1001.0
            )
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
