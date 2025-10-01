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

        # PROJEKTIONS-TABELLEN MATRIX: Statische Tabellen für Views
        # Struktur: {view_guid: {projection_type: [spalten_liste]}}
        self._projection_tables = {}

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
        self._u_db = PdvmCentralDatenbank('benutzerstamm')

        # Setze die user_json Daten direkt in die Benutzerdatenbank
        # Datenstruktur für die Datenbank: {user_guid: user_data_dict}
        db_data = {user_guid: user_data_dict}
        self._u_db.set_data(self._user_data, user_guid)
        logger.info(f"✅ Benutzerdatenbank geladen mit GUID: {user_guid} und {len(self._user_data)} Properties")

        # 2.2 Datenbank-Instanz für Systemsteuerung
        self._db = PdvmCentralDatenbank('systemsteuerung', user_guid)
        logger.info(f"✅ Systemsteuerungsdatenbank geladen mit GUID: {user_guid}")
        
        # 2.3 Datenbank-Instanz für Anwendungsdaten (gespeicherte Filter, etc.)
        self._app_db = PdvmCentralDatenbank('anwendungsdaten', user_guid)
        logger.info(f"✅ Anwendungsdatenbank geladen mit GUID: {user_guid}")

        # Stichtag-Instanz erstellen und initialisieren
        country = self._u_db.get_static_value(self.user_guid, 'country') if user_guid in self._u_db.data else 'DEU'
        self._st_inst = Pdvm_DateTime(country)
        
        # Temporäre Pdvm_DateTime Instanz für Formatierungen erstellen
        self._temp_dt_inst = Pdvm_DateTime(country)
        logger.info(f"✅ Temporäre Pdvm_DateTime Instanz erstellt für Country: {country}")

        # Stichtag aus Systemsteuerung laden
        stored_stichtag = self._db.get_static_value(self.user_guid, 'stichtag') if user_guid in self._db.data and 'stichtag' in self._db.data[user_guid] else None
        if stored_stichtag is not None:
            try:
                self._st_inst.PdvmDateTime = float(stored_stichtag)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Ungültiger Stichtag aus DB: {stored_stichtag}, verwende Default")
        else:
            # Kein Stichtag in DB: Setze den aktuellen DateTime
            stored_stichtag = self._temp_dt_inst.PdvmDateTimeNow()
            self._st_inst.PdvmDateTime = stored_stichtag
            self._db.set_value(user_guid, 'stichtag', stored_stichtag)
            logger.info(f"💾 Default-Stichtag gesetzt und gespeichert: {stored_stichtag}")

        self._initialized = True
        logger.info(f"✅ Systemsteuerung initialisiert für {user_guid}")
        logger.info(f"📅 Stichtag: {self._st_inst.FormTimeStamp}")
    
    @property
    def db(self):
        """Öffentlicher Zugriff auf die Systemsteuerung-Datenbank-Instanz"""
        self._ensure_initialized()
        return self._db
    
    @property
    def app_db(self):
        """Öffentlicher Zugriff auf die Anwendungsdaten-Datenbank-Instanz (für Filter, etc.)"""
        self._ensure_initialized()
        return self._app_db
    
    # ENTFERNT: u_db Property - kein öffentlicher Zugriff auf Benutzer-DB
    
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
                anwendungen = self.get_property('start', 'u', 'MeineApps')
                return anwendungen
            
            # Für andere Apps: Suche in Anwendungen -> app_name
            app_data = self.get_property(app_name, 'u', 'Anwendungen')
            menu_id = app_data['Menu']
            logger.debug(f"✅ Menü-ID für '{app_name}': {menu_id}")
            return menu_id
            
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
    
    def get_menu_panel_visible(self, menu_guid):
        """
        Einfache direkte Methode für Menüpanel-Sichtbarkeit
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            bool: True = sichtbar, False = ausgeblendet, True = Default (bei None)
        """
        self._ensure_initialized()
        
        property_name = f"menu_visible_{menu_guid}"
        stored_value = self.get_property(property_name, 's')
        
        # Default: sichtbar (True) falls noch nie gesetzt
        return stored_value if stored_value is not None else True
    
    def set_menu_panel_visible(self, menu_guid, visible):
        """
        Speichert die Menüpanel-Sichtbarkeit für ein Menü
        
        Args:
            menu_guid: GUID des Menüs
            visible: bool - True = sichtbar, False = ausgeblendet
        """
        self._ensure_initialized()
        
        property_name = f"menu_visible_{menu_guid}"
        self.set_property(property_name, visible)
        logger.info(f"💾 Menüpanel-Status gespeichert: {visible} für Menü {menu_guid}")
    
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
    def global_expert_mode(self):
        """Alias für expert_mode für Kompatibilität mit globalen Modulen"""
        return self.expert_mode
    
    @global_expert_mode.setter
    def global_expert_mode(self, value):
        """Alias für expert_mode für Kompatibilität mit globalen Modulen"""
        self.expert_mode = value
    
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
    
    # ==========================================
    # EINFACHE PROJEKTIONS-ARCHITEKTUR
    # ==========================================

    def get_projection_table(self, view_guid: str, projection_type: str = "table"):
        """
        ✅ STATISCHES PROJEKTIONS-TABELLEN SYSTEM
        
        Gibt die vorberechneten Projektions-Listen zurück. Diese werden nur 
        beim Speichern der Controls neu aufgebaut, ansonsten statisch verwendet.

        Args:
            view_guid: GUID der View
            projection_type: "table", "change_spalten", "search_spalten", etc.

        Returns:
            list: Statische Liste der Spalten-Keys für den entsprechenden Zweck
        """
        try:
            # Prüfe ob Projektions-Tabellen für diese View existieren
            if view_guid not in self._projection_tables:
                logger.info(f"🔧 Erstelle initiale Projektions-Tabellen für View {view_guid}")
                self._build_projection_tables(view_guid)
            
            # Hole die entsprechende Projektion
            view_projections = self._projection_tables.get(view_guid, {})
            projection = view_projections.get(projection_type, [])
            
            if projection:
                logger.debug(f"✅ Statische Projektion '{projection_type}' für {view_guid}: {len(projection)} Spalten")
                return projection.copy()  # Kopie für Unveränderlichkeit
            else:
                logger.warning(f"⚠️ Keine Projektion '{projection_type}' für View {view_guid} gefunden")
                return []
                
        except Exception as e:
            logger.error(f"❌ Fehler bei get_projection_table({view_guid}, {projection_type}): {e}")
            return []
    
    def _build_projection_tables(self, view_guid: str):
        """
        Baut die 6 statischen Projektions-Tabellen für eine View auf.
        Wird nur aufgerufen nach Controls-Speicherung oder bei erster Verwendung.
        
        Args:
            view_guid: GUID der View
        """
        try:
            # Controls aus Datenbank laden
            controls, _ = self.db.get_value(view_guid, "controls")
            if not controls:
                logger.warning(f"⚠️ Keine Controls für View {view_guid} - erstelle leere Projektionen")
                self._projection_tables[view_guid] = {
                    'table_standard': [],
                    'table_expert': [],
                    'search_standard': [],
                    'search_expert': [],
                    'change_standard': [],
                    'change_expert': [],
                    'sort_standard': [],
                    'sort_expert': []
                }
                return
            
            logger.info(f"🏗️ Baue Projektions-Tabellen für View {view_guid} mit {len(controls)} Controls")
            
            # Analysiere alle Controls
            dummy_controls = []
            visible_controls = []
            hidden_controls = []
            all_controls = []
            non_expert_controls = []  # Spalten die NICHT expert_mode=True haben
            
            for control_key, control_data in controls.items():
                # Dummy-Check
                control_type = control_data.get('type') or control_data.get('control_type', '')
                is_dummy = (control_type == 'dummy' or 
                           control_data.get('dummy', False) or 
                           control_key.lower().startswith('dummy'))
                
                if is_dummy:
                    dummy_controls.append(control_key)
                else:
                    control_info = {
                        'key': control_key,
                        'display_order': control_data.get('display_order', 999),
                        'expert_order': control_data.get('expert_order', 999),
                        'show': control_data.get('show', False),
                        'expert_mode': control_data.get('expert_mode', False)  # Expert Mode Flag
                    }
                    
                    all_controls.append(control_info)
                    
                    # Prüfe Expert Mode Flag - nur Spalten die NICHT expert_mode=True sind
                    if not control_data.get('expert_mode', False):
                        non_expert_controls.append(control_info)
                    
                    if control_data.get('show', False):
                        visible_controls.append(control_key)
                    else:
                        hidden_controls.append(control_key)
            
            # Sortiere nach entsprechenden Orders
            all_controls_display = sorted(all_controls, key=lambda x: x['display_order'])
            all_controls_expert = sorted(all_controls, key=lambda x: (x['expert_order'], x['display_order']))
            visible_controls_display = sorted([c for c in all_controls if c['show']], key=lambda x: x['display_order'])
            non_expert_controls_display = sorted(non_expert_controls, key=lambda x: x['display_order'])
            non_expert_controls_expert = sorted(non_expert_controls, key=lambda x: (x['expert_order'], x['display_order']))
            
            # LINEARES SYSTEM: 8 Projektions-Tabellen (4 Bereiche × 2 Modi)
            projections = {
                # VIEW-Bereich: Darstellung in der Tabelle
                'table_standard': [c['key'] for c in visible_controls_display],        # Nur sichtbare, display_order
                'table_expert': [c['key'] for c in all_controls_display],              # Alle Spalten, display_order
                
                # SEARCH-Bereich: Verfügbare Suchspalten  
                'search_standard': [c['key'] for c in visible_controls_display],      # Nur sichtbare, display_order
                'search_expert': [c['key'] for c in all_controls_display],            # Alle Spalten, display_order
                
                # CHANGE-Bereich: Verwaltbare Spalten in Spaltenverwaltung
                'change_standard': [c['key'] for c in non_expert_controls_display],   # Nur non-expert, display_order
                'change_expert': [c['key'] for c in all_controls_expert],             # Alle Spalten, expert_order
                
                # SORT-Bereich: Sortierbare Spalten im Sortier-Dialog
                'sort_standard': [c['key'] for c in visible_controls_display],        # Nur sichtbare, display_order
                'sort_expert': [c['key'] for c in all_controls_expert]                # Alle Spalten, expert_order
            }
            
            # Speichere in Matrix
            self._projection_tables[view_guid] = projections
            
            logger.info(f"✅ LINEARES Projektions-Tabellen für {view_guid} erstellt:")
            logger.info(f"  📊 Table Standard: {len(projections['table_standard'])} Spalten (nur sichtbare)")
            logger.info(f"  📊 Table Expert: {len(projections['table_expert'])} Spalten (alle)")
            logger.info(f"  🔍 Search Standard: {len(projections['search_standard'])} Spalten (nur sichtbare)") 
            logger.info(f"  🔍 Search Expert: {len(projections['search_expert'])} Spalten (alle)")
            logger.info(f"  🔧 Change Standard: {len(projections['change_standard'])} Spalten (nur non-expert)")
            logger.info(f"  🔧 Change Expert: {len(projections['change_expert'])} Spalten (alle)")
            logger.info(f"  🔄 Sort Standard: {len(projections['sort_standard'])} Spalten (nur sichtbare)")
            logger.info(f"  🔄 Sort Expert: {len(projections['sort_expert'])} Spalten (alle)")
            logger.info(f"  ❌ Dummy Controls: {len(dummy_controls)} (ausgeschlossen)")
            logger.info(f"  📋 Non-Expert Controls: {len(non_expert_controls)} (für Change Standard)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der Projektions-Tabellen für {view_guid}: {e}")
            # Fallback: Leere Projektionen (LINEARES SYSTEM)
            self._projection_tables[view_guid] = {
                'table_standard': [],
                'table_expert': [],
                'search_standard': [],
                'search_expert': [],
                'change_standard': [],
                'change_expert': [],
                'sort_standard': [],
                'sort_expert': []
            }
    
    def rebuild_projection_tables(self, view_guid: str):
        """
        Baut die Projektions-Tabellen für eine View neu auf.
        Wird nach Speicherung von Controls aufgerufen.
        
        Args:
            view_guid: GUID der View
        """
        logger.info(f"🔄 Baue Projektions-Tabellen für {view_guid} neu auf...")
        self._build_projection_tables(view_guid)
    
    def get_projection_for_mode(self, view_guid: str, projection_base: str):
        """
        Hilfsmethode: Gibt die korrekte Projektion basierend auf Expert Mode zurück
        
        Args:
            view_guid: GUID der View
            projection_base: 'table' oder 'search'
            
        Returns:
            list: Spalten-Liste je nach Modus
        """
        if projection_base == 'table':
            if self.expert_mode:
                return self.get_projection_table(view_guid, 'table_expert')
            else:
                return self.get_projection_table(view_guid, 'table_standard')
        elif projection_base == 'search':
            if self.expert_mode:
                return self.get_projection_table(view_guid, 'search_expert') 
            else:
                return self.get_projection_table(view_guid, 'search_standard')
        else:
            return []
    
    # ✅ STATISCHES PROJEKTIONS-SYSTEM 
    # 6 vordefinierte Projektions-Tabellen pro View:
    # - table_standard, table_expert 
    # - search_standard, search_expert
    # - change_spalten, admin
    # 
    # API-Mapping für Kompatibilität:
    # - get_projection_table(view_guid, 'table') → table_standard/table_expert je nach expert_mode
    # - get_projection_table(view_guid, 'search_spalten') → search_standard/search_expert je nach expert_mode  
    # - get_projection_table(view_guid, 'change_spalten') → change_spalten (immer alle)

    def get_projection_matrix(self, view_guid: str):
        """
        ZENTRALE PROJECTION-MATRIX VERWALTUNG

        Gibt die ProjectionMatrix für eine View-GUID zurück.
        Erstellt neue Instanz falls nicht vorhanden.

        Args:
            view_guid: GUID der View

        Returns:
            ProjectionMatrix: Matrix-Instanz für die View
        """
        if not hasattr(self, '_projection_matrices'):
            self._projection_matrices = {}  # Cache für ProjectionMatrix-Instanzen

        if view_guid not in self._projection_matrices:
            try:
                from projection_matrix import ProjectionMatrix
                self._projection_matrices[view_guid] = ProjectionMatrix(view_guid, self)

                # Versuche aus GCS zu laden
                if not self._projection_matrices[view_guid].load_from_gcs():
                    logger.info(f"📝 Neue ProjectionMatrix für View {view_guid} erstellt")

            except Exception as e:
                logger.error(f"❌ Fehler beim Erstellen der ProjectionMatrix: {e}")
                return None

        return self._projection_matrices[view_guid]

    def _update_projection_matrix(self, view_guid: str, basis_columns: list):
        """
        Aktualisiert die ProjectionMatrix mit neuen Basis-Columns

        Args:
            view_guid: GUID der View
            basis_columns: Neue Basis-Spalten
        """
        try:
            matrix = self.get_projection_matrix(view_guid)
            if matrix:
                matrix.update_basis_columns(basis_columns)
                logger.info(f"✅ ProjectionMatrix für {view_guid} aktualisiert")
            else:
                logger.warning(f"⚠️ Konnte ProjectionMatrix für {view_guid} nicht aktualisieren")

        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der ProjectionMatrix: {e}")

    # ✅ ALTE METHODE ENTFERNT: get_projection_table(view_guid, param) 
    # Alle Projektionen werden jetzt über spezialisiierte Methoden bereitgestellt:
    # - get_projection_table(view_guid) für Tabellen
    # - get_projection_column_management(view_guid) für Spaltenverwaltung  
    # - get_projection_search(view_guid) für Such-Dialog

    # ✅ CONTROLS-ZUGRIFF VEREINFACHT: Nur noch über get_value(view_guid, "controls")

    # ✅ SAVE/REBUILD ENTFERNT: Controls werden direkt in pdvm_view_dialog gespeichert

    @property
    def is_initialized(self):
        """Prüfe Initialisierungs-Status"""
        return self._initialized
    
    # ==================================================
    # ERWEITERTE FILTER SPEICHER-METHODEN
    # ==================================================
    
    def save_extended_filters(self, view_guid: str, search_name: str, filters_config: dict):
        """
        Speichere erweiterte Filter-Konfiguration in Anwendungsdatenbank
        
        Struktur: uid=user_guid, Gruppe=view_guid, Feld=search_name
        
        Args:
            view_guid: GUID der View
            search_name: Name der Suche (z.B. "default", "familienname_suche", etc.)
            filters_config: Dictionary mit erweiterten Filter-Bedingungen
        """
        try:
            self._ensure_initialized()
            
            # Speichere in Anwendungsdatenbank: uid=user_guid, gruppe=view_guid, feld=search_name
            self._app_db.set_value(view_guid, search_name, filters_config)
            self._app_db.save_all_values()
            
            logger.info(f"💾 Erweiterte Filter '{search_name}' für View {view_guid} gespeichert: {len(filters_config)} Felder")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern erweiterter Filter: {e}")
            raise
    
    def load_extended_filters(self, view_guid: str, search_name: str = "default") -> dict:
        """
        Lade erweiterte Filter-Konfiguration aus Anwendungsdatenbank
        
        Args:
            view_guid: GUID der View
            search_name: Name der Suche (default: "default")
            
        Returns:
            dict: Erweiterte Filter-Konfiguration oder leeres Dict
        """
        try:
            self._ensure_initialized()
            
            # Lade aus Anwendungsdatenbank
            filters_config, _ = self._app_db.get_value(view_guid, search_name)
            
            if filters_config:
                logger.info(f"✅ Erweiterte Filter '{search_name}' für View {view_guid} geladen: {len(filters_config)} Felder")
                return filters_config
            else:
                logger.info(f"ℹ️ Keine erweiterten Filter '{search_name}' für View {view_guid} gefunden")
                return {}
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden erweiterter Filter: {e}")
            return {}
    
    def list_saved_searches(self, view_guid: str) -> list:
        """
        Liste alle gespeicherten Suchen für eine View
        
        Args:
            view_guid: GUID der View
            
        Returns:
            list: Liste der Suchennamen
        """
        try:
            self._ensure_initialized()
            
            # Hole alle Felder für diese View-Gruppe
            if view_guid in self._app_db.data:
                search_names = list(self._app_db.data[view_guid].keys())
                logger.info(f"📋 {len(search_names)} gespeicherte Suchen für View {view_guid}: {search_names}")
                return search_names
            else:
                return []
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Auflisten gespeicherter Suchen: {e}")
            return []
    
    def delete_saved_search(self, view_guid: str, search_name: str):
        """
        Lösche eine gespeicherte Suche
        
        Args:
            view_guid: GUID der View
            search_name: Name der zu löschenden Suche
        """
        try:
            self._ensure_initialized()
            
            # Lösche aus Anwendungsdatenbank
            if view_guid in self._app_db.data and search_name in self._app_db.data[view_guid]:
                del self._app_db.data[view_guid][search_name]
                self._app_db.save_all_values()
                logger.info(f"🗑️ Gespeicherte Suche '{search_name}' für View {view_guid} gelöscht")
            else:
                logger.warning(f"⚠️ Gespeicherte Suche '{search_name}' für View {view_guid} nicht gefunden")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen gespeicherter Suche: {e}")
            raise

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
