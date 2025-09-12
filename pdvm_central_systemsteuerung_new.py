"""
PdvmCentralSystemsteuerungNew - Neue vereinfach        # User-Daten für Login und Menü
        self._user_daten = user_daten or {}
        self._user_name = ""
        
        # Extrahiere User-Name falls in user_daten verfügbar
        if self._user_daten and isinstance(self._user_daten, dict):
            benutzer_data = self._user_daten.get("Benutzer", {})
            if benutzer_data:
                vorname = benutzer_data.get("Vorname", "")
                name = benutzer_data.get("Name", "")
                self._user_name = f"{vorname} {name}".strip()
                logger.info(f"✅ User-Name aus user_daten extrahiert: {self._user_name}")
        
        # Refresh-Architektur
        self._current_command = None
        self._first_call = True
        
        # Initialisiere Properties
        self._load_all_properties()
        
        # Globale Stichtag-Instanz erstellen und initialisieren
        self._initialize_global_stichtag_instance()
        
        # Log Initialisierung
        logger.info(f"✅ PdvmCentralSystemsteuerungNew initialisiert für User: {self._user_guid}")
        logger.info(f"📋 User-Daten verfügbar: {bool(self._user_daten)}")
        if self._user_daten and "Anwendungen" in self._user_daten:
            apps = self._user_daten["Anwendungen"]
            if "MeineApps" in apps:
                logger.info(f"✅ MeineApps GUID: {apps['MeineApps']}")
            if "Application" in apps:
                logger.info(f"📱 Verfügbare Apps: {list(apps['Application'].keys())}")ystemsteuerung
Klare Architektur mit direktem Property-Zugriff und globaler Stichtag-Instanz
"""

import logging
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_datetime import Pdvm_DateTime

logger = logging.getLogger(__name__)

# GLOBALE INSTANZEN für zentrale Verwendung
global_stichtag_inst = None  # Zentrale Pdvm_DateTime Instanz für Stichtag


