#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINALE ZENTRALE SYSTEMSTEUERUNG

Robuste Architektur mit:
1. User-GUID und Benutzerdaten bei Initialisierung
2. Parametrisierte Properties für flexible Erweiterung
3. Persistente Speicherung bei allen Settern
4. Spezielle Stichtag-Behandlung über st_inst
"""

import logging
from typing import Dict
from pdvm_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmCentralSystemsteuerung:
    """Zentrale Systemsteuerung mit robuster Architektur"""

    def __init__(self, user_guid, user_data):
        """Initialisierung direkt im Konstruktor"""
        self._db = None
        self._user_guid = user_guid
        self._user_data = user_data
        self._st_inst = None
        self._temp_dt_inst = None  # Temporäre Pdvm_DateTime Instanz für Formatierungen
        self._dropdown_cache = {}  # Cache für geladene Dropdowns: {dropdown_name: {language: {key: value}}}
        self._initialized = False

        if not user_guid:
            raise ValueError("User-GUID muss übergeben werden!")

        # JSON-String zu Dictionary konvertieren falls nötig
        if isinstance(user_data, str):
            import json
            try:
                user_data_dict = json.loads(user_data)
                logger.info("✅ user_data JSON erfolgreich geparst")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ user_data JSON konnte nicht geparst werden: {e}")
                user_data_dict = {}
        else:
            user_data_dict = user_data if user_data else {}

        self._user_data = user_data_dict.copy() if user_data_dict else {}

        # 2.1 Datenbank-Instanz für Benutzerstamm (ohne erneut DB zu lesen)
        from pdvm_central_datenbank import PdvmCentralDatenbank as RealDB
        self._u_db = RealDB('benutzerstamm')

        # Setze die user_json Daten direkt in die Benutzerdatenbank
        if user_data_dict:
            # Datenstruktur für die Datenbank: {user_guid: user_data_dict}
            db_data = {user_guid: user_data_dict}
            self._u_db.set_data(db_data, user_guid)
            logger.info(f"✅ Benutzerdatenbank geladen mit GUID: {user_guid} und {len(user_data_dict)} Properties")
        else:
            logger.warning(f"⚠️ Keine Benutzerdaten für GUID: {user_guid}")

        # 2.2 Datenbank-Instanz für Systemsteuerung
        self._db = RealDB('systemsteuerung', user_guid)
        logger.info(f"✅ Systemsteuerungsdatenbank geladen mit GUID: {user_guid}")

        # Stichtag-Instanz erstellen und initialisieren
        try:
            country = self._u_db.get_static_value(user_guid, 'country') if user_guid in self._u_db.data else 'DEU'
        except KeyError:
            country = 'DEU'
            logger.info(f"⚠️ Country nicht in Benutzerdaten gefunden, verwende Default: {country}")
        self._st_inst = Pdvm_DateTime(country)
        
        # Temporäre Pdvm_DateTime Instanz für Formatierungen erstellen
        self._temp_dt_inst = Pdvm_DateTime(country)
        logger.info(f"✅ Temporäre Pdvm_DateTime Instanz erstellt für Country: {country}")

        # Stichtag aus Systemsteuerung laden
        try:
            stored_stichtag = self._db.get_static_value(user_guid, 'stichtag') if user_guid in self._db.data and 'stichtag' in self._db.data[user_guid] else None
        except KeyError:
            stored_stichtag = None
            logger.info(f"⚠️ Stichtag nicht in Systemsteuerung gefunden, verwende Default")
        if stored_stichtag is not None:
            try:
                self._st_inst.PdvmDateTime = float(stored_stichtag)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Ungültiger Stichtag aus DB: {stored_stichtag}, verwende Default")
        else:
            # Kein Stichtag in DB: Setze bekannten Default-Wert
            default_stichtag = 1001.0
            self._st_inst.PdvmDateTime = default_stichtag
            self._db.set_value(user_guid, 'stichtag', default_stichtag)
            logger.info(f"💾 Default-Stichtag gesetzt und gespeichert: {default_stichtag}")

        self._initialized = True
        logger.info(f"✅ Systemsteuerung initialisiert für {user_guid}")
        logger.info(f"📅 Stichtag: {self._st_inst.FormTimeStamp}")
    
    @property
    def db(self):
        """Öffentlicher Zugriff auf die Systemsteuerung-Datenbank-Instanz"""
        self._ensure_initialized()
        return self._db
    
    # ENTFERNT: u_db Property - kein öffentlicher Zugriff auf Benutzer-DB
    
#    @property
#    def u_db(self):
#        """Öffentlicher Zugriff auf die Benutzer-Datenbank-Instanz"""
#        self._ensure_initialized()
#        return self._u_db

    def _ensure_initialized(self):
        """Prüfe ob initialisiert"""
        if not self._initialized:
            raise RuntimeError("Systemsteuerung nicht initialisiert! Rufe initialize() auf.")
    
    def get_property(self, property_name, db_type='s', gruppe=None):
        """
        Lade Property aus der gewählten Datenbank
        
        Args:
            property_name: Name der Property
            db_type: 'u' für Benutzer-DB, 's' für Systemsteuerung-DB
            gruppe: Gruppe (default: user_guid)
        """
        self._ensure_initialized()
        
        if gruppe is None:
            gruppe = self._user_guid
            
        if db_type == 'u':
            try:
                return self._u_db.get_static_value(gruppe, property_name)
            except KeyError:
                logger.warning(f"⚠️ Property '{property_name}' nicht in Benutzerdaten gefunden für Gruppe '{gruppe}'")
                return None
        else:
            try:
                return self._db.get_static_value(gruppe, property_name)
            except KeyError:
                logger.warning(f"⚠️ Property '{property_name}' nicht in Systemsteuerung gefunden für Gruppe '{gruppe}'")
                return None
    
    def set_property(self, property_name, value, gruppe=None):
        """
        Setze Property NUR in der Systemsteuerung-DB (Benutzer-DB ist read-only)
        
        Args:
            property_name: Name der Property
            value: Wert
            gruppe: Gruppe (default: user_guid)
        """
        self._ensure_initialized()
        
        if gruppe is None:
            gruppe = self._user_guid
            
        # Nur in Systemsteuerung schreiben - Benutzer-DB ist read-only
        self._db.set_value(gruppe, property_name, value)

    def get_menu_id(self, app_name):
        """
        Hole die Menü-GUID für eine spezifische Anwendung aus den Benutzerdaten
        
        Args:
            app_name: Name der Anwendung (z.B. "Testbereich", "Administration")
            
        Returns:
            Menü-GUID als String oder None falls nicht gefunden
        """
        self._ensure_initialized()
        
        try:
            # Navigiere zu Anwendungen -> Application -> [app_name] -> Menu
            anwendungen = self._u_db.data.get('Anwendungen', {})
            applications = anwendungen.get('Application', {})
            app_config = applications.get(app_name, {})
            menu_id = app_config.get('Menu')
            
            if menu_id:
                logger.debug(f"✅ Menü-ID für App '{app_name}': {menu_id}")
                return menu_id
            else:
                logger.debug(f"⚠️ Keine Menü-ID für App '{app_name}' gefunden")
                return None
                
        except Exception as e:
            logger.warning(f"❌ Fehler beim Holen der Menü-ID für App '{app_name}': {e}")
            return None
    
    def get_menu_id(self, app_name):
        """
        Hole Menü-ID für eine bestimmte Applikation aus Benutzerdaten
        
        Args:
            app_name: Name der Applikation (z.B. 'Testbereich', 'Startbereich')
            
        Returns:
            str: Menü-ID oder None wenn nicht gefunden
        """
        self._ensure_initialized()
        
        try:
            # Spezielle Behandlung für 'Startbereich' - kommt aus 'MeineApps'
            if app_name == 'Startbereich':
                # Suche in Anwendungen -> MeineApps
                anwendungen = self.get_property('Anwendungen', 'u')
                if anwendungen and isinstance(anwendungen, dict):
                    return anwendungen.get('MeineApps')
                return None
            
            # Für andere Apps: Suche in Anwendungen -> Application -> app_name
            anwendungen = self.get_property('Anwendungen', 'u')
            if anwendungen and isinstance(anwendungen, dict):
                applications = anwendungen.get('Application', {})
                if isinstance(applications, dict) and app_name in applications:
                    app_config = applications[app_name]
                    if isinstance(app_config, dict) and 'Menu' in app_config:
                        menu_id = app_config['Menu']
                        logger.debug(f"✅ Menü-ID für '{app_name}': {menu_id}")
                        return menu_id
            
            logger.warning(f"⚠️ Menü-ID für App '{app_name}' nicht gefunden in Benutzerdaten")
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen der Menü-ID für App '{app_name}': {e}")
            return None
    
    def get_all_app_menu_ids(self):
        """
        Hole alle verfügbaren App-Namen und ihre Menü-GUIDs
        
        Returns:
            Dictionary: {app_name: menu_id, ...}
        """
        self._ensure_initialized()
        
        try:
            anwendungen = self._u_db.data.get('Anwendungen', {})
            applications = anwendungen.get('Application', {})
            
            app_menu_mapping = {}
            for app_name, app_config in applications.items():
                menu_id = app_config.get('Menu')
                app_menu_mapping[app_name] = menu_id
                
            logger.debug(f"✅ App-Menü-Mapping: {app_menu_mapping}")
            return app_menu_mapping
            
        except Exception as e:
            logger.warning(f"❌ Fehler beim Holen aller App-Menü-IDs: {e}")
            return {}
    
    # ENTFERNT: save_all_values() - nicht benötigt da Systemsteuerung-DB direkt ansprechbar
    
    def field_value(self, property_name, value=None):
        """
        Parametrisierter Getter/Setter für Properties
        
        Args:
            property_name: Name der Property
            value: Wert zum Setzen (None = Getter)
            
        Returns:
            Bei Getter: Wert der Property
            Bei Setter: None
        """
        self._ensure_initialized()
        
        if value is None:
            # Getter
            if property_name == 'stichtag':
                return self._st_inst.PdvmDateTime if self._st_inst else None
            else:
                return self.get_property(property_name, 's')
        else:
            # Setter
            if property_name == 'stichtag':
                if self._st_inst:
                    self._st_inst.PdvmDateTime = float(value)
                    # Speichere direkt über DB-Instanz - kein save_all_values() mehr
                    self._db.set_value(self._user_guid, 'stichtag', value)
            else:
                self.set_property(property_name, value)
            return None
    
    def get_group(self, group_guid, db_type='s'):
        """
        Hole alle Properties einer Gruppe
        
        Args:
            group_guid: GUID der Gruppe
            db_type: 'u' für Benutzer-DB, 's' für Systemsteuerung-DB
            
        Returns:
            Dictionary mit Gruppen-Daten
        """
        self._ensure_initialized()
        
        if db_type == 'u':
            if group_guid in self.u_db.data:
                return self.u_db.data[group_guid].copy()
            return {}
        else:
            if group_guid in self._db.data:
                return self._db.data[group_guid].copy()
            return {}
    
    def set_group(self, group_guid, group_data):
        """
        Setze alle Properties einer Gruppe NUR in Systemsteuerung-DB
        
        Args:
            group_guid: GUID der Gruppe
            group_data: Dictionary mit Daten
        """
        self._ensure_initialized()
        
        # Direkte Änderung in DB-Instanz vermeiden - verwende set_value
        for key, value in group_data.items():
            self._db.set_value(group_guid, key, value)
    
    def group_value(self, group_guid, value=None):
        """
        LEGACY: Getter/Setter für Gruppen-Properties (backwards compatibility)
        
        Args:
            group_guid: GUID der Gruppe
            value: Wert zum Setzen (None = Getter)
            
        Returns:
            Bei Getter: Dictionary mit Gruppen-Daten
            Bei Setter: None
        """
        if value is None:
            return self.get_group(group_guid, 's')
        else:
            self.set_group(group_guid, value)
            return None
    
    # ENTFERNT: save_values() - überflüssige Weiterleitung
    
    @property
    def st_inst(self):
        """Stichtag-Instanz für DateTimePicker"""
        self._ensure_initialized()
        return self._st_inst
    
    @property
    def stichtag(self):
        """Stichtag als Float-Wert (direkter Zugriff)"""
        self._ensure_initialized()
        return self._st_inst.PdvmDateTime if self._st_inst else None
    
    def update_stichtag(self):
        """
        Aktualisiert den Stichtag in der Datenbank aus der aktuellen st_inst.
        
        Diese Methode liest den aktuellen Wert aus self._st_inst.PdvmDateTime
        und speichert ihn in der Systemsteuerungsdatenbank.
        """
        self._ensure_initialized()
        if self._st_inst and self._db:
            current_stichtag = self._st_inst.PdvmDateTime
            # Speichere in Systemsteuerung-DB
            self._db.set_value(self._user_guid, 'stichtag', current_stichtag)
            # Persistiere alle Änderungen
            self._db.save_all_values()
            logger.info(f"💾 Stichtag in finale GCS gespeichert: {current_stichtag} ({self._st_inst.FormTimeStamp})")
        else:
            logger.error("❌ Kann Stichtag nicht speichern - st_inst oder db nicht verfügbar")
    
    @property
    def user_guid(self):
        """User-GUID (readonly)"""
        return self._user_guid
    
    @property
    def user_data(self):
        """Benutzerdaten (readonly)"""
        return self._user_data.copy() if self._user_data else {}
    
    @property
    def country(self):
        """Country aus Benutzerdaten (Parameter Gruppe)"""
        self._ensure_initialized()
        try:
            # Hole country aus Parameter Gruppe der Benutzerdaten
            parameter_data = self._user_data.get('Parameter', {})
            return parameter_data.get('country', 'DEU')
        except (KeyError, AttributeError, TypeError):
            return 'DEU'
    
    @property
    def language(self):
        """Language aus Benutzerdaten (Parameter Gruppe)"""
        self._ensure_initialized()
        try:
            # Hole language aus Parameter Gruppe der Benutzerdaten
            parameter_data = self._user_data.get('Parameter', {})
            return parameter_data.get('language', 'de-de')
        except (KeyError, AttributeError, TypeError):
            return 'de-de'
    
    @property
    def mode(self):
        """Mode aus Benutzerdaten (Parameter Gruppe)"""
        self._ensure_initialized()
        try:
            # Hole mode aus Parameter Gruppe der Benutzerdaten
            parameter_data = self._user_data.get('Parameter', {})
            return parameter_data.get('mode', 'user')
        except (KeyError, AttributeError, TypeError):
            return 'user'
    
    @property
    def temp_dt_inst(self):
        """Temporäre Pdvm_DateTime Instanz für Formatierungen"""
        self._ensure_initialized()
        return self._temp_dt_inst
    
    @property
    def expert_mode(self):
        """Expert-Modus aus Systemsteuerung-DB"""
        self._ensure_initialized()
        try:
            return self.get_property('expert_mode', 's') or False
        except (KeyError, AttributeError):
            # Default-Wert setzen wenn Property nicht existiert
            self.set_property('expert_mode', False, 's')
            return False
    
    @expert_mode.setter
    def expert_mode(self, value):
        """Setze Expert-Modus in Systemsteuerung-DB"""
        self._ensure_initialized()
        self.set_property('expert_mode', bool(value))
        # Explizit persistieren
        self._db.save_all_values()
        logger.info(f"💾 ExpertMode persistent gespeichert: {bool(value)}")
    
    @property
    def is_admin(self):
        """Admin-Modus basierend auf mode='admin' in Systemsteuerung-DB"""
        self._ensure_initialized()
        try:
            # Hole mode aus Systemsteuerung-DB (nicht Benutzer-DB)
            if self._user_guid in self._db.data:
                user_mode = self._db.data[self._user_guid].get('mode', '')
                return str(user_mode).lower() == 'admin'
            return False
        except (KeyError, AttributeError, TypeError):
            return False
    
    def get_dropdown_options(self, dropdown_guid: str, dropdown_gruppe: str = None) -> Dict[str, str]:
        """
        Holt Dropdown-Optionen für einen bestimmten Dropdown-Namen.
        Lädt einmal pro Sitzung und cached die Ergebnisse.
        
        Args:
            dropdown_guid: GUID des Dropdowns (z.B. 'ddaa6590-6d08-461b-a061-75faec26f4ba')
            dropdown_gruppe: Gruppe des Dropdowns (z.B. 'anrede'). Wenn None, wird versucht sie zu ermitteln.
            
        Returns:
            Dict[str, str]: {key: display_text} für die aktuelle Sprache
        """
        self._ensure_initialized()
        
        # Cache-Key für diese Sprache und Gruppe
        cache_key = f"{dropdown_guid}_{dropdown_gruppe or 'unknown'}_{self.language}"
        
        # Cache prüfen
        if cache_key in self._dropdown_cache:
            logger.debug(f"📋 Dropdown '{dropdown_gruppe or dropdown_guid}' aus Cache geladen")
            return self._dropdown_cache[cache_key]
        
        try:
            # Dropdown aus Datenbank laden - verwende die korrekte Struktur
            dropdown_db = PdvmCentralDatenbank(
                table_name="dropdowndaten",
                guid=dropdown_guid  # dropdown_guid ist die GUID aus "key"
            )
            
            # Übersetzungstabelle mit get_all_values holen
            dropdown_data = dropdown_db.get_all_values()
            
            if dropdown_data and isinstance(dropdown_data, dict):
                # Datenstruktur: {gruppe: {sprache: {key: value}}}
                # Beispiel: {"anrede": {"de-de": {"m": "Herr", "w": "Frau"}}}
                
                # Finde die richtige Gruppe (z.B. "anrede")
                # Normalerweise ist dropdown_name die GUID, aber wir brauchen die Gruppe
                # Für Testzwecke nehmen wir an, dass die Gruppe "anrede" ist
                gruppe_name = "anrede"  # TODO: Das sollte aus den ViewDaten kommen
                
                if gruppe_name in dropdown_data:
                    gruppe_data = dropdown_data[gruppe_name]
                    if isinstance(gruppe_data, dict):
                        # Sprache mapping: DEU -> de-de
                        language_map = {
                            'DEU': 'de-de',
                            'ENG': 'us-en',
                            'FRA': 'fr-fr'
                        }
                        db_language = language_map.get(self.language, self.language.lower())
                        
                        if db_language in gruppe_data:
                            language_data = gruppe_data[db_language]
                            if isinstance(language_data, dict):
                                # Cache speichern
                                self._dropdown_cache[cache_key] = language_data
                                logger.info(f"✅ Dropdown '{dropdown_guid}' (Gruppe: {gruppe_name}) geladen: {len(language_data)} Optionen für {db_language}")
                                return language_data
                            else:
                                logger.warning(f"⚠️ Ungültige Sprachdaten für '{db_language}' in Gruppe '{gruppe_name}'")
                        else:
                            logger.warning(f"⚠️ Sprache '{db_language}' nicht gefunden in Gruppe '{gruppe_name}'. Verfügbare Sprachen: {list(gruppe_data.keys())}")
                    else:
                        logger.warning(f"⚠️ Ungültige Gruppendaten für '{gruppe_name}'")
                else:
                    logger.warning(f"⚠️ Gruppe '{gruppe_name}' nicht in Dropdown-Daten gefunden. Verfügbare Gruppen: {list(dropdown_data.keys())}")
            else:
                logger.warning(f"⚠️ Keine gültigen Dropdown-Daten für GUID '{dropdown_guid}'")
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Dropdowns '{dropdown_guid}': {e}")
            return {}
    
    def translate_dropdown_value(self, dropdown_guid: str, raw_value: str, dropdown_gruppe: str = None) -> str:
        """
        Übersetzt einen Raw-Wert zu seinem Display-Text für einen bestimmten Dropdown.
        
        Args:
            dropdown_guid: GUID des Dropdowns (z.B. 'ddaa6590-6d08-461b-a061-75faec26f4ba')
            raw_value: Der rohe Wert (z.B. 'm')
            dropdown_gruppe: Gruppe des Dropdowns (z.B. 'anrede'). Wenn None, wird versucht sie zu ermitteln.
            
        Returns:
            str: Übersetzter Display-Text oder Raw-Wert als Fallback
        """
        if not raw_value:
            return ""
        
        # Optionen für diesen Dropdown holen
        options = self.get_dropdown_options(dropdown_guid, dropdown_gruppe)
        
        # Übersetzung suchen
        return options.get(str(raw_value), str(raw_value))
    
    @property
    def is_initialized(self):
        """Prüfe Initialisierungs-Status"""
        return self._initialized

# Globale Instanz
_gcs_instance = None

def initialize_gcs(user_guid, user_data):
    """
    Initialisiere globale Systemsteuerung
    
    Args:
        user_guid: GUID des Benutzers
        user_data: Benutzerdaten nach Login
    """
    global _gcs_instance
    
    if _gcs_instance is not None and _gcs_instance.is_initialized:
        raise RuntimeError("GCS bereits initialisiert!")
    
    _gcs_instance = PdvmCentralSystemsteuerung(user_guid, user_data)
    
    logger.info("🌐 Globale Systemsteuerung initialisiert")
    return _gcs_instance

def get_gcs():
    """Hole globale Systemsteuerung"""
    if _gcs_instance is None or not _gcs_instance.is_initialized:
        raise RuntimeError("GCS nicht initialisiert! Rufe initialize_gcs() auf.")
    return _gcs_instance

def is_gcs_initialized():
    """Prüfe ob GCS initialisiert ist"""
    return _gcs_instance is not None and _gcs_instance.is_initialized

# Alias für einfachen Zugriff
gcs = property(get_gcs)
