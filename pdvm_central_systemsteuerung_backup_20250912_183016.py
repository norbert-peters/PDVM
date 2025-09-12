"""
PdvmCentralSystemsteuerung - Zentrale Einstellungsverwaltung mit Properties Pattern
Vereinfachte lineare Architektur für automatische Initialisierung und persistente Speicherung
"""

import logging
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)

# GLOBALE INSTANZEN für zentrale Verwendung
global_stichtag_inst = None  # Zentrale Pdvm_DateTime Instanz für Stichtag


class PdvmCentralSystemsteuerung:
    """
    Zentrale Systemsteuerung mit Properties-Pattern für automatische Wertverwaltung
    Vereinfachte Architektur mit linearer Ausführung und persistenter Speicherung
    """
    
    def __init__(self, user_guid):
        """
        Initialisierung mit verpflichtender user_guid aus Login.
        
        Args:
            user_guid (str): GUID des eingeloggten Benutzers (ERFORDERLICH)
            
        Raises:
            ValueError: Wenn user_guid fehlt oder ungültig ist
        """
#        global global_stiichtag_inst wird nicht mehr so initialisiert
        
        # KRITISCH: Keine Fallbacks! user_guid MUSS vom Login kommen
        if not user_guid:
            raise ValueError(
                "❌ KRITISCHER FEHLER: user_guid ist erforderlich! "
                "Systemsteuerung darf nur nach erfolgreichem Login initialisiert werden."
            )
        
        if not isinstance(user_guid, str) or len(user_guid.strip()) == 0:
            raise ValueError(
                "❌ KRITISCHER FEHLER: user_guid muss ein gültiger String sein! "
                f"Erhalten: {repr(user_guid)}"
            )
        
        self._user_guid = user_guid.strip()
        
        # Datenbank-Verbindung erst NACH user_guid Validierung
        try:
            self._database = PdvmCentralDatenbank(
                table_name="systemsteuerung",
                guid=self._user_guid
            )
        except Exception as e:
            raise RuntimeError(
                f"❌ FEHLER beim Laden der Systemsteuerung für User {self._user_guid}: {e}"
            ) from e
        
#        self._datetime = Pdvm_DateTime() wird nicht mehr so initialisiert
        
        # Globale Stichtag-Instanz hier nicht initialisieren 
#        if global_stichtag_inst is None:
#            global_stichtag_inst = Pdvm_DateTime()
        
        # Properties Werte (werden automatisch geladen)
        self._country = None
        self._stichtag = None
        self._expert_mode = None
        self._mode = None
        self._language = None
        
        # 🎯 NEUE REFRESH-ARCHITEKTUR: Command und first_call Tracking
        self._current_command = None    # Aktueller Menübefehl für Refresh
        self._first_call = True         # Flag für initialen vs. Refresh-Aufruf
        
        # Automatische Initialisierung
        self._initialize_defaults()

        # Globale Stichtag-Instanz auf den geladenen/default Stichtag setzen (über Property)
        global global_stichtag_inst
        global_stichtag_inst = Pdvm_DateTime(self.global_country)
        global_stichtag_inst.PdvmDateTime = self._stichtag

    def _initialize_defaults(self):
        """Lädt gespeicherte Werte oder setzt Standard-Defaults"""
        
        # Standard-Werte falls nichts gespeichert ist