class PdvmCentralSystemsteuerungNew:
    """
    Neue vereinfachte zentrale Systemsteuerung mit klarem Properties-Pattern.
    
    DESIGN PRINZIPIEN:
    1. Jede Property hat einen einfachen getter/setter
    2. Stichtag arbeitet DIREKT mit der globalen Instanz
    3. Keine redundanten Fallbacks oder Komplikationen
    4. save_values() persistiert alle Werte
    5. Direkte Kompatibilität mit gcs.property Zugriff
    """
    
    def __init__(self, user_guid, user_daten=None):
        """
        Initialisierung mit user_guid und optionalen user_daten.
        
        Args:
            user_guid (str): GUID des eingeloggten Benutzers (ERFORDERLICH)
            user_daten (dict): Login-Daten des Benutzers (OPTIONAL, aber empfohlen)
        """
        if not user_guid or not isinstance(user_guid, str):
            raise ValueError("❌ user_guid ist erforderlich und muss ein String sein!")
            
        self._user_guid = user_guid.strip()
        
        # Datenbank-Verbindung für Systemsteuerung
        self._database = PdvmCentralDatenbank(
            table_name="systemsteuerung",
            guid=self._user_guid
        )
        
        # Separate Datenbank-Verbindung für Benutzerdaten
        self._user_database = PdvmCentralDatenbank(
            table_name="benutzerdaten",
            guid=self._user_guid
        )
        
        # Properties - werden beim ersten Zugriff geladen
        self._country = None
        self._expert_mode = None
        self._mode = None
        self._language = None
        
        # User-Daten für Login und Menü - speichere in Datenbank wenn übergeben
        if user_daten is not None:
            self._store_user_data_to_database(user_daten)
            logger.info(f"✅ User-Daten in Datenbank gespeichert: {list(user_daten.keys())}")
        else:
            logger.info("ℹ️ Keine user_daten bei GCS-Initialisierung übergeben - verwende DB-Daten")
        
        # Refresh-Architektur
        self._current_command = None
        self._first_call = True
        
        # Initialisiere Properties
        self._load_all_properties()
        
        # Globale Stichtag-Instanz erstellen und initialisieren
        self._initialize_global_stichtag_instance()
    
    def _store_user_data_to_database(self, user_daten):
        """Speichert Benutzerdaten in die Datenbank für robusten Zugriff"""
        try:
            if not user_daten or not isinstance(user_daten, dict):
                logger.warning("⚠️ Keine gültigen user_daten zum Speichern")
                return
                
            # Benutzer-Informationen speichern
            benutzer = user_daten.get("Benutzer", {})
            if benutzer:
                self._user_database.set_value("benutzer", "vorname", benutzer.get("Vorname", ""))
                self._user_database.set_value("benutzer", "nachname", benutzer.get("Name", ""))
                self._user_database.set_value("benutzer", "anrede", benutzer.get("Anrede", ""))
                logger.info(f"✅ Benutzer-Daten gespeichert: {benutzer.get('Vorname', '')} {benutzer.get('Name', '')}")
            
            # Anwendungen speichern
            anwendungen = user_daten.get("Anwendungen", {})
            if anwendungen:
                # Startmenü-GUID speichern
                startmenu_guid = anwendungen.get("MeineApps")
                if startmenu_guid:
                    self._user_database.set_value("anwendungen", "startmenu_guid", startmenu_guid)
                    logger.info(f"✅ Startmenü-GUID gespeichert: {startmenu_guid}")
                
                # Verfügbare Anwendungen speichern
                applications = anwendungen.get("Application", {})
                if applications:
                    # Speichere jede Anwendung als separaten Eintrag
                    verfuegbare_apps = []
                    for app_name, app_data in applications.items():
                        if isinstance(app_data, dict) and app_data.get("Menu"):
                            self._user_database.set_value("apps", app_name.lower(), app_data["Menu"])
                            verfuegbare_apps.append(app_name)
                            logger.info(f"✅ App gespeichert: {app_name} -> {app_data['Menu']}")
                    
                    # Speichere Liste der verfügbaren Apps als JSON
                    import json
                    self._user_database.set_value("anwendungen", "verfuegbare_apps", json.dumps(verfuegbare_apps))
                    logger.info(f"✅ Verfügbare Apps gespeichert: {verfuegbare_apps}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Benutzerdaten: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _load_all_properties(self):
        """Lädt alle Properties aus der Datenbank oder setzt Defaults"""
        defaults = {
            'country': 'DEU',
            'stichtag': Pdvm_DateTime("DEU").PdvmDateTimeNow(),  # Aktueller Timestamp als Default
            'expert_mode': False,
            'mode': 'user',
            'language': 'de-de'
        }
        
        for key, default_value in defaults.items():
            try:
                result = self._database.get_value(self._user_guid, key)
                saved_value = result.get("wert") if result else None
                
                # Normale Property-Behandlung für alle Properties gleich
                setattr(self, f"_{key}", saved_value if saved_value is not None else default_value)
                logger.info(f"✅ Property {key} geladen: {getattr(self, f'_{key}')}")
                    
            except Exception as e:
                setattr(self, f"_{key}", default_value)
                logger.warning(f"⚠️ Property {key} auf Default gesetzt: {default_value} (Fehler: {e})")
    
    def _initialize_global_stichtag_instance(self):
        """Initialisiert die globale Stichtag-Instanz mit dem geladenen Stichtag-Wert"""
        global global_stichtag_inst
        
        # Erstelle neue Instanz mit dem geladenen Country
        global_stichtag_inst = Pdvm_DateTime(self._country)
        
        # Verwende den bereits geladenen Stichtag-Wert (aus _load_all_properties)
        if hasattr(self, '_stichtag') and self._stichtag is not None:
            global_stichtag_inst.PdvmDateTime = self._stichtag
            logger.info(f"✅ Stichtag in globale Instanz gesetzt: {global_stichtag_inst.FormTimeStamp}")
        else:
            # Fallback: aktueller Zeitstempel
            current_time = global_stichtag_inst.PdvmDateTimeNow()
            global_stichtag_inst.PdvmDateTime = current_time
            self._stichtag = current_time  # Auch lokal setzen
            logger.warning(f"⚠️ Stichtag Fallback auf aktuell: {global_stichtag_inst.FormTimeStamp}")
    
    # ==========================================================================
    # PROPERTY: COUNTRY
    # ==========================================================================
    @property
    def country(self):
        """Land/Country Code (AT, DEU, etc.)"""
        return self._country
    
    @country.setter
    def country(self, value):
        """Setzt den Country Code und speichert automatisch"""
        self._country = value
        self.save_values()
        logger.info(f"✅ Country gesetzt und gespeichert: {value}")
    
    @property
    def global_country(self):
        """Alias für country - für Kompatibilität"""
        return self._country
    
    # ==========================================================================
    # PROPERTY: STICHTAG (arbeitet direkt mit globaler Instanz)
    # ==========================================================================
    @property
    def stichtag(self):
        """Stichtag als Float-Wert - DIREKT aus globaler Instanz"""
        global global_stichtag_inst
        if global_stichtag_inst is not None:
            return global_stichtag_inst.PdvmDateTime
        return None
    
    @stichtag.setter
    def stichtag(self, value):
        """Setzt Stichtag DIREKT in globale Instanz und speichert automatisch"""
        global global_stichtag_inst
        if global_stichtag_inst is not None:
            global_stichtag_inst.PdvmDateTime = value
            # Auch lokal setzen für Konsistenz (wird beim Speichern verwendet)
            self._stichtag = value
            self.save_stichtag()  # Nur Stichtag speichern für Performance
            logger.info(f"✅ Stichtag gesetzt und gespeichert: {value}")
    
    @property
    def global_stichtag_inst(self):
        """Direkte Referenz auf die globale Stichtag-Instanz"""
        global global_stichtag_inst
        return global_stichtag_inst
    
    # ==========================================================================
    # PROPERTY: EXPERT_MODE
    # ==========================================================================
    @property
    def expert_mode(self):
        """Expert Mode Flag (Boolean)"""
        return self._expert_mode
    
    @expert_mode.setter
    def expert_mode(self, value):
        """Setzt Expert Mode und speichert automatisch"""
        self._expert_mode = bool(value)
        self.save_values()
        logger.info(f"✅ Expert Mode gesetzt und gespeichert: {value}")
    
    # ==========================================================================
    # PROPERTY: MODE
    # ==========================================================================
    @property
    def mode(self):
        """System Mode ('user', 'admin', etc.)"""
        return self._mode
    
    @mode.setter
    def mode(self, value):
        """Setzt System Mode und speichert automatisch"""
        self._mode = value
        self.save_values()
        logger.info(f"✅ Mode gesetzt und gespeichert: {value}")
    
    # ==========================================================================
    # PROPERTY: LANGUAGE
    # ==========================================================================
    @property
    def language(self):
        """Sprache (de-de, en-us, etc.)"""
        return self._language
    
    @language.setter
    def language(self, value):
        """Setzt Sprache und speichert automatisch"""
        self._language = value
        self.save_values()
        logger.info(f"✅ Language gesetzt und gespeichert: {value}")

    # ==========================================================================
    # USER-DATEN PROPERTIES - Direkte Getter für häufig verwendete Daten
    # ==========================================================================
    @property
    def user_daten(self):
        """User-Login-Daten für Menü und Berechtigungen"""
        return self._user_daten
    # ==========================================================================
    # USER DATA PROPERTIES (DATABASE-BASED)
    # ==========================================================================
    
    @property
    def user_vorname(self):
        """Vorname des Benutzers aus Datenbank"""
        result = self._user_database.get_value("benutzer", "vorname")
        return result if result else ""
    
    @property
    def user_nachname(self):
        """Nachname des Benutzers aus Datenbank"""
        result = self._user_database.get_value("benutzer", "nachname")
        return result if result else ""
    
    @property
    def user_anrede(self):
        """Anrede des Benutzers aus Datenbank"""
        result = self._user_database.get_value("benutzer", "anrede")
        return result if result else ""
    
    @property
    def user_vollname(self):
        """Vollständiger Name des Benutzers"""
        vorname = self.user_vorname
        nachname = self.user_nachname
        return f"{vorname} {nachname}".strip() if vorname or nachname else "Unbekannter Benutzer"
    
    @property
    def startmenu_guid(self):
        """Startmenü-GUID für Hauptanwendung aus Datenbank"""
        result = self._user_database.get_value("anwendungen", "startmenu_guid")
        if not result:
            logger.warning("⚠️ Keine Startmenü-GUID in Datenbank gefunden!")
        return result if result else None
    
    @property
    def anwendungen(self):
        """Verfügbare Anwendungen des Benutzers aus Datenbank"""
        # Lade alle verfügbaren Apps und baue die Struktur auf
        import json
        result = self._user_database.get_value("anwendungen", "verfuegbare_apps")
        if not result:
            return {}
            
        try:
            verfuegbare_apps = json.loads(result) if result else []
            anwendungen = {}
            
            for app_name in verfuegbare_apps:
                menu_result = self._user_database.get_value("apps", app_name.lower())
                if menu_result:
                    anwendungen[app_name] = {"Menu": menu_result}
                    
            return anwendungen
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"⚠️ Fehler beim Laden der Anwendungen: {e}")
            return {}
    
    @property
    def berechtigungen(self):
        """Berechtigungen für Anwendungen (nur die mit Menu-GUID)"""
        apps = self.anwendungen
        return {app: config for app, config in apps.items() if config.get("Menu")}
    
    @property
    def verfuegbare_apps(self):
        """Liste der verfügbaren App-Namen aus Datenbank"""
        import json
        result = self._user_database.get_value("anwendungen", "verfuegbare_apps")
        if result:
            try:
                return json.loads(result) if result else []
            except json.JSONDecodeError:
                logger.warning("⚠️ Fehler beim Parsen der verfügbaren Apps")
                return []
        return []
    
    # ==========================================================================
    # PERSISTIERUNG
    # ==========================================================================
    def save_values(self):
        """Speichert alle Property-Werte persistent"""
        properties_to_save = ['country', 'expert_mode', 'mode', 'language']
        
        try:
            # Speichere Standard-Properties
            for prop in properties_to_save:
                value = getattr(self, f"_{prop}")
                self._database.set_value(self._user_guid, prop, value)
                logger.info(f"💾 Property {prop} gespeichert: {value}")
            
            # Speichere Stichtag aus globaler Instanz
            global global_stichtag_inst
            if global_stichtag_inst is not None:
                stichtag_value = global_stichtag_inst.PdvmDateTime
                self._database.set_value(self._user_guid, 'stichtag', stichtag_value)
                logger.info(f"💾 Stichtag gespeichert: {stichtag_value}")
            
            # Datenbank-Speicherung ausführen
            self._database.save_all_values()
            logger.info("✅ Alle Werte erfolgreich gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            raise
    
    def save_stichtag(self):
        """Speichert nur den Stichtag - für Kompatibilität"""
        global global_stichtag_inst
        
        try:
            if global_stichtag_inst is not None:
                stichtag_value = global_stichtag_inst.PdvmDateTime
                self._database.set_value(self._user_guid, 'stichtag', stichtag_value)
                self._database.save_all_values()
                logger.info(f"✅ Stichtag gespeichert: {stichtag_value}")
            else:
                logger.warning("⚠️ Keine globale Stichtag-Instanz verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Stichtags: {e}")
            raise
    
    # ==========================================================================
    # REFRESH-ARCHITEKTUR
    # ==========================================================================
    def refresh_current_menu(self):
        """Gibt Call-Daten für Menü-Refresh zurück"""
        if self._current_command:
            # Erstelle Refresh-Call-Daten mit first_call=False
            refresh_call_daten = self._current_command.copy()
            refresh_call_daten['first_call'] = False
            return refresh_call_daten
        return None
    
    def set_current_command(self, command_dict):
        """Setzt den aktuellen Menübefehl für Refresh"""
        self._current_command = command_dict
        
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    def get_user_guid(self):
        """Gibt die User-GUID zurück"""
        return self._user_guid
    
    def __str__(self):
        """String-Repräsentation für Debugging"""
        return (f"PdvmCentralSystemsteuerungNew("
                f"user_guid={self._user_guid}, "
                f"country={self.country}, "
                f"stichtag={self.stichtag}, "
                f"mode={self.mode})")
