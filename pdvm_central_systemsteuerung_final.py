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
from pdvm_datetime import Pdvm_DateTime
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)

class PdvmCentralSystemsteuerung:
    """Zentrale Systemsteuerung mit robuster Architektur"""
    
    def __init__(self):
        """Initialisierung - noch ohne Daten"""
        self._db = None
        self._user_guid = None
        self._user_data = None
        self._st_inst = None
        self._initialized = False
        
        logger.info("🏗️ Zentrale Systemsteuerung erstellt (nicht initialisiert)")
    
    def initialize(self, user_guid, user_data):
        """
        Initialisierung nach dem Login
        
        Args:
            user_guid: GUID des Benutzers
            user_data: Vollständige Benutzerdaten-Dictionary oder JSON-String mit user_json
        """
        if self._initialized:
            raise RuntimeError("Systemsteuerung bereits initialisiert!")
        
        self._user_guid = user_guid
        
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
        # Daten kommen aus dem Login-Prozess
        from pdvm_central_datenbank import PdvmCentralDatenbank as RealDB
        self._u_db = RealDB('benutzerstamm')
        
        # Setze die user_json Daten direkt in die Benutzerdatenbank
        # user_data_dict ist bereits das geparste JSON von user_json
        if user_data_dict:
            self._u_db.set_data(user_data_dict, user_guid)
            logger.info(f"✅ Benutzerdatenbank geladen mit GUID: {user_guid} und {len(user_data_dict)} Properties")
        else:
            logger.warning(f"⚠️ Keine Benutzerdaten für GUID: {user_guid}")
        
        # 2.2 Datenbank-Instanz für Systemsteuerung 
        self._db = RealDB('systemsteuerung', user_guid)
        logger.info(f"✅ Systemsteuerungsdatenbank geladen mit GUID: {user_guid}")

        # Stichtag-Instanz erstellen und initialisieren
        country = self._u_db.get_static_value(user_guid, 'country') if user_guid in self._u_db.data else 'DEU'
        self._st_inst = Pdvm_DateTime(country)
        
        # Stichtag aus Systemsteuerung laden
        stored_stichtag = self._db.get_static_value(user_guid, 'stichtag') if user_guid in self._db.data and 'stichtag' in self._db.data[user_guid] else None
        if stored_stichtag is not None:
            try:
                self._st_inst.PdvmDateTime = float(stored_stichtag)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Ungültiger Stichtag aus DB: {stored_stichtag}, verwende Default")
        else:
            # Kein Stichtag in DB: Setze bekannten Default-Wert
            default_stichtag = 1001.0  
            self._st_inst.PdvmDateTime = default_stichtag
            # Speichere Default direkt in Systemsteuerung
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
            return self._u_db.get_static_value(gruppe, property_name)
        else:
            return self._db.get_static_value(gruppe, property_name)
    
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
            if group_guid in self._u_db.data:
                return self._u_db.data[group_guid].copy()
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
    
    _gcs_instance = PdvmCentralSystemsteuerung()
    _gcs_instance.initialize(user_guid, user_data)
    
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