#        current_pdvm_datetime = self._datetime.PdvmDateTimeNow() wird nicht mehr so initialisiert
        
        defaults = {
            'country': 'DEU',
            'stichtag': Pdvm_DateTime("DEU").PdvmDateTimeNow(),  # Float direkt verwenden
            'expert_mode': False,
            'mode': 'user',  # ⚠️ WICHTIG: Default auf 'user' - darf NIEMALS auf 'standard' geändert werden!
            'language': 'de-de'
        }
        
        # Lade gespeicherte Werte oder verwende Defaults
        for key, default_value in defaults.items():
            try:
                # Lade direkt aus der User-GUID-Gruppe (nicht aus "systemsteuerung")
                result = self._database.get_value(self._user_guid, key)
                logging.info(f"🔹 Geladener Wert für {key}: {result}")
                saved_value = result.get("wert") if result else None
                setattr(self, f"_{key}", saved_value if saved_value is not None else default_value)
            except Exception:
                # Fallback auf Default falls Fehler beim Laden
                setattr(self, f"_{key}", default_value)
        
    
    def save_values(self):
        """Speichert alle aktuellen Property-Werte persistent"""
        properties_to_save = ['country', 'stichtag', 'expert_mode', 'mode', 'language']
        
        try:
            for prop in properties_to_save:
                value = getattr(self, f"_{prop}")
                # Speichere in User-GUID-Gruppe (nicht "systemsteuerung")
                self._database.set_value(self._user_guid, prop, value)
            
            # Datenbank-interne Speicherung ausführen
            self._database.save_values()
        except Exception as e:
            print(f"Fehler beim Speichern der Werte: {e}")
    
    def save_stichtag(self):
        """Speichert nur den Stichtag-Wert - für Kompatibilität mit pdvm_systemstart.py"""
        global global_stichtag_inst
        
        try:
            # 🔧 FIX: Hole aktuellen Wert aus globaler Instanz vor dem Speichern
            if global_stichtag_inst is not None:
                current_stichtag_value = global_stichtag_inst.PdvmDateTime
                self._stichtag = current_stichtag_value
                logger.info(f"🔄 Stichtag-Wert aus globaler Instanz synchronisiert: {current_stichtag_value}")
            
            # Speichere aktuellen Stichtag-Wert
            self._database.set_value(self._user_guid, 'stichtag', self._stichtag)
            self._database.save_values()
            logger.info("✅ Stichtag in Datenbank gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Stichtags: {e}")
            print(f"Fehler beim Speichern des Stichtags: {e}")
    
    # GLOBAL_COUNTRY Property
    @property
    def global_country(self):
        """Land/Country Code (AT, DEU, etc.)"""
        return self._country
    
    @global_country.setter
    def global_country(self, value):
        """Setzt Country und speichert automatisch"""
        if value in ['AT', 'DEU', 'CH', 'US', 'UK']:
            self._country = value
            # Bei Country-Änderung auch Pdvm_DateTime neu initialisieren
            self._datetime = Pdvm_DateTime(country=value)
            self.save_values()
        else:
            raise ValueError(f"Ungültiger Country-Code: {value}")
    
    # GLOBAL_STICHTAG Property mit globaler Pdvm_DateTime Instanz
    @property
    def global_stichtag(self):
        """Aktueller Stichtag für Datenabfragen - verwendet globale Pdvm_DateTime Instanz"""
        return self.global_stichtag_inst.PdvmDateTime
    
    @global_stichtag.setter
    def global_stichtag(self, value):
        """Setzt Stichtag und speichert automatisch - synchronisiert globale Instanz"""
        global global_stichtag_inst
        
        self._stichtag = value
        
        # Globale Stichtag-Instanz auf den neuen Wert setzen (über Property)
        global_stichtag_inst.PdvmDateTime = value
        
        self.save_values()
    
    def get_global_stichtag_inst(self):
        """Gibt die globale Pdvm_DateTime Instanz für Stichtag zurück"""
        return global_stichtag_inst
    
    @property
    def global_stichtag_inst(self):
        """Property für Zugriff auf die globale Pdvm_DateTime Instanz"""
        return global_stichtag_inst
    
    @property
    def global_expert_mode(self):
        """Expert Mode für erweiterte Funktionen"""
        return self._expert_mode
    
    @global_expert_mode.setter
    def global_expert_mode(self, value):
        """Setzt Expert Mode und speichert automatisch"""
        self._expert_mode = bool(value)
        self.save_values()
    
    # GLOBAL_MODE Property
    @property
    def global_mode(self):
        """Aktueller Anwendungsmodus"""
        return self._mode
    
    @global_mode.setter
    def global_mode(self, value):
        """Setzt Mode und speichert automatisch"""
        self._mode = value
        self.save_values()
    
    # GLOBAL_LANGUAGE Property
    @property
    def global_language(self):
        """Aktuelle Sprache/Language"""
        return self._language
    
    @global_language.setter
    def global_language(self, value):
        """Setzt Language und speichert automatisch"""
        self._language = value
        self.save_values()
    
    # Utility Methoden
    def is_expert_mode_available(self):
        """Prüft, ob der ExpertMode-Umschalter verfügbar ist (nur bei admin mode)"""
        return self.global_mode == 'admin'
    
    # KURZE PROPERTY-ALIASES für einfachen Zugriff (wie im alten System)
    @property
    def stichtag(self):
        """Kurzer Zugriff auf global_stichtag"""
        return self.global_stichtag
    
    @stichtag.setter
    def stichtag(self, value):
        """Kurzer Zugriff auf global_stichtag"""
        self.global_stichtag = value
    
    @property
    def expert_mode(self):
        """Kurzer Zugriff auf global_expert_mode"""
        return self.global_expert_mode
    
    @expert_mode.setter
    def expert_mode(self, value):
        """Kurzer Zugriff auf global_expert_mode"""
        self.global_expert_mode = value
    
    @property
    def mode(self):
        """Kurzer Zugriff auf global_mode"""
        return self.global_mode
    
    @mode.setter
    def mode(self, value):
        """Kurzer Zugriff auf global_mode"""
        self.global_mode = value
    
    @property
    def country(self):
        """Kurzer Zugriff auf global_country"""
        return self.global_country
    
    @country.setter
    def country(self, value):
        """Kurzer Zugriff auf global_country"""
        self.global_country = value
    
    @property
    def language(self):
        """Kurzer Zugriff auf global_language"""
        return self.global_language
    
    @language.setter
    def language(self, value):
        """Kurzer Zugriff auf global_language"""
        self.global_language = value
    
    # 🎯 NEUE REFRESH-ARCHITEKTUR Properties
    @property
    def current_command(self):
        """Aktueller Menübefehl für Refresh-Mechanismus"""
        return self._current_command
    
    @current_command.setter  
    def current_command(self, value):
        """Setzt den aktuellen Menübefehl"""
        self._current_command = value
    
    @property
    def first_call(self):
        """Flag ob initialer Aufruf (True) oder Refresh (False)"""
        return self._first_call
    
    @first_call.setter
    def first_call(self, value):
        """Setzt das first_call Flag"""
        self._first_call = value

    def get_current_settings(self):
        """Gibt alle aktuellen Einstellungen als Dictionary zurück"""
        return {
            'global_country': self.global_country,
            'global_stichtag': self.global_stichtag,
            'global_expert_mode': self.global_expert_mode,
            'global_mode': self.global_mode,
            'global_language': self.global_language,
            'expert_mode_available': self.is_expert_mode_available(),
            'user_guid': self._user_guid
        }
    
    def debug_values(self):
        """Debug-Ausgabe aller aktuellen Werte - für Kompatibilität mit pdvm_systemstart.py"""
        settings = self.get_current_settings()
        print("=== PdvmCentralSystemsteuerung Debug Values ===")
        for key, value in settings.items():
            print(f"{key}: {value}")
        print("=== Debug Values Ende ===")
    
    def reset_to_defaults(self):
        """Setzt alle Werte auf Standard-Defaults zurück"""
        global global_stichtag_inst
        
        current_pdvm_datetime = self._datetime.PdvmDateTimeNow()
        
        self.global_country = 'AT'
        self.global_stichtag = current_pdvm_datetime  # Float direkt verwenden - automatisch in globale Instanz synchronisiert
        self.global_expert_mode = False
        # ⚠️ WICHTIG: Mode NIEMALS auf 'standard' zurücksetzen - bleibt auf aktuellem Wert!
        # self.global_mode = 'standard'  # DEAKTIVIERT - Mode darf nicht geändert werden
        self.global_language = 'DE'
        print("Einstellungen auf Standard-Defaults zurückgesetzt (Mode beibehalten)")
    
    # 🎯 NEUE REFRESH-ARCHITEKTUR: Zentrale Methoden für Menü-Refresh
    def set_menu_command(self, command_dict, from_menu=True):
        """
        Setzt den aktuellen Menübefehl für Refresh-Mechanismus.
        
        Args:
            command_dict (dict): Das Command-Dictionary aus dem Menü
            from_menu (bool): True wenn aus Menü, False wenn Refresh
        """
        self._current_command = command_dict
        self._first_call = from_menu
    
    def prepare_call_daten(self, base_call_daten=None):
        """
        Bereitet call_daten für Menüaufruf vor - setzt first_call automatisch.
        
        Args:
            base_call_daten (dict): Basis call_daten, falls vorhanden
            
        Returns:
            dict: Vollständige call_daten mit first_call gesetzt
        """
        if base_call_daten is None:
            base_call_daten = {}
        
        # first_call automatisch setzen
        call_daten = base_call_daten.copy()
        call_daten['first_call'] = self._first_call
        
        return call_daten
    
    def delete_group(self, gruppe: str) -> bool:
        """
        Löscht eine komplette Gruppe aus der Systemsteuerung.
        Nutzt die delete_group Methode der zugrunde liegenden Datenbank.
        
        Args:
            gruppe: Name der zu löschenden Gruppe
            
        Returns:
            bool: True wenn Gruppe existierte und gelöscht wurde, False sonst
        """
        logger.info(f"🗑️ Lösche Gruppe '{gruppe}' aus Systemsteuerung")
        result = self._database.delete_group(gruppe)
        if result:
            # Nach Löschung speichern
            self._database.save_values()
            logger.info(f"✅ Gruppe '{gruppe}' erfolgreich gelöscht und persistiert")
        else:
            logger.warning(f"⚠️ Gruppe '{gruppe}' war nicht vorhanden")
        return result
    
    def refresh_current_menu(self):
        """
        Führt Refresh des aktuellen Menüpunkts durch - wiederholt Aufruf mit first_call=False.
        
        Returns:
            dict: call_daten für Refresh-Aufruf oder None wenn kein Command gesetzt
        """
        if self._current_command is None:
            return None
        
        # Setze first_call = False für Refresh
        self._first_call = False
        
        # Bereite call_daten vor (mit current_command als Basis)
        refresh_call_daten = self.prepare_call_daten(self._current_command)
        
        return refresh_call_daten

    # Delegate-Methoden für Kompatibilität mit bestehender API
    def set_value(self, gruppe, feld, wert, ab_zeit=None):
        """Delegate zu PdvmCentralDatenbank.set_value"""
        return self._database.set_value(gruppe, feld, wert, ab_zeit)
    
    def get_value(self, gruppe, feld, stichtag=None):
        """Delegate zu PdvmCentralDatenbank.get_value"""
        return self._database.get_value(gruppe, feld, stichtag)

    # ENTWICKLUNGSPHASE: Rohe String-Methoden
    def set_raw_string(self, gruppe, feld, raw_string, ab_zeit=None):
        """
        ENTWICKLUNGSPHASE: Speichert rohen String ohne JSON-Parsing
        """
        return self._database.set_raw_string(gruppe, feld, raw_string, ab_zeit)
    
    def get_raw_string(self, gruppe, feld, stichtag=None):
        """
        ENTWICKLUNGSPHASE: Lädt rohen String ohne JSON-Parsing
        """
        return self._database.get_raw_string(gruppe, feld, stichtag)

    # COMPATIBILITY: No-JSON Methoden für Spalten-Dialog
    def get_value_no_json(self, gruppe, feld, ab_zeit=None):
        """
        Kompatibilitäts-Methode für Spalten-Dialog - delegiert zu get_raw_string
        
        Args:
            gruppe (str): Gruppe
            feld (str): Feld  
            ab_zeit (float, optional): Zeitstempel
            
        Returns:
            str or None: Roher String-Wert ohne JSON-Parsing
        """
        return self.get_raw_string(gruppe, feld, ab_zeit)
    
    def set_value_no_json(self, gruppe, feld, wert, ab_zeit=1001.0):
        """
        Kompatibilitäts-Methode für Spalten-Dialog - delegiert zu set_raw_string
        
        Args:
            gruppe (str): Gruppe
            feld (str): Feld
            wert (str): Roher String-Wert ohne JSON-Konvertierung
            ab_zeit (float): Zeitstempel
        """
        return self.set_raw_string(gruppe, feld, wert, ab_zeit)


