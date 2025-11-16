#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2.0 ZENTRALE SYSTEMSTEUERUNG

Erweiterung der bewährten pdvm_central_systemsteuerung.py für V2.0:
1. User-GUID und Benutzerdaten bei Initialisierung
2. MANDANT-GUID und Mandanten-Daten hinzugefügt (NEU!)
3. 4 Datenbank-Instanzen: u_db, app_db, db, man_db (NEU!)
4. Parametrisierte Properties für flexible Erweiterung
5. Persistente Speicherung bei allen Settern
6. Spezielle Stichtag-Behandlung über st_inst
"""

import logging
from typing import Dict, Union
from PyQt5.QtCore import QObject, pyqtSignal
from pdvm_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

# ========================================
# PROJECTION TABLE ARRAY KONSTANTEN
# ========================================
# Array-Positionen für Projektions-Tabellen (0-9)
TABLE_INDEX_VIEW = 0           # View-Darstellung (ProjectionMatrix)
TABLE_INDEX_CHANGE = 1         # Spalten verwalten Dialog
TABLE_INDEX_FILTER = 2         # Filter Dialog
TABLE_INDEX_SORT = 3           # Sort Dialog (NEU!)
TABLE_INDEX_RESERVED = 4       # Reserviert für zukünftige Features

EXPERT_MODE_OFFSET = 5         # Expert Mode = Standard + 5

# Legacy-Mapping für Abwärtskompatibilität
_LEGACY_INDEX_MAP = {
    'table_standard': 0,
    'table_expert': 5,
    'change_standard': 1,
    'change_expert': 6,
    'filter_standard': 2,
    'filter_expert': 7,
    'sort_standard': 3,
    'sort_expert': 8,
    # Alte Namen (Kompatibilität)
    'search_standard': 2,
    'search_expert': 7,
}
# ========================================

class PdvmCentralSystemsteuerung(QObject):
    """
    Zentrale Systemsteuerung mit robuster Architektur
    
    Signals:
    - stichtag_changed(float): Emittiert bei Stichtag-Änderung
    """
    
    # Signal für Stichtag-Änderungen
    stichtag_changed = pyqtSignal(float)  # Neuer Stichtag-Wert
    
    def __init__(self, user_guid, user_data, mandant_guid, mandant_data):
        """
        V2.0 Initialisierung mit User UND Mandant
        
        Args:
            user_guid: User-GUID aus auth.db
            user_data: User-Daten aus auth.db (dict)
            mandant_guid: Mandanten-GUID aus auth.db (NEU!)
            mandant_data: Mandanten-Daten aus auth.db (dict, NEU!)
        """
        super().__init__()  # QObject initialisieren für Signals
        
        self._db = None
        self._user_guid = user_guid
        self._user_data = user_data
        self._mandant_guid = mandant_guid  # NEU!
        self._mandant_data = mandant_data  # NEU!
        self._st_inst = None
        self._temp_dt_inst = None  # Temporäre Pdvm_DateTime Instanz für Formatierungen
        self._dropdown_cache = {}  # Cache für geladene Dropdowns: {dropdown_name: {language: {key: value}}}
        self._initialized = False
        self._menu_containers = {}  # Container-Referenzen für autonomes Menü-System

        # ========================================================================
        # BASIS-SCHRIFTGRÖSSE: Zentral für alle Views (KEINE Akkumulation!)
        # ========================================================================
        # Systemweit einheitliche Schriftgrößen:
        # - base_font_size: Standard-Größe (z.B. 9pt von System)
        # - header_font_size: Header-Größe = Basis + 2pt
        # - group_font_size: Gruppierungs-Zeilen = Basis + 1pt
        from PyQt5.QtWidgets import QApplication
        app_font = QApplication.font()
        self.base_font_size = app_font.pointSize()  # System-Standard (z.B. 9pt)
        self.header_font_size = self.base_font_size + 2  # Header = Basis + 2pt
        self.group_font_size = self.base_font_size + 1   # Gruppen = Basis + 1pt
        logger.info(f"📏 Basis-Schriftgrößen: Standard={self.base_font_size}pt, Header={self.header_font_size}pt, Gruppen={self.group_font_size}pt")

        # PROJEKTIONS-TABELLEN ARRAY: 10-Positionen pro View
        # Struktur: {view_guid: [10 Listen]} - Positionen 0-4 Standard, 5-9 Expert
        # 0/5: View, 1/6: Change, 2/7: Filter, 3/8: Sort, 4/9: Reserviert
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

        # V2.0: DB-Pfad aus Mandantendaten ermitteln und als Property setzen
        from pathlib import Path
        mandant_id = self._mandant_data['METADATEN']['MANDANT_ID']
        self.db_path = str(Path(__file__).parent / "Daten" / mandant_id / "datenbank.db")
        logger.info(f"📂 V2.0: DB-Pfad gesetzt: {self.db_path}")

        # WICHTIG: Globale Instanz SOFORT setzen, damit PdvmDatenbank auf GCS zugreifen kann!
        global _gcs_instance
        _gcs_instance = self
        logger.info(f"✅ V2.0: Globale GCS-Instanz registriert (für DB-Zugriff)")

        # 2.1 Datenbank-Instanz für Benutzerstamm (fiktiv, OHNE GUID!)
        self._u_db = PdvmCentralDatenbank('benutzerstamm')
        self._u_db.set_data(self._user_data)  # Nur user_data, KEINE GUID!
        logger.info(f"✅ Benutzerdatenbank geladen (fiktiv, ohne GUID) mit {len(self._user_data)} Properties")

        # 2.2 Datenbank-Instanz für Systemsteuerung
        self._db = PdvmCentralDatenbank('sys_systemsteuerung', user_guid)
        logger.info(f"✅ Systemsteuerungsdatenbank geladen mit User-GUID: {user_guid}")
        
        # 2.3 Datenbank-Instanz für User-Anwendungsdaten (Filter, etc.)
        self._app_db = PdvmCentralDatenbank('sys_anwendungsdaten', user_guid)
        logger.info(f"✅ User-Anwendungsdatenbank geladen mit User-GUID: {user_guid}")
        
        # 2.4 Datenbank-Instanz für Mandanten-Anwendungsdaten (NEU in V2.0!)
        self._man_db = PdvmCentralDatenbank('sys_anwendungsdaten', mandant_guid)
        logger.info(f"✅ Mandanten-Anwendungsdatenbank geladen mit Mandant-GUID: {mandant_guid}")
        
        # 2.5 Datenbank-Instanz für System-Menü (sys_menudaten)
        # WICHTIG: Menü wird über UID aus sys_menudaten geladen
        # Standard: Admin-Startmenü (TODO: Aus User-Profil laden)
        start_menu_uid = '5ca6674e-b9ce-4581-9756-64e742883f80'  # Admin-Startmenü
        self._menu_system_db = PdvmCentralDatenbank('sys_menudaten', start_menu_uid, no_save=True)
        logger.info(f"✅ System-Menü-Datenbank geladen mit UID={start_menu_uid} (no_save=True - temporär für Rendering)")
        
        # Menu-Pipeline Instanzen (Lazy Initialization)
        self._menu_pipeline_vertikal = None
        self._menu_pipeline_grund = None
        self._menu_pipeline_zusatz = None

        # Stichtag-Instanz erstellen und initialisieren
        # V2.0: Country aus user_data holen (auth.db)
        country = self._user_data.get('country', 'DEU')
        logger.info(f"🌍 Country aus user_data: {country}")
        
        self._st_inst = Pdvm_DateTime(country)
        
        # NEUES ABDATUM-Instanz erstellen (systemweit wie Stichtag!)
        self._neues_abdatum_inst = Pdvm_DateTime(country)
        
        # Temporäre Pdvm_DateTime Instanz für Formatierungen erstellen
        self._temp_dt_inst = Pdvm_DateTime(country)
        logger.info(f"✅ Pdvm_DateTime Instanzen erstellt für Country: {country}")

        # Stichtag aus Systemsteuerung laden
        stored_stichtag = self._db.get_static_value(self.user_guid, 'stichtag') if user_guid in self._db.data and 'stichtag' in self._db.data[user_guid] else None
        
        # Prüfe ob Stichtag vorhanden UND gültig (NICHT Sentinel-Werte!)
        is_valid_stichtag = False
        if stored_stichtag is not None:
            try:
                stichtag_float = float(stored_stichtag)
                # SENTINEL-WERTE ABLEHNEN: 1001.0 und 9999365.0 sind NICHT gültig für Stichtag!
                if stichtag_float != 1001.0 and stichtag_float != 9999365.0 and stichtag_float > 0:
                    self._st_inst.PdvmDateTime = stichtag_float
                    is_valid_stichtag = True
                    logger.info(f"✅ Stichtag aus DB geladen: {self._st_inst.FormTimeStamp}")
                else:
                    logger.warning(f"⚠️ Ungültiger Stichtag (Sentinel): {stichtag_float}, verwende aktuellen Timestamp")
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Fehler beim Laden des Stichtags: {e}, verwende aktuellen Timestamp")
        
        # Kein gültiger Stichtag: Aktuellen Timestamp setzen und speichern
        if not is_valid_stichtag:
            current_timestamp = self._temp_dt_inst.PdvmDateTimeNow()
            self._st_inst.PdvmDateTime = current_timestamp
            self._db.set_value(user_guid, 'stichtag', current_timestamp)
            self._db.save_all_values()  # Sofort speichern!
            logger.info(f"💾 Stichtag auf aktuellen Timestamp gesetzt: {self._st_inst.FormTimeStamp}")
        
        # === NEUES ABDATUM aus Systemsteuerung laden (analog zu Stichtag) ===
        stored_neues_abdatum = self._db.get_static_value(self.user_guid, 'neues_abdatum') if user_guid in self._db.data and 'neues_abdatum' in self._db.data[user_guid] else None
        
        # Prüfe ob Neues Abdatum vorhanden UND gültig
        is_valid_neues_abdatum = False
        if stored_neues_abdatum is not None:
            try:
                neues_abdatum_float = float(stored_neues_abdatum)
                # Sentinels sind hier ERLAUBT (können explizit gesetzt werden)
                if neues_abdatum_float > 0:
                    self._neues_abdatum_inst.PdvmDateTime = neues_abdatum_float
                    is_valid_neues_abdatum = True
                    logger.info(f"✅ Neues Abdatum aus DB geladen: {self._neues_abdatum_inst.FormTimeStamp}")
                else:
                    logger.warning(f"⚠️ Ungültiges Neues Abdatum: {neues_abdatum_float}, verwende aktuellen Timestamp")
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Fehler beim Laden des Neuen Abdatums: {e}, verwende aktuellen Timestamp")
        
        # Kein gültiges Neues Abdatum: Aktuellen Timestamp setzen und speichern
        if not is_valid_neues_abdatum:
            current_timestamp = self._temp_dt_inst.PdvmDateTimeNow()
            self._neues_abdatum_inst.PdvmDateTime = current_timestamp
            self._db.set_value(user_guid, 'neues_abdatum', current_timestamp)
            self._db.save_all_values()  # Sofort speichern!
            logger.info(f"💾 Neues Abdatum auf aktuellen Timestamp gesetzt: {self._neues_abdatum_inst.FormTimeStamp}")

        # V2.0: Mandanten-Daten NACH Initialisierung der DateTime-Instanzen abgleichen
        self._sync_mandant_data()
        
        # === VERSION aus Systemsteuerung laden oder initialisieren ===
        stored_version = self._db.get_static_value(self.user_guid, 'version') if user_guid in self._db.data and 'version' in self._db.data[user_guid] else None
        
        if stored_version is None:
            # Initial Version 0.9 setzen
            self._version = "0.9"
            self._db.set_value(user_guid, 'version', "0.9")
            self._db.save_all_values()
            logger.info(f"💾 Version initial gesetzt: {self._version}")
        else:
            self._version = str(stored_version)
            logger.info(f"✅ Version aus DB geladen: {self._version}")
        
        self._initialized = True
        logger.info(f"✅ Systemsteuerung initialisiert für {user_guid}")
        logger.info(f"📅 Stichtag: {self._st_inst.FormTimeStamp}")
        logger.info(f"📅 Neues Abdatum: {self._neues_abdatum_inst.FormTimeStamp}")
        logger.info(f"🚀 PDVM-SYSTEM Version: {self._version}")
    
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
    
    def set_menu_system_db_guid(self, menu_guid):
        """
        Lädt Menü-Datenbank mit neuer GUID.
        
        WICHTIG: no_save=True → Menü wird nur temporär für Rendering geladen!
        
        Args:
            menu_guid: GUID des zu ladenden Menüs
        """
        logger.info(f"🔄 Lade Menü-Datenbank mit GUID: {menu_guid}")
        self._menu_system_db = PdvmCentralDatenbank('sys_menudaten', menu_guid, no_save=True)
        logger.info(f"✅ Menü-Datenbank geladen (no_save=True)")
    
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
            
            # ⭐ KORREKTUR: App-Name zu Großbuchstaben für Lookup
            app_name_upper = app_name.upper()
            logger.debug(f"🔍 Suche Menü für App: '{app_name}' → '{app_name_upper}'")
            
            # Für andere Apps: Suche in ANWENDUNGEN (Großbuchstaben!) -> APP_NAME (Großbuchstaben!)
            app_data = self.get_property(app_name_upper, 'u', 'ANWENDUNGEN')
            
            # ⭐ KORREKTUR: MENU statt Menu (Großbuchstaben!)
            if isinstance(app_data, dict):
                menu_id = app_data.get('MENU')
            else:
                menu_id = None
            
            logger.debug(f"✅ Menü-ID für '{app_name}': {menu_id}")
            return menu_id
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen der Menü-ID für App '{app_name}': {e}")
            import traceback
            traceback.print_exc()
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
            # Getter - Spezielle Properties verwenden @property statt DB-Zugriff
            if property_name == 'stichtag':
                return self._st_inst.PdvmDateTime if self._st_inst else None
            elif property_name == 'country':
                return self.country  # Verwende @property (liest aus _user_data)
            elif property_name == 'mode':
                return self.mode  # Verwende @property (liest aus _user_data)
            elif property_name == 'language':
                return self.language  # Verwende @property (liest aus _user_data)
            else:
                return self.get_property(property_name, 's')
        else:
            # Setter
            if property_name == 'stichtag':
                if self._st_inst:
                    self._st_inst.PdvmDateTime = float(value)
                    # Speichere direkt über DB-Instanz
                    self._db.set_value(self._user_guid, 'stichtag', value)
            else:
                self.set_property(property_name, value)
            return None
    
    def register_menu_containers(self, vertical=None, grund=None, zusatz=None):
        """
        Registriert Container-Referenzen für autonomes Menü-System.
        
        Args:
            vertical: QWidget Container für vertikales Menü
            grund: QWidget Container für Grund-Menü
            zusatz: QWidget Container für Zusatz-Menü
            
        Returns:
            None
        """
        if vertical:
            self._menu_containers['vertical'] = vertical
            logger.info("✅ Vertikaler Menu-Container registriert")
        if grund:
            self._menu_containers['grund'] = grund
            logger.info("✅ Grund Menu-Container registriert")
        if zusatz:
            self._menu_containers['zusatz'] = zusatz
            logger.info("✅ Zusatz Menu-Container registriert")
        
        logger.info(f"📦 {len(self._menu_containers)}/3 Menu-Container in GCS registriert")
    
    def get_container(self, name):
        """
        Holt registrierten Container.
        
        Args:
            name: Container-Name ('vertical_menu_container', 'grund_menu_container', 'zusatz_menu_container')
        
        Returns:
            QWidget oder None
        """
        # Mapping von alten Namen zu neuen Namen
        name_mapping = {
            'vertical_menu_container': 'vertical',
            'grund_menu_container': 'grund',
            'zusatz_menu_container': 'zusatz'
        }
        
        container_key = name_mapping.get(name, name)
        container = self._menu_containers.get(container_key)
        
        if not container:
            logger.warning(f"⚠️ Container '{name}' nicht gefunden!")
        
        return container
    
    # ========================================
    # ZUSATZMENÜ-VERWALTUNG (LINEAR & EINFACH)
    # ========================================
    
    def expand_templates_in_gruppe(self, gruppe: str):
        """
        Expandiert Templates DIREKT IN GCS-Datenbank (no_save=True).
        
        LINEARER ABLAUF:
        1. Lade Gruppe aus GCS
        2. Finde SPACER mit template_guid
        3. Lade Template-Items
        4. Ersetze SPACER durch erstes Template-Item (SUBMENU)
        5. Füge restliche Template-Items ein
        6. Schreibe ALLES zurück in GCS
        
        Args:
            gruppe: Menü-Gruppe (GRUND, VERTIKAL, ZUSATZ)
        """
        logger.info(f"🔧 Expandiere Templates in {gruppe}...")
        
        try:
            # 1. Gruppe aus GCS laden
            gruppe_data = self._menu_system_db.get_gruppe(gruppe)
            if not gruppe_data or not isinstance(gruppe_data, dict):
                logger.debug(f"  ℹ️ Gruppe {gruppe} leer oder ungültig")
                return
            
            # 2. SPACER mit template_guid finden
            import json
            spacers_to_expand = []
            
            for guid, item_value in gruppe_data.items():
                try:
                    if isinstance(item_value, str):
                        item_data = json.loads(item_value)
                    else:
                        item_data = item_value
                    
                    if (isinstance(item_data, dict) and 
                        item_data.get('type') == 'SPACER' and 
                        item_data.get('template_guid')):
                        spacers_to_expand.append({
                            'guid': guid,
                            'data': item_data,
                            'template_guid': item_data['template_guid']
                        })
                except:
                    continue
            
            if not spacers_to_expand:
                logger.debug(f"  ℹ️ Keine Templates in {gruppe}")
                return
            
            logger.info(f"  🎯 {len(spacers_to_expand)} Template(s) gefunden")
            
            # 3. Für jeden SPACER: Template expandieren
            for spacer_info in spacers_to_expand:
                spacer_guid = spacer_info['guid']
                spacer_data = spacer_info['data']
                template_guid = spacer_info['template_guid']
                
                logger.info(f"    🔄 Expandiere Template: {template_guid}")
                
                # Template-Items aus sys_menudaten laden
                from pdvm_central_datenbank import PdvmCentralDatenbank
                template_db = PdvmCentralDatenbank('sys_menudaten', template_guid)
                template_data = template_db.get_value_by_group(gruppe)
                
                if not template_data:
                    logger.warning(f"      ⚠️ Kein Template in {gruppe} für {template_guid}")
                    continue
                
                # Template-Items parsen
                template_items = []
                for item_guid, item_value in template_data.items():
                    try:
                        if isinstance(item_value, str):
                            item_data = json.loads(item_value)
                        else:
                            item_data = item_value
                        
                        if isinstance(item_data, dict):
                            item_data['guid'] = item_guid
                            template_items.append(item_data)
                    except:
                        continue
                
                if not template_items:
                    logger.warning(f"      ⚠️ Template {template_guid} hat keine Items")
                    continue
                
                # Sortieren nach sort_order
                template_items.sort(key=lambda x: x.get('sort_order', 0))
                
                # 4. Erstes Item muss SUBMENU sein
                first_item = template_items[0]
                if first_item.get('type') != 'SUBMENU':
                    logger.warning(f"      ⚠️ Erstes Template-Item ist kein SUBMENU")
                    continue
                
                # Übernehme parent_guid und sort_order vom SPACER
                first_item['parent_guid'] = spacer_data.get('parent_guid')
                first_item['sort_order'] = spacer_data.get('sort_order', 0)
                
                logger.info(f"      ✅ Ersetze SPACER {spacer_guid} mit SUBMENU {first_item['guid']}")
                
                # 5. SPACER durch erstes Item ersetzen IN GCS!
                first_item_json = json.dumps(first_item, ensure_ascii=False)
                self._menu_system_db.set_value(gruppe, first_item['guid'], first_item_json)
                
                # SPACER aus GCS löschen
                self._menu_system_db.set_value(gruppe, spacer_guid, None)
                
                # 6. Restliche Template-Items einfügen IN GCS!
                for item in template_items[1:]:
                    item_json = json.dumps(item, ensure_ascii=False)
                    self._menu_system_db.set_value(gruppe, item['guid'], item_json)
                    logger.debug(f"      📎 Template-Item hinzugefügt: {item['guid']}")
                
                logger.info(f"      ✅ {len(template_items)} Template-Items in GCS geschrieben")
            
            logger.info(f"  ✅ Templates in {gruppe} expanded (in GCS!)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Expandieren von Templates in {gruppe}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def prepare_menu_with_zusatz(self):
        """
        Bereitet Menü-Struktur vor: Templates + Zusatzmenü-GUIDs eintragen.
        
        LINEARER ABLAUF:
        1. Templates in Struktur übernehmen (falls vorhanden)
        2. Zusatzmenüs verteilen: Von ZUSATZ-Gruppe ausgehend, GUIDs in Items eintragen
        3. Nach Hierarchie: Parent → Children Vererbung
        
        Arbeitet direkt auf self._menu_system_db (no_save=True, wird nicht persistent!)
        """
        logger.info("🔧 Bereite Menü-Struktur vor (Templates + Zusatzmenüs)...")
        
        # SCHRITT 1: ZUSATZ-Gruppe laden
        try:
            zusatz_gruppe = self._menu_system_db.get_gruppe('ZUSATZ')
            if not isinstance(zusatz_gruppe, dict):
                logger.info("  📋 Keine ZUSATZ-Gruppe vorhanden")
                return
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der ZUSATZ-Gruppe: {e}")
            return
        
        logger.info(f"  ✅ ZUSATZ-Gruppe geladen: {len(zusatz_gruppe)} Einträge")
        
        # SCHRITT 2: Root-SUBMENUs identifizieren (parent_guid=null, type=SUBMENU)
        zusatz_roots = {}
        for guid, item_data in zusatz_gruppe.items():
            if (item_data.get('type') == 'SUBMENU' 
                and item_data.get('parent_guid') is None):
                zusatz_roots[guid] = item_data
                logger.debug(f"    📎 Zusatzmenü gefunden: {guid} → {item_data.get('label')}")
        
        if not zusatz_roots:
            logger.info("  📋 Keine Zusatzmenüs definiert (keine Root-SUBMENUs)")
            return
        
        logger.info(f"  ✅ {len(zusatz_roots)} Zusatzmenü(s) gefunden")
        
        # SCHRITT 3: Zusatzmenü-GUIDs in Menü-Items eintragen (VERTIKAL + GRUND)
        for gruppe_name in ['VERTIKAL', 'GRUND']:
            try:
                gruppe = self._menu_system_db.get_gruppe(gruppe_name)
                if not isinstance(gruppe, dict):
                    continue
                
                logger.info(f"  🔧 Verarbeite {gruppe_name}-Gruppe...")
                
                # Für jedes Zusatzmenü: Wenn Item-GUID == Zusatzmenü-GUID, eintragen
                for zusatz_guid in zusatz_roots.keys():
                    if zusatz_guid in gruppe:
                        # Item hat Zusatzmenü!
                        item = gruppe[zusatz_guid]
                        item['zusatz_guid'] = zusatz_guid
                        logger.info(f"    📎 Zusatzmenü verknüpft: {item.get('label')} → {zusatz_guid}")
                        
                        # Vererbung: An alle Children weitergeben (rekursiv)
                        self._propagate_zusatz_to_children(gruppe, zusatz_guid, zusatz_guid)
                
            except Exception as e:
                logger.error(f"❌ Fehler bei {gruppe_name}: {e}")
        
        logger.info("✅ Menü-Struktur vorbereitet (Templates + Zusatzmenüs)")
    
    def _propagate_zusatz_to_children(self, gruppe: dict, parent_guid: str, zusatz_guid: str):
        """
        Vererbt Zusatzmenü-GUID rekursiv an alle Children.
        
        Args:
            gruppe: Menu-Gruppe (dict)
            parent_guid: GUID des Parents
            zusatz_guid: GUID des Zusatzmenüs (wird vererbt)
        """
        # Alle Children finden
        children = [
            (guid, item) for guid, item in gruppe.items()
            if item.get('parent_guid') == parent_guid
        ]
        
        for child_guid, child_item in children:
            # Nur setzen wenn noch nicht vorhanden (eigenes überschreibt Vererbung)
            if 'zusatz_guid' not in child_item:
                child_item['zusatz_guid'] = zusatz_guid
                logger.debug(f"      🔗 Vererbt an: {child_item.get('label')} → {zusatz_guid}")
            
            # Rekursiv an Enkel-Children weitergeben
            self._propagate_zusatz_to_children(gruppe, child_guid, child_item.get('zusatz_guid', zusatz_guid))
    
    def build_zusatzmenu_mapping(self, menu_matrix: list) -> dict:
        """
        Baut Zusatzmenü-Zuordnung mit Vererbungslogik bei Menü-Load auf.
        
        Temporäre Instanz die bei jedem Haupt-Menüwechsel neu aufgebaut wird.
        Ordnet jedem Item-GUID das zuständige Zusatzmenü-GUID zu (mit Vererbung).
        
        Args:
            menu_matrix: Komplette Menu-Matrix (VERTIKAL oder GRUND)
        
        Returns:
            dict: {item_guid: zusatzmenu_guid} Mapping
        """
        mapping = {}
        
        # ZUSATZ-Gruppe einmal laden für Performance
        try:
            zusatz_gruppe = self._menu_system_db.get_gruppe('ZUSATZ')
            if not isinstance(zusatz_gruppe, dict):
                zusatz_gruppe = {}
        except:
            zusatz_gruppe = {}
        
        # Rekursive Funktion für Vererbung
        def process_item(item, inherited_zusatz_guid=None):
            """
            Verarbeitet Item und Kinder mit Vererbungslogik.
            
            Args:
                item: Menu-Item Dict
                inherited_zusatz_guid: Von Parent vererbtes Zusatzmenü
            """
            item_guid = item.get('guid')
            if not item_guid:
                return
            
            # Hat Item eigenes Zusatzmenü?
            # Zusatzmenü existiert wenn Root-SUBMENU mit item_guid in ZUSATZ-Gruppe vorhanden
            zusatz_root = zusatz_gruppe.get(item_guid)
            has_zusatzmenu = (
                zusatz_root is not None 
                and zusatz_root.get('type') == 'SUBMENU'
                and zusatz_root.get('parent_guid') is None
            )
            
            if has_zusatzmenu:
                # Eigenes Zusatzmenü vorhanden → verwenden
                current_zusatz = item_guid
                logger.debug(f"  📎 Item '{item.get('label')}' hat eigenes Zusatzmenü: {item_guid}")
            else:
                # Kein eigenes → vererbt von Parent
                current_zusatz = inherited_zusatz_guid
                if current_zusatz:
                    logger.debug(f"  🔗 Item '{item.get('label')}' erbt Zusatzmenü: {current_zusatz}")
            
            # Mapping speichern
            if current_zusatz:
                mapping[item_guid] = current_zusatz
            
            # Kinder verarbeiten (mit Vererbung)
            children = [child for child in menu_matrix if child.get('parent_guid') == item_guid]
            for child in children:
                process_item(child, current_zusatz)
        
        # Root-Items finden und verarbeiten
        root_items = [item for item in menu_matrix if item.get('parent_guid') is None]
        for root_item in root_items:
            process_item(root_item, None)
        
        logger.info(f"✅ Zusatzmenü-Mapping erstellt: {len(mapping)} Items mit Zusatzmenüs")
        return mapping
    
    def get_zusatzmenu_for_item(self, item_guid: str, zusatz_mapping: dict) -> str:
        """
        Ermittelt Zusatzmenü-GUID für Item aus vorgefertigtem Mapping.
        
        Args:
            item_guid: GUID des geklickten Items
            zusatz_mapping: Mapping aus build_zusatzmenu_mapping()
        
        Returns:
            Zusatzmenü-GUID oder None
        """
        return zusatz_mapping.get(item_guid)
    
    def load_zusatzmenu_data(self, zusatzmenu_guid: str) -> list:
        """
        Lädt Zusatzmenü-Daten aus ZUSATZ-Gruppe.
        
        Die ZUSATZ-Gruppe enthält für jedes Zusatzmenü:
        - Root-SUBMENU mit GUID = zusatzmenu_guid (parent_guid=null)
        - Children des Root-SUBMENU (parent_guid = zusatzmenu_guid)
        
        Beim Rendern wird das Root-SUBMENU übersprungen,
        nur die Children werden horizontal angezeigt.
        
        Args:
            zusatzmenu_guid: GUID des Zusatzmenüs (= Item-GUID aus Hauptmenü)
        
        Returns:
            list: Menu-Matrix mit NUR den Children (ohne Root-SUBMENU)
        """
        if not zusatzmenu_guid:
            return []
        
        try:
            # Gesamte ZUSATZ-Gruppe laden
            zusatz_gruppe = self._menu_system_db.get_gruppe('ZUSATZ')
            
            if not zusatz_gruppe or not isinstance(zusatz_gruppe, dict):
                logger.warning(f"⚠️ ZUSATZ-Gruppe leer oder ungültig")
                return []
            
            # Root-SUBMENU suchen
            root_submenu = zusatz_gruppe.get(zusatzmenu_guid)
            if not root_submenu:
                logger.warning(f"⚠️ Zusatzmenü nicht gefunden: {zusatzmenu_guid}")
                return []
            
            if root_submenu.get('type') != 'SUBMENU' or root_submenu.get('parent_guid') is not None:
                logger.warning(f"⚠️ Ungültiges Root-SUBMENU: {zusatzmenu_guid}")
                return []
            
            # Children des Root-SUBMENU sammeln (rekursiv für Hierarchie)
            menu_matrix = []
            
            def collect_children(parent_guid):
                """Sammelt alle Nachkommen rekursiv"""
                for guid, item_data in zusatz_gruppe.items():
                    if item_data.get('parent_guid') == parent_guid:
                        # Item zur Matrix hinzufügen
                        item_copy = item_data.copy()
                        item_copy['guid'] = guid
                        menu_matrix.append(item_copy)
                        
                        # Rekursiv Kinder sammeln
                        if item_data.get('type') == 'SUBMENU':
                            collect_children(guid)
            
            # Children des Root-SUBMENU sammeln (nicht Root selbst!)
            collect_children(zusatzmenu_guid)
            
            logger.info(f"✅ Zusatzmenü geladen: {zusatzmenu_guid} ({len(menu_matrix)} Items)")
            return menu_matrix
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von Zusatzmenü {zusatzmenu_guid}: {e}", exc_info=True)
            return []
    
    # ========================================
    
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
        
        # PERSISTENT SPEICHERN (war vorher vergessen!)
        self._db.save_all_values()
        
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
        
        Emittiert Signal 'stichtag_changed' nach erfolgreicher Aktualisierung.
        """
        self._ensure_initialized()
        if self._st_inst and self._db:
            current_stichtag = self._st_inst.PdvmDateTime
            # Speichere in Systemsteuerung-DB
            self._db.set_value(self._user_guid, 'stichtag', current_stichtag)
            # Persistiere alle Änderungen
            self._db.save_all_values()
            logger.info(f"💾 Stichtag in finale GCS gespeichert: {current_stichtag} ({self._st_inst.FormTimeStamp})")
            
            # 🔔 Signal emittieren für alle verbundenen Views
            self.stichtag_changed.emit(current_stichtag)
            logger.info(f"🔔 Signal 'stichtag_changed' emittiert: {current_stichtag}")
        else:
            logger.error("❌ Kann Stichtag nicht speichern - st_inst oder db nicht verfügbar")
    
    # ========================================================================
    # NEUES ABDATUM PROPERTIES & METHODEN (analog zu Stichtag)
    # ========================================================================
    
    @property
    def neues_abdatum_inst(self):
        """Neues Abdatum-Instanz für DateTimePicker (systemweit!)"""
        self._ensure_initialized()
        return self._neues_abdatum_inst
    
    @property
    def neues_abdatum(self):
        """Neues Abdatum als Float-Wert (direkter Zugriff)"""
        self._ensure_initialized()
        return self._neues_abdatum_inst.PdvmDateTime if self._neues_abdatum_inst else None
    
    def update_neues_abdatum(self):
        """
        Aktualisiert das Neue Abdatum in der Datenbank aus der aktuellen neues_abdatum_inst.
        
        Diese Methode liest den aktuellen Wert aus self._neues_abdatum_inst.PdvmDateTime
        und speichert ihn in der Systemsteuerungsdatenbank.
        
        VERWENDUNG: Nach Änderungen im DateTimePicker (analog zu update_stichtag())
        """
        self._ensure_initialized()
        if self._neues_abdatum_inst and self._db:
            current_neues_abdatum = self._neues_abdatum_inst.PdvmDateTime
            # Speichere in Systemsteuerung-DB unter user_guid.neues_abdatum
            self._db.set_value(self._user_guid, 'neues_abdatum', current_neues_abdatum)
            # Persistiere alle Änderungen
            self._db.save_all_values()
            logger.info(f"💾 Neues Abdatum in GCS gespeichert: {current_neues_abdatum} ({self._neues_abdatum_inst.FormTimeStamp})")
        else:
            logger.error("❌ Kann Neues Abdatum nicht speichern - neues_abdatum_inst oder db nicht verfügbar")
    
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
        """Country aus Benutzerdaten (SETTINGS Gruppe, UPPERCASE Felder)"""
        self._ensure_initialized()
        try:
            # V2 verwendet SETTINGS Gruppe mit UPPERCASE Feldnamen
            settings_data = self._user_data.get('SETTINGS', {})
            country_value = settings_data.get('COUNTRY', None)
            
            # Fallback für V1-Kompatibilität (lowercase in Parameter Gruppe)
            if country_value is None:
                parameter_data = self._user_data.get('Parameter', {})
                country_value = parameter_data.get('country', 'DEU')
            
            return country_value if country_value else 'DEU'
        except (KeyError, AttributeError, TypeError):
            return 'DEU'
    
    @property
    def language(self):
        """Language aus Benutzerdaten (SETTINGS Gruppe, UPPERCASE Felder)"""
        self._ensure_initialized()
        try:
            # V2 verwendet SETTINGS Gruppe mit UPPERCASE Feldnamen
            settings_data = self._user_data.get('SETTINGS', {})
            language_value = settings_data.get('LANGUAGE', None)
            
            # Fallback für V1-Kompatibilität (lowercase in Parameter Gruppe)
            if language_value is None:
                parameter_data = self._user_data.get('Parameter', {})
                language_value = parameter_data.get('language', 'de-de')
            
            return language_value if language_value else 'de-de'
        except (KeyError, AttributeError, TypeError):
            return 'de-de'
    
    @property
    def mode(self):
        """Mode aus Benutzerdaten (SETTINGS Gruppe, UPPERCASE Felder) - 'user' oder 'admin'"""
        self._ensure_initialized()
        try:
            # V2 verwendet SETTINGS Gruppe mit UPPERCASE Feldnamen
            settings_data = self._user_data.get('SETTINGS', {})
            mode_value = settings_data.get('MODE', None)
            
            # Fallback für V1-Kompatibilität (lowercase in Parameter Gruppe)
            if mode_value is None:
                parameter_data = self._user_data.get('Parameter', {})
                mode_value = parameter_data.get('mode', 'user')
            
            # Default falls nichts gefunden
            if mode_value is None:
                mode_value = 'user'
            
            # Validiere Wert: nur 'user' oder 'admin' erlaubt
            if mode_value not in ['user', 'admin']:
                logger.warning(f"⚠️ Ungültiger mode Wert '{mode_value}', verwende 'user' als Fallback")
                return 'user'
            
            logger.info(f"✅ Mode erfolgreich gelesen: '{mode_value}' aus SETTINGS.MODE")
            return mode_value
        except (KeyError, AttributeError, TypeError) as e:
            logger.warning(f"⚠️ mode nicht gefunden in Benutzerdaten: {e}, verwende 'user' als Fallback")
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
    
    @property
    def version(self):
        """PDVM-System Version (zentral verwaltet in GCS)"""
        self._ensure_initialized()
        return self._version
    
    @version.setter
    def version(self, value):
        """Version setzen und persistieren"""
        self._ensure_initialized()
        self._version = str(value)
        self._db.set_value(self.user_guid, 'version', str(value))
        self._db.save_all_values()
        logger.info(f"💾 Version aktualisiert: {self._version}")
    
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
            # Dropdown aus Datenbank laden - KORREKT: sys_dropdowndaten
            dropdown_db = PdvmCentralDatenbank(
                table_name="sys_dropdowndaten",
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

    def get_projection_table(self, view_guid: str, index_or_name: Union[int, str] = 0):
        """
        ✅ ARRAY-BASIERTES PROJEKTIONS-TABELLEN SYSTEM
        
        Gibt die vorberechneten Projektions-Listen zurück aus dem 10-Positionen Array.
        Diese werden nur beim Speichern der Controls neu aufgebaut, ansonsten statisch verwendet.

        Args:
            view_guid: GUID der View
            index_or_name: Integer (0-9) für Array-Zugriff ODER String für Legacy-Kompatibilität
                          0/5: View, 1/6: Change, 2/7: Filter, 3/8: Sort, 4/9: Reserviert
                          Expert Mode = Standard + 5

        Returns:
            list: Statische Liste der Spalten-Keys für den entsprechenden Zweck
        """
        try:
            # Prüfe ob Projektions-Tabellen für diese View existieren
            if view_guid not in self._projection_tables:
                logger.info(f"🔧 Erstelle initiale Projektions-Tabellen für View {view_guid}")
                self._build_projection_tables(view_guid)
            
            # Legacy-Kompatibilität: String → Integer-Index
            if isinstance(index_or_name, str):
                index = _LEGACY_INDEX_MAP.get(index_or_name)
                if index is None:
                    logger.warning(f"⚠️ Unbekannter Projektions-Name: {index_or_name}")
                    return []
                logger.debug(f"🔄 Legacy-String '{index_or_name}' → Index {index}")
            else:
                index = index_or_name
            
            # Validiere Index
            if not (0 <= index < 10):
                logger.error(f"❌ Ungültiger Projektions-Index: {index} (muss 0-9 sein)")
                return []
            
            # Hole Array für View
            view_tables = self._projection_tables.get(view_guid)
            if not view_tables or len(view_tables) != 10:
                logger.warning(f"⚠️ Projektions-Array für {view_guid} nicht vollständig")
                return []
            
            # Array-Zugriff
            projection = view_tables[index]
            
            if projection:
                logger.debug(f"✅ Projektion Index {index} für {view_guid}: {len(projection)} Spalten")
                return projection.copy()  # Kopie für Unveränderlichkeit
            else:
                logger.warning(f"⚠️ Leere Projektion an Index {index} für View {view_guid}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Fehler bei get_projection_table({view_guid}, {index_or_name}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _build_projection_tables(self, view_guid: str):
        """
        Baut das 10-Positionen Array für statische Projektions-Tabellen auf.
        Wird nur aufgerufen nach Controls-Speicherung oder bei erster Verwendung.
        
        Array-Struktur:
        - 0/5: View (table_standard/expert)
        - 1/6: Change (change_standard/expert) - Spalten verwalten
        - 2/7: Filter (filter_standard/expert)
        - 3/8: Sort (sort_standard/expert)
        - 4/9: Reserviert
        
        KORREKTE REGELN:
        1. View Standard (0): Alle mit show=true, Sortierung: display_order
        2. View Expert (5): Alle außer dummy+row_type, Sortierung: expert_order
        3. Change Standard (1): Alle mit expert_mode=false, Sortierung: display_sort
        4. Change Expert (6): Alle außer dummy+row_type, Sortierung: expert_order
        5. Filter Standard/Expert (2/7): Bestehend beibehalten
        
        Args:
            view_guid: GUID der View
        """
        try:
            # Controls aus Datenbank laden
            controls, _ = self.db.get_value(view_guid, "controls")
            if not controls:
                logger.warning(f"⚠️ Keine Controls für View {view_guid} - erstelle leeres Array")
                self._projection_tables[view_guid] = [[] for _ in range(10)]  # 10 leere Listen
                return
            
            logger.info(f"🏗️ Baue Projektions-Array für View {view_guid} mit {len(controls)} Controls")
            
            # Analysiere alle Controls
            excluded_controls = []  # dummy + row_type
            all_controls = []
            non_expert_controls = []  # Spalten die NICHT expert_mode=True haben
            
            for control_key, control_data in controls.items():
                # Exclusion-Check: dummy ODER row_type
                control_type = control_data.get('type') or control_data.get('control_type', '')
                is_dummy = (control_type == 'dummy' or 
                           control_data.get('dummy', False) or 
                           control_key.lower().startswith('dummy'))
                is_row_type = (control_key == 'row_type')
                
                if is_dummy or is_row_type:
                    excluded_controls.append(control_key)
                else:
                    control_info = {
                        'key': control_key,
                        'display_order': control_data.get('display_order', 999),
                        'display_sort': control_data.get('display_sort', 999),  # ⭐ NEU für Change Standard
                        'expert_order': control_data.get('expert_order', 999),
                        'show': control_data.get('show', False),
                        'expert_mode': control_data.get('expert_mode', False),
                        'sortable': control_data.get('sortable', False),
                        'filterable': control_data.get('filterable', False)
                    }
                    
                    all_controls.append(control_info)
                    
                    # Prüfe Expert Mode Flag - nur Spalten die NICHT expert_mode=True sind
                    if not control_data.get('expert_mode', False):
                        non_expert_controls.append(control_info)
            
            # Sortierte Listen erstellen nach KORREKTEN Regeln
            # 1. View Standard: show=true, sort by display_order
            visible_by_display = sorted(
                [c for c in all_controls if c['show']], 
                key=lambda x: x['display_order']
            )
            
            # 2. View Expert: alle (außer excluded), sort by expert_order
            all_by_expert = sorted(all_controls, key=lambda x: x['expert_order'])
            
            # 3. Change Standard: expert_mode=false, sort by display_sort ⭐ KORRIGIERT
            non_expert_by_display_sort = sorted(
                non_expert_controls, 
                key=lambda x: x['display_sort']
            )
            
            # 4. Change Expert: alle (außer excluded), sort by expert_order (gleich wie View Expert)
            
            # ARRAY-SYSTEM: 10 Projektions-Tabellen
            # Positionen 0-4: Standard Mode | Positionen 5-9: Expert Mode (+5)
            tables = [None] * 10
            
            # ========================================================================
            # STANDARD MODE (0-4)
            # ========================================================================
            
            # Position 0: View Standard - Alle mit show=true, Sortierung: display_order ✅
            tables[0] = [c['key'] for c in visible_by_display]
            
            # Position 1: Change Standard - Alle mit expert_mode=false, Sortierung: display_sort ⭐ KORRIGIERT
            tables[1] = [c['key'] for c in non_expert_by_display_sort]
            
            # Position 2: Filter Standard - Alle sichtbaren Spalten (BEIBEHALTEN)
            tables[2] = [c['key'] for c in visible_by_display]
            
            # Position 3: Sort Standard - Alle sichtbaren Spalten (BEIBEHALTEN)
            tables[3] = [c['key'] for c in visible_by_display]
            
            # Position 4: Reserviert
            tables[4] = []
            
            # ========================================================================
            # EXPERT MODE (5-9)
            # ========================================================================
            
            # Position 5: View Expert - Alle außer dummy+row_type, Sortierung: expert_order ✅
            tables[5] = [c['key'] for c in all_by_expert]
            
            # Position 6: Change Expert - Alle außer dummy+row_type, Sortierung: expert_order ✅
            tables[6] = [c['key'] for c in all_by_expert]
            
            # Position 7: Filter Expert - Alle Controls (BEIBEHALTEN)
            tables[7] = [c['key'] for c in all_by_expert]
            
            # Position 8: Sort Expert - Alle Controls (BEIBEHALTEN)
            tables[8] = [c['key'] for c in all_by_expert]
            
            # Position 9: Reserviert
            tables[9] = []
            
            # Speichere Array
            self._projection_tables[view_guid] = tables
            
            logger.info(f"✅ ARRAY-BASIERTE Projektions-Tabellen für {view_guid} erstellt:")
            logger.info(f"  [0] 📊 View Standard: {len(tables[0])} Spalten (show=true, display_order)")
            logger.info(f"  [1] � Change Standard: {len(tables[1])} Spalten (nicht expert_mode, display_order)")
            logger.info(f"  [2] 🔍 Filter Standard: {len(tables[2])} Spalten (sichtbar + filterbar)")
            logger.info(f"  [3] 🔄 Sort Standard: {len(tables[3])} Spalten (aus Change, nur sortierbar) ⭐ NEU")
            logger.info(f"  [4] ⏸️  Reserviert: {len(tables[4])} Spalten")
            logger.info(f"  [5] 📊 View Expert: {len(tables[5])} Spalten (alle außer dummy, expert_order)")
            logger.info(f"  [6] 🔧 Change Expert: {len(tables[6])} Spalten (alle außer dummy, expert_order)")
            logger.info(f"  [7] � Filter Expert: {len(tables[7])} Spalten (alle filterbar)")
            logger.info(f"  [8] 🔄 Sort Expert: {len(tables[8])} Spalten (aus Change, nur sortierbar) ⭐ NEU")
            logger.info(f"  [9] ⏸️  Reserviert: {len(tables[9])} Spalten")
            logger.info(f"  ❌ Excluded: {len(excluded_controls)} (dummy + row_type) ⭐ KORRIGIERT")
            logger.info(f"  📋 Non-Expert: {len(non_expert_controls)} (für Change Standard)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der Projektions-Tabellen für {view_guid}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: 10 leere Listen
            self._projection_tables[view_guid] = [[] for _ in range(10)]
    
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
        LEGACY: ProjectionMatrix-Instanz für View holen
        HINWEIS: Wird durch Array-basiertes System ersetzt (siehe get_projection_table)
        """
        logger.warning(f"⚠️ LEGACY: get_projection_matrix() aufgerufen - sollte get_projection_table() verwenden!")
        
        # Initialisiere Cache falls nicht vorhanden
        if not hasattr(self, '_projection_matrices'):
            self._projection_matrices = {}  # Cache für ProjectionMatrix-Instanzen

        if view_guid not in self._projection_matrices:
            # Erstelle Dummy-Objekt mit load_from_gcs Methode
            class LegacyProjectionMatrix:
                def load_from_gcs(self):
                    return False
            
            self._projection_matrices[view_guid] = LegacyProjectionMatrix()
            logger.warning(f"⚠️ Legacy ProjectionMatrix-Dummy erstellt für View {view_guid}")

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
    
    # ========================================
    # V2.0 MANDANTEN-DATEN ABGLEICH
    # ========================================
    
    def _sync_mandant_data(self):
        """
        Gleicht Mandanten-Daten aus auth.db mit man_db ab
        
        LINEAR:
        1. set_data(mandant_data) → Überschreibt alle Daten
        2. set_value() für Zusatz-Felder (DB_PATH, LETZTER_LOGIN)
        3. save_all_values() → Fertig!
        """
        try:
            # Aktuellen Zeitstempel
            letzter_login = self._st_inst.PdvmDateTimeNow()
            
            # DB-Pfad ermitteln
            from pathlib import Path
            mandant_id = self._mandant_data['METADATEN']['MANDANT_ID']
            base_path = Path(__file__).parent / "Daten" / mandant_id
            db_path = str(base_path / "datenbank.db")
            
            # 1. Mandanten-Daten aus auth.db überschreiben
            self._man_db.set_data(self._mandant_data, self._mandant_guid)
            
            # 2. Zusätzliche Felder setzen
            self._man_db.set_value('ROOT', 'DB_PATH', db_path, 1001.0)
            self._man_db.set_value('METADATEN', 'LETZTER_LOGIN', letzter_login, letzter_login)
            
            # 3. Speichern
            self._man_db.save_all_values()
            
            logger.info(f"💾 Mandanten-Daten abgeglichen in man_db")
            logger.info(f"   DB-Pfad: {db_path}")
            logger.info(f"   Letzter Login: {letzter_login}")
            
        except Exception as e:
            logger.error(f"⚠️ Fehler beim Abgleich der Mandanten-Daten: {e}")
            import traceback
            traceback.print_exc()
    
    # ========================================
    # V2.0 PROPERTIES FÜR MANDANTEN-ZUGRIFF
    # ========================================
    
    @property
    def mandant_db_path(self):
        """Gibt den Pfad zur Mandanten-Datenbank zurück"""
        try:
            mandant_id = self._mandant_data['METADATEN']['MANDANT_ID']
            from pathlib import Path
            return str(Path(__file__).parent / "Daten" / mandant_id / "datenbank.db")
        except Exception as e:
            logger.error(f"❌ Fehler beim Ermitteln des Mandanten-DB-Pfads: {e}")
            return None
    
    # ========================================
    # MENÜ-SYSTEM: System-Menü Pipelines (Singleton-Pattern)
    # ========================================
    
    def get_system_menu_pipeline(self, menu_guid: str):
        """
        Hole System-Menü-Pipeline für angegebene Gruppe.
        
        SINGLETON-PATTERN: Pro menu_guid wird nur EINE Pipeline-Instanz erstellt.
        
        Args:
            menu_guid: 'VERTIKAL', 'GRUND' oder 'ZUSATZ'
            
        Returns:
            PdvmMenuPipeline Instanz
            
        Example:
            >>> pipeline = gcs.get_system_menu_pipeline('VERTIKAL')
            >>> pipeline.run('BASIS')
            >>> matrix, info = pipeline.get_projected_data()
        """
        from pdvm_menu_pipeline import get_menu_pipeline
        
        # Lazy initialization: Nur erstellen wenn noch nicht vorhanden
        if menu_guid == 'VERTIKAL':
            if self._menu_pipeline_vertikal is None:
                logger.info(f"🎯 Erstelle VERTIKAL-Menü-Pipeline")
                self._menu_pipeline_vertikal = get_menu_pipeline('VERTIKAL', self._menu_system_db)
            return self._menu_pipeline_vertikal
            
        elif menu_guid == 'GRUND':
            if self._menu_pipeline_grund is None:
                logger.info(f"🎯 Erstelle GRUND-Menü-Pipeline")
                self._menu_pipeline_grund = get_menu_pipeline('GRUND', self._menu_system_db)
            return self._menu_pipeline_grund
            
        elif menu_guid == 'ZUSATZ':
            if self._menu_pipeline_zusatz is None:
                logger.info(f"🎯 Erstelle ZUSATZ-Menü-Pipeline")
                self._menu_pipeline_zusatz = get_menu_pipeline('ZUSATZ', self._menu_system_db)
            return self._menu_pipeline_zusatz
            
        else:
            logger.error(f"❌ Ungültige menu_guid: {menu_guid}")
            raise ValueError(f"Ungültige menu_guid: {menu_guid}. Muss 'VERTIKAL', 'GRUND' oder 'ZUSATZ' sein.")

# Globale Instanz
_gcs_instance = None

def initialize_gcs(user_guid, user_data, mandant_guid, mandant_data):
    """
    V2.0: Initialisiere globale Systemsteuerung mit Mandanten-Support
    
    Args:
        user_guid: GUID des Benutzers
        user_data: Benutzerdaten nach Login
        mandant_guid: GUID des gewählten Mandanten
        mandant_data: Mandanten-Daten aus auth.db
    """
    global _gcs_instance
    
    if _gcs_instance is not None and _gcs_instance.is_initialized:
        raise RuntimeError("GCS bereits initialisiert!")
    
    _gcs_instance = PdvmCentralSystemsteuerung(user_guid, user_data, mandant_guid, mandant_data)
    
    logger.info("🌐 Globale Systemsteuerung initialisiert (V2.0 mit Mandant)")
    return _gcs_instance

def get_gcs():
    """Hole globale Systemsteuerung"""
    if _gcs_instance is None or not _gcs_instance.is_initialized:
        raise RuntimeError("GCS nicht initialisiert! Rufe initialize_gcs() auf.")
    return _gcs_instance

def is_gcs_initialized():
    """Prüfe ob GCS initialisiert ist"""
    return _gcs_instance is not None and _gcs_instance.is_initialized

# ========================================
# HELPER FUNKTION: Vereinfachter Projektions-Zugriff
# ========================================

_gcs_instance = None

def initialize_gcs(user_guid, user_data, mandant_guid, mandant_data):
    """
    Initialisiere globale Systemsteuerung (V2.0 mit Mandant)
    
    Args:
        user_guid: GUID des Benutzers
        user_data: Benutzerdaten nach Login
        mandant_guid: GUID des gewählten Mandanten (NEU!)
        mandant_data: Mandanten-Daten aus auth.db (NEU!)
    """
    global _gcs_instance
    
    if _gcs_instance is not None and _gcs_instance.is_initialized:
        raise RuntimeError("GCS bereits initialisiert!")
    
    # V2.0: Zwei-Phasen-Initialisierung wegen Circular Dependency
    # Phase 1: GCS-Instanz erstellen (setzt db_path und _gcs_instance)
    _gcs_instance = PdvmCentralSystemsteuerung(user_guid, user_data, mandant_guid, mandant_data)
    
    logger.info("🌐 V2.0 Globale Systemsteuerung initialisiert")
    return _gcs_instance

def get_gcs():
    """
    V2.0: Hole globale Systemsteuerung
    
    WICHTIG: Gibt Instanz zurück, auch während Initialisierung (für db_path Zugriff)
    """
    if _gcs_instance is None:
        raise RuntimeError("GCS nicht initialisiert! Rufe initialize_gcs() auf.")
    return _gcs_instance

def is_gcs_initialized():
    """Prüfe ob GCS initialisiert ist"""
    return _gcs_instance is not None and _gcs_instance.is_initialized

def reset_gcs():
    """
    V2.0: Setze GCS zurück (für Logout/Neustart)
    
    Wichtig bei Logout: GCS muss zurückgesetzt werden damit
    beim nächsten Login eine neue Instanz erstellt wird.
    """
    global _gcs_instance
    
    if _gcs_instance is not None:
        logger.info("🔄 Setze GCS zurück für Neustart")
        _gcs_instance = None
    else:
        logger.debug("ℹ️ GCS bereits zurückgesetzt")

# ========================================
# HELPER FUNKTION: Vereinfachter Projektions-Zugriff
# ========================================

def get_view_projection(view_guid: str) -> list:
    """
    ✅ ULTRA-VEREINFACHT: Hole View-Projektion basierend auf expert_mode
    
    Ersetzt alle _get_visible_columns_from_gcs() Wrapper-Methoden!
    
    Args:
        view_guid: GUID der View
        
    Returns:
        list: Liste der sichtbaren Spalten-Keys (Standard oder Expert)
        
    Example:
        >>> visible_columns = get_view_projection(view_guid)
    """
    gcs = get_gcs() if is_gcs_initialized() else None
    if not gcs:
        logger.warning("⚠️ GCS nicht verfügbar für Projektions-Zugriff")
        return []
    
    # ✅ DIREKTER ARRAY-ZUGRIFF: Index 0 (Standard) oder 5 (Expert)
    projection_index = 5 if gcs.expert_mode else 0
    projection = gcs.get_projection_table(view_guid, projection_index)
    
    return projection if projection else []

# Alias für einfachen Zugriff
gcs = property(get_gcs)