# Globale Instanz für einfache Verwendung
_global_instance = None

def get_central_systemsteuerung(user_guid=None):
    """
    Gibt die globale Instanz zurück oder erstellt sie
    Vereinfachter Zugriff für lineare Architektur
    """
    global _global_instance
    if _global_instance is None:
        _global_instance = PdvmCentralSystemsteuerung(user_guid)
    return _global_instance


def set_global_central_systemsteuerung(instance):
    """
    Setzt die globale Instanz explizit
    Für Kompatibilität mit pdvm_systemstart.py
    """
    global _global_instance
    _global_instance = instance
    return _global_instance


def initialize_central_systemsteuerung(user_guid):
    """
    Explizite Initialisierung für bekannte user_guid
    Für Verwendung in pdvm_systemstart.py
    """
    global _global_instance
    _global_instance = PdvmCentralSystemsteuerung(user_guid)
    return _global_instance


# Alias für gcs (get_central_systemsteuerung) - Kompatibilität
gcs = get_central_systemsteuerung


# Convenience Functions für direkte Verwendung
def get_country():
    """Direkter Zugriff auf Country"""
    return get_central_systemsteuerung().global_country

def set_country(value):
    """Direkter Zugriff zum Setzen von Country"""
    get_central_systemsteuerung().global_country = value

def get_stichtag():
    """Direkter Zugriff auf Stichtag"""
    return get_central_systemsteuerung().global_stichtag

def set_stichtag(value):
    """Direkter Zugriff zum Setzen von Stichtag"""
    get_central_systemsteuerung().global_stichtag = value

def get_global_stichtag_inst():
    """Direkter Zugriff auf die globale Pdvm_DateTime Stichtag-Instanz"""
    return global_stichtag_inst

def is_expert_mode():
    """Direkter Zugriff auf Expert Mode"""
    return get_central_systemsteuerung().global_expert_mode

def set_expert_mode(value):
    """Direkter Zugriff zum Setzen von Expert Mode"""
    get_central_systemsteuerung().global_expert_mode = value

def is_expert_mode_available():
    """Prüft, ob der ExpertMode-Umschalter verfügbar ist (nur bei admin mode)"""
    return get_central_systemsteuerung().is_expert_mode_available()


if __name__ == "__main__":
    # Test der Properties-basierten Architektur
    print("=== Test PdvmCentralSystemsteuerung Properties ===")
    
    # Initialisierung testen
    central = PdvmCentralSystemsteuerung("test_user")
    print(f"Initiale Settings: {central.get_current_settings()}")
    
    # Properties testen
    print(f"\nVor Änderungen:")
    print(f"Country: {central.global_country}")
    print(f"Expert Mode: {central.global_expert_mode}")
    
    # Änderungen mit automatischer Speicherung
    central.global_country = 'DE'
    central.global_expert_mode = True
    
    print(f"\nNach Änderungen:")
    print(f"Country: {central.global_country}")
    print(f"Expert Mode: {central.global_expert_mode}")
    
    # Globale Instanz testen
    print(f"\nGlobale Instanz Test:")
    global_central = get_central_systemsteuerung("global_user")
    print(f"Global Settings: {global_central.get_current_settings()}")
    
    print("\n=== Test erfolgreich abgeschlossen ===")
