"""
PdvmViewDialog - Vereinfachte Dialog-basierte View-Architektur

Architektur:
- Dialog = autonome Anwendung + kompletter Datenmanager
- Display = nur UI-Verantwortung 
- Lineare Ausführung ohne komplexe Widget/Manager-Struktur
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                            QMenu, QAction, QMessageBox, QToolButton, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

# GLOBALE IMPORTS: Einfacher Zugriff auf zentrale Funktionen
import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_spalten_parameter_dialog_clean import PdvmSpaltenParameterDialog



logger = logging.getLogger(__name__)

class PdvmViewDialog:
    """
    Autonomer View-Dialog mit integriertem Datenmanagement
    
    Ablauf:
    1. Aufruf über call_daten (view_guid, user_guid, title)
    2. Dialog = Dateninstanz + alle Manager-Funktionen
    3. Display wird durch Dialog gesteuert
    """
    
    def __init__(self, call_daten, parent=None):
        """
        Initialisierung des autonomen View-Dialogs
        
        Args:
            call_daten: Enthält view_guid, user_guid, title
            parent: Parent-Widget
        """
        self.call_daten = call_daten
        self.parent = parent
        
        # 🔍 1. TITEL-VALIDATION: Prüfung auf erforderliche Daten
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.title = call_daten.get("title")
        
        # Fehlerbehandlung für fehlende erforderliche Daten
        error_messages = []
        if not self.view_guid:
            error_messages.append("❌ Keine view_guid in call_daten gefunden")
        if not self.user_guid:
            error_messages.append("❌ Keine user_guid in call_daten gefunden")
        if not self.title:
            error_messages.append("❌ Kein Titel in call_daten gefunden")
            
        if error_messages:
            error_text = "\n".join(error_messages)
            logger.error(f"Validation Error: {error_text}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(parent, "Fehlende Daten", 
                               f"Die Ausgabe kann nicht erfolgen:\n\n{error_text}")
            raise ValueError(error_text)
        
        # Zentrale Systemsteuerung - Globaler Zugriff
        # Nutze die globale Instanz für direkten Property-Zugriff
        if not gcs:
            error_msg = "❌ Zentrale Systemsteuerung nicht verfügbar"
            logger.error(error_msg)
            QMessageBox.critical(parent, "System Error", error_msg)
            raise RuntimeError(error_msg)
            
        logger.info(f"🔹 PdvmViewDialog initialisiert - View: {self.view_guid}, User: {self.user_guid}")
        
        # Datenbank-Instanzen
        self.view_db = PdvmCentralDatenbank()  # Für View-Daten und get_value_view
        self.control_db = PdvmCentralDatenbank(self.view_guid)  # Controls pro View
        
        # Daten-Container
        self.view_config = None
        self.controls_config = None
        self.all_data_records = []
        self.display_matrix = []
        
        # 🚀 PERFORMANCE-OPTIMIERUNG: Smart Data Caching
        self.cached_all_data = None      # Cache für alle gelesenen Datensätze
        self.cached_view_config = None   # Cache für View-Konfiguration
        self.cached_controls_config = None  # Cache für Controls-Konfiguration
        self.cache_timestamp = None      # Zeitstempel des Caches
        self.cache_view_guid = None      # View-GUID für Cache-Validierung
        
        # UI-Container
        self.display = None
        
        # Initialisierung starten
        self._initialize_dialog()
    
    # 🚀 PERFORMANCE-OPTIMIERUNG: Cache-Management-Methoden
    def _is_cache_valid(self):
        """Prüft ob der aktuelle Cache noch gültig ist"""
        if not self.cached_all_data or not self.cache_view_guid:
            return False
        
        # Cache nur für gleiche View-GUID gültig
        if self.cache_view_guid != self.view_guid:
            return False
        
        # Cache-Altersprüfung (optional: nach X Minuten verfallen lassen)
        import time
        if self.cache_timestamp:
            cache_age = time.time() - self.cache_timestamp
            if cache_age > 3600:  # 1 Stunde Cache-Lebensdauer
                logger.info("🗑️ Cache ist zu alt (>1h) - wird verworfen")
                return False
        
        return True
    
    def _save_to_cache(self):
        """Speichert aktuelle Daten im Cache"""
        import time
        self.cached_all_data = self.raw_records.copy() if hasattr(self, 'raw_records') else []
        self.cached_view_config = self.view_config.copy() if self.view_config else None
        self.cached_controls_config = self.controls_config.copy() if self.controls_config else None
        self.cache_timestamp = time.time()
        self.cache_view_guid = self.view_guid
        logger.info(f"💾 Daten im Cache gespeichert: {len(self.cached_all_data)} Datensätze")
    
    def _load_from_cache(self):
        """Lädt Daten aus dem Cache"""
        if self._is_cache_valid():
            self.raw_records = self.cached_all_data.copy()
            self.view_config = self.cached_view_config.copy() if self.cached_view_config else None
            self.controls_config = self.cached_controls_config.copy() if self.cached_controls_config else None
            logger.info(f"🚀 Daten aus Cache geladen: {len(self.raw_records)} Datensätze (Performance-Optimierung)")
            return True
        return False
    
    def _clear_cache(self):
        """Löscht den Cache"""
        self.cached_all_data = None
        self.cached_view_config = None
        self.cached_controls_config = None
        self.cache_timestamp = None
        self.cache_view_guid = None
        logger.info("🗑️ Cache geleert")

    def _initialize_dialog(self):
        """
        🚀 PERFORMANCE-OPTIMIERTE INITIALISIERUNG mit first_call-Logik
        
        first_call=True:  Vollständige Initialisierung (Controls + Daten laden)
        first_call=False: Nur Matrix neu aufbauen (Stichtag-Refresh)
        """
        first_call = self.call_daten.get('first_call', True)
        logger.info(f"🔹 Starte Dialog-Initialisierung (first_call={first_call})...")
        
        if first_call:
            # 🔄 ERSTAUFRUF: Vollständige Initialisierung
            logger.info("🆕 Erstaufruf - vollständige Initialisierung")
            
            # 1. Basisdaten erstellen
            self._create_base_data()
            
            # 2. Controls aufbauen  
            self._build_controls_from_view()
            
            # 3. Controls mit Systemsteuerung synchronisieren
            self._sync_controls_with_systemsteuerung()
            
            # 4. Alle Datensätze laden (mit Cache-Check)
            if not self._load_from_cache():
                self._load_all_data_records()
                self._save_to_cache()
            
        else:
            # 🔄 REFRESH: Nur Matrix neu aufbauen
            logger.info("🔄 Stichtag-Refresh - nur Matrix neu aufbauen")
            
            # Cache laden (sollte vorhanden sein)
            if not self._load_from_cache():
                logger.warning("⚠️ Cache nicht verfügbar - lade Daten neu")
                self._create_base_data()
                self._build_controls_from_view() 
                self._load_all_data_records()
                self._save_to_cache()
        
        # 5. Display-Matrix für aktuellen Stichtag erstellen (immer)
        self._build_display_matrix()
        
        # 6. UI-Display erstellen und zeigen (immer)
        self._create_and_show_display()
        
        logger.info("✅ Dialog-Initialisierung abgeschlossen")
    
    def _create_base_data(self):
        """🔧 Basisdaten erstellen - robuste View-Konfiguration laden"""
        logger.info("� Erstelle Basisdaten...")
        
        # View-Konfiguration laden (analog zu _load_view_felder)
        try:
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten", 
                guid=self.view_guid
            )
            
            # VIEW_TABLE ermitteln - mit Fallback
            view_table = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not view_table:
                # Fallback: Versuche andere mögliche Felder
                view_table = view_db.get_static_value(gruppe='ROOT', feld='view_table')
                if not view_table:
                    # Standard-Fallback für Tests
                    view_table = "persondaten"
                    logger.warning(f"⚠️ VIEW_TABLE nicht gefunden - verwende Fallback: {view_table}")
            
            # ViewDaten-Metadaten laden - mit Fallback
            view_metadaten = view_db.get_static_value(gruppe='METADATEN', feld=view_table.upper())
            if not view_metadaten or 'felder' not in view_metadaten:
                # Fallback: Standard-Felder für persondaten erstellen
                logger.warning("⚠️ ViewDaten-Felder nicht gefunden - erstelle Standard-Fallback")
                view_metadaten = {
                    'felder': [
                        {'feld': 'VORNAME', 'name': 'Vorname', 'type': 'string', 'gruppe': 'PERSDATEN'},
                        {'feld': 'NAME', 'name': 'Nachname', 'type': 'string', 'gruppe': 'PERSDATEN'},
                        {'feld': 'GEBURTSDATUM', 'name': 'Geburtsdatum', 'type': 'date', 'gruppe': 'PERSDATEN'},
                        {'feld': 'STATUS', 'name': 'Status', 'type': 'string', 'gruppe': 'PERSDATEN'}
                    ]
                }
                
            # View-Config zusammenstellen
            self.view_config = {
                'ROOT': {'view_table': view_table},
                'spalten': view_metadaten['felder']
            }
            
            logger.info(f"✅ View-Konfiguration geladen: Tabelle '{view_table}', {len(self.view_config['spalten'])} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Konfiguration: {e}")
            # Notfall-Fallback: Minimale Konfiguration
            self.view_config = {
                'ROOT': {'view_table': 'persondaten'},
                'spalten': [
                    {'feld': 'VORNAME', 'name': 'Vorname', 'type': 'string', 'gruppe': 'PERSDATEN'},
                    {'feld': 'NAME', 'name': 'Nachname', 'type': 'string', 'gruppe': 'PERSDATEN'}
                ]
            }
            logger.warning("⚠️ Verwende Notfall-Fallback Konfiguration")
    
    def _build_controls_from_view(self):
        """
        🔧 STEP-BY-STEP CONTROL-AUFBAU wie im Original:
        
        1. Controls anhand der viewDaten mit _original Zusatz
        2. Für type=date werden Zusatz-Spalten (alter, jahr, monat, tag) erstellt  
        3. Aus _original werden _show Spalten gebildet
        4. Dummy-Spalte wird hinzugefügt
        5. Attribute aus Systemsteuerung übernehmen (show, expertOrder, displayOrder)
        """
        logger.info("� Starte Step-by-Step Control-Aufbau...")
        
        # Neue Viewdaten-Struktur mit METADATEN
        if not self.view_config:
            logger.warning("⚠️ Keine View-Konfiguration gefunden")
            self.controls_config = {'ColumnControls': {}}
            return
            
        # Extrahiere Felder aus neuer Struktur: METADATEN -> PERSONDATEN -> felder
        view_felder = []
        if 'METADATEN' in self.view_config and 'PERSONDATEN' in self.view_config['METADATEN']:
            view_felder = self.view_config['METADATEN']['PERSONDATEN'].get('felder', [])
        elif 'spalten' in self.view_config:  # Fallback für alte Struktur
            view_felder = self.view_config['spalten']
            
        if not view_felder:
            logger.warning("⚠️ Keine Felder in View-Konfiguration gefunden")
            self.controls_config = {'ColumnControls': {}}
            return
        logger.info(f"📊 Verarbeite {len(view_felder)} View-Felder")
        
        # STEP 1: ORIGINAL-CONTROLS erstellen
        columns = []
        order_counter = 0
        
        # System-Spalte: uid_original
        uid_orig_col = {
            'name': 'uid_original',
            'type': 'string',
            'gruppe': 'SYSTEM',
            'feld': 'UID',
            'show': False,  # Standard: unsichtbar
            'expertOrder': order_counter,
            'displayOrder': order_counter,
            'field_config': {'feld': 'UID', 'name': 'UID', 'type': 'string'},
            'spaltenueberschrift': 'UID (orig.)'
        }
        columns.append(uid_orig_col)
        order_counter += 1
        logger.info(f"➕ System-Control erstellt: uid_original")
        
        # View-Felder: _original Controls erstellen
        for feld_config in view_felder:
            feldname_gross = feld_config.get("feld", feld_config.get("name", "unknown"))
            feld_name = feldname_gross.lower()
            feld_type = feld_config.get("type", "string")
            gruppe = feld_config.get("gruppe", "PERSDATEN")
            spaltenname = feld_config.get("name", feld_name)
            
            # Haupt-_original Control
            name_orig = f"{feld_name}_original"
            col = {
                'name': name_orig,
                'type': feld_type,
                'gruppe': gruppe,
                'feld': feldname_gross,
                'show': False,  # Standard: unsichtbar
                'expertOrder': order_counter,
                'displayOrder': order_counter,
                'field_config': feld_config,
                'spaltenueberschrift': f"{spaltenname} (orig.)"
            }
            columns.append(col)
            order_counter += 1
            logger.debug(f"➕ Original-Control erstellt: {name_orig}")
            
            # STEP 2: Zusatzfelder für type=date mit UI-Parameter-Integration
            if feld_type == "date":
                # UI-Parameter aus Feld-Konfiguration extrahieren
                ui_config = feld_config.get('ui', {})
                show_ymd = ui_config.get('show_YMD', False)
                show_alter = ui_config.get('show_alter', False)
                
                zusatz_namen = {
                    "alter": "Alter",
                    "jahr": "Jahr", 
                    "monat": "Monat",
                    "tag": "Tag"
                }
                
                for zusatz in ["alter", "jahr", "monat", "tag"]:
                    # Sichtbarkeit basierend auf UI-Parametern bestimmen
                    zusatz_sichtbar = False
                    if zusatz == "alter" and show_alter:
                        zusatz_sichtbar = True
                    elif zusatz in ["jahr", "monat", "tag"] and show_ymd:
                        zusatz_sichtbar = True
                    
                    zusatz_field_config = feld_config.copy()
                    zusatz_field_config["type"] = f"date_{zusatz}"
                    zusatz_field_config["ui_visible"] = zusatz_sichtbar
                    
                    name_zusatz = f"{feld_name}_{zusatz}_original"
                    zusatz_anzeige = zusatz_namen[zusatz]
                    
                    col = {
                        'name': name_zusatz,
                        'type': f"date_{zusatz}",
                        'gruppe': gruppe,
                        'feld': feldname_gross,
                        'show': False,  # Standard: unsichtbar
                        'expertOrder': order_counter,
                        'displayOrder': order_counter,
                        'field_config': zusatz_field_config,
                        'spaltenueberschrift': f"{spaltenname} {zusatz_anzeige} (orig.)",
                        'ui_visible': zusatz_sichtbar  # UI-Parameter markieren
                    }
                    columns.append(col)
                    order_counter += 1
                    logger.debug(f"➕ Date-Zusatz-Control erstellt: {name_zusatz} (UI-sichtbar: {zusatz_sichtbar})")
        
        logger.info(f"✅ Step 1+2: {len(columns)} Original-Controls erstellt (inkl. Date-Zusätze)")
        
        # STEP 3: _show Controls für alle _original Controls erstellen
        original_count = len(columns)
        for col in columns[:original_count]:  # Nur über Original-Liste iterieren
            if col['name'].endswith('_original'):
                show_name = col['name'].replace('_original', '_show')
                
                # Überschrift: Gleich wie Original-Spalte, aber ohne "(orig.)"
                original_ueberschrift = col.get('spaltenueberschrift', '')
                show_ueberschrift = original_ueberschrift.replace(' (orig.)', '') if original_ueberschrift else show_name
                
                # Sichtbarkeit für _show Controls basierend auf UI-Parametern bestimmen
                ui_visible = col.get('ui_visible', True)  # Standard: sichtbar
                show_visible = True if col['name'] == 'uid_original' else ui_visible
                
                show_col = {
                    'name': show_name,
                    'type': col['type'],
                    'gruppe': col.get('gruppe'),
                    'feld': col.get('feld'),
                    'show': show_visible,  # UI-Parameter berücksichtigen
                    'expertOrder': order_counter,
                    'displayOrder': order_counter,
                    'field_config': col.get('field_config', {}),
                    'spaltenueberschrift': show_ueberschrift,
                    'ui_visible': ui_visible  # UI-Parameter weiterleiten
                }
                columns.append(show_col)
                order_counter += 1
                logger.debug(f"➕ Show-Control erstellt: {show_name}")
        
        logger.info(f"✅ Step 3: {len(columns) - original_count} Show-Controls erstellt")
        
        # STEP 4: Dummy-Spalte hinzufügen
        dummy_col = {
            'name': 'dummy',
            'type': 'dummy',
            'show': False,  # Standard: unsichtbar
            'expertOrder': order_counter,
            'displayOrder': order_counter,
            'field_config': {},
            'spaltenueberschrift': ''
        }
        columns.append(dummy_col)
        order_counter += 1
        logger.info(f"✅ Step 4: Dummy-Control hinzugefügt - Gesamt: {len(columns)} Controls")
        
        # Als Dict für einfachen Zugriff konvertieren
        self.controls_config = {
            'ColumnControls': {col['name']: col for col in columns}
        }
        
        logger.info(f"✅ Control-Aufbau abgeschlossen: {len(columns)} Controls erstellt")
    
    def _sync_controls_with_systemsteuerung(self):
        """
        🔧 STEP 5: Controls mit Systemsteuerung synchronisieren
        
        - Attribute show, expertOrder, displayOrder aus Systemsteuerung übernehmen
        - Neue Controls markieren und bei Bedarf speichern
        - Bei neuen Controls alle Order-Werte neu nummerieren
        """
        logger.info("� Step 5: Synchronisiere Controls mit Systemsteuerung...")
        
        if not self.controls_config or 'ColumnControls' not in self.controls_config:
            logger.warning("⚠️ Keine Controls für Synchronisation verfügbar")
            return
        
        try:
            # Bestehende Control-Attribute aus Systemsteuerung laden
            existing_controls = self.control_db.get_value(self.view_guid, 'ColumnControls')
            attr_map = {}
            
            if existing_controls and 'wert' in existing_controls:
                attr_map = existing_controls['wert']
                logger.info(f"📋 {len(attr_map)} gespeicherte Control-Attribute geladen")
            else:
                logger.info("📋 Keine gespeicherten Control-Attribute gefunden")
            
            # SYNCHRONISATION: Attribute aus Systemsteuerung übernehmen
            columns = list(self.controls_config['ColumnControls'].values())
            found_new_controls = False
            
            for col in columns:
                col_name = col['name']
                if col_name in attr_map:
                    # Bestehende Einstellungen übernehmen
                    saved_attrs = attr_map[col_name]
                    col['show'] = saved_attrs.get('show', col['show'])
                    col['expertOrder'] = saved_attrs.get('expertOrder', col['expertOrder'])
                    col['displayOrder'] = saved_attrs.get('displayOrder', col['displayOrder'])
                    logger.debug(f"🔄 Control-Attribute übernommen: {col_name}")
                else:
                    # NEUES Control nicht in Systemsteuerung gefunden
                    logger.debug(f"🆕 Neues Control gefunden: {col_name}")
                    col['expertOrder'] += 1000  # Markierung als "neu"
                    col['displayOrder'] += 1000  # Markierung als "neu"
                    # _show Controls: show=True beibehalten, andere: show bleibt wie Standard
                    if col_name.endswith('_show'):
                        col['show'] = True
                    found_new_controls = True
            
            logger.info(f"✅ Synchronisation abgeschlossen - neue Controls gefunden: {found_new_controls}")
            
            # Bei neuen Controls: Alle Order-Werte neu nummerieren
            if found_new_controls:
                logger.info(f"🔧 Neue Controls gefunden - nummeriere alle Order-Werte neu")
                
                # ExpertOrder neu nummerieren
                expert_sorted = sorted(columns, key=lambda x: x['expertOrder'])
                for i, col in enumerate(expert_sorted):
                    col['expertOrder'] = i
                    
                # DisplayOrder neu nummerieren  
                display_sorted = sorted(columns, key=lambda x: x['displayOrder'])
                for i, col in enumerate(display_sorted):
                    col['displayOrder'] = i
                    
                logger.info(f"✅ Order-Werte neu nummeriert: {len(columns)} Controls")
                
                # Neue Controls in Systemsteuerung speichern
                persist_map = {col['name']: {
                    'show': col['show'],
                    'expertOrder': col['expertOrder'],
                    'displayOrder': col['displayOrder']
                } for col in columns}
                
                try:
                    self.control_db.set_value(self.view_guid, 'ColumnControls', persist_map)
                    self.control_db.save_values()
                    logger.info(f"💾 Neue Controls in Systemsteuerung gespeichert für {self.view_guid}")
                except Exception as e:
                    logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht speichern: {e}")
            
            # Controls wieder als Dict struktur speichern
            self.controls_config['ColumnControls'] = {col['name']: col for col in columns}
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Control-Synchronisation: {e}")
            # Fallback: Generierte Controls verwenden
            logger.info("🔄 Verwende generierte Controls als Fallback")
    
    def _load_all_data_records(self):
        """
        🎯 PERFORMANCE-OPTIMIERTE DATENLADUNG
        
        Lädt ALLE Rohdatensätze (ohne Stichtag-Filter) für maximale Performance
        bei Stichtag-Wechseln - nur Matrix wird neu aufgebaut
        """
        logger.info("🔹 Lade alle Rohdatensätze (ohne Stichtag-Filter)...")
        
        try:
            # View-Datenbank für die spezifische Tabelle
            table_name = self.view_config['ROOT']['view_table']
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=table_name
            )
            
            # lesen_alle_ohne_system verwenden - ROHDATEN bleiben statisch
            self.raw_records = view_db.lesen_alle_ohne_system()
            
            if self.raw_records:
                logger.info(f"✅ {len(self.raw_records)} Rohdatensätze geladen - optimiert für Stichtagswechsel")
            else:
                logger.warning("⚠️ Keine Datensätze gefunden")
                self.raw_records = []
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Datensätze: {e}")
            self.raw_records = []
    
    def _build_display_matrix(self):
        """
        🔧 STEP 6: Display-Matrix für aktuellen Stichtag erstellen
        
        - Für jeden Rohdatensatz eine Matrix-Zeile erstellen
        - Alle _original Felder mit get_value füllen (stichtagsbasiert)
        - Alle _show Felder von _original übertragen (1:1 Kopie)
        - UID-Behandlung für System-Spalten
        """
        logger.info("� Step 6: Erstelle Display-Matrix...")
        
        current_stichtag = gcs.stichtag
        logger.info(f"📅 Verwende Stichtag: {current_stichtag}")
        
        self.display_matrix = []
        
        if not self.raw_records:
            logger.warning("⚠️ Keine Rohdatensätze verfügbar")
            return
            
        # EINE temporäre PdvmCentralDatenbank Instanz für alle get_value Operationen
        table_name = self.view_config['ROOT']['view_table']
        temp_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name=table_name
        )
        
        logger.info(f"📊 Verarbeite {len(self.raw_records)} Rohdatensätze...")
        
        # Für jeden Rohdatensatz Matrix-Zeile erstellen
        for record_idx, record in enumerate(self.raw_records):
            row_data = {}
            
            try:
                # Rohdaten in die temporäre DB-Instanz setzen (überschreibt vorherige)
                temp_db.set_data(record['daten_dict'], record['uid'])
                
                # STEP 6.1: System-Spalten füllen
                row_data['uid_original'] = record['uid']
                row_data['uid_show'] = record['uid']
                
                # STEP 6.2: Alle _original Felder mit get_value füllen
                controls = self.controls_config.get('ColumnControls', {})
                for control_name, control_config in controls.items():
                    if control_name.endswith('_original') and control_name != 'uid_original':
                        control_type = control_config.get('type', '')
                        
                        # Normale Felder (nicht date_*)
                        if not control_type.startswith('date_'):
                            # Feldwert über get_value mit Stichtag holen
                            gruppe = control_config.get('gruppe', 'PERSDATEN')
                            feld = control_config.get('feld', '')
                            
                            if feld:
                                wert = self._get_field_value_by_stichtag(temp_db, gruppe, feld, current_stichtag)
                                row_data[control_name] = wert
                            else:
                                row_data[control_name] = ''
                        
                        # Date-Zusatzfelder (date_alter, date_jahr, etc.)
                        else:
                            zusatz_typ = control_type.replace('date_', '')  # alter, jahr, monat, tag
                            
                            # Basis-Feld finden (ohne _zusatz_original)
                            basis_field_name = control_name.replace(f'_{zusatz_typ}_original', '_original')
                            
                            # Prüfen ob Basis-Feld bereits berechnet wurde
                            if basis_field_name in row_data:
                                # Verwende bereits berechneten Basis-Wert
                                basis_wert = row_data[basis_field_name]
                            else:
                                # Basis-Feld direkt aus DB holen
                                gruppe = control_config.get('gruppe', 'PERSDATEN')
                                feld = control_config.get('feld', '')
                                
                                if feld:
                                    basis_wert = self._get_field_value_by_stichtag(temp_db, gruppe, feld, current_stichtag)
                                else:
                                    basis_wert = ''
                            
                            # Date-Zusatz berechnen
                            if basis_wert and isinstance(basis_wert, (int, float)) and basis_wert > 0:
                                zusatz_wert = self._format_date_field(basis_wert, zusatz_typ)
                                row_data[control_name] = zusatz_wert
                                logger.debug(f"📅 {control_name}: {basis_wert} → {zusatz_wert} ({zusatz_typ})")
                            else:
                                row_data[control_name] = ''
                
                # STEP 6.3: Alle _show Felder von _original übertragen mit Formatierung
                for control_name, control_config in controls.items():
                    if control_name.endswith('_show'):
                        original_name = control_name.replace('_show', '_original')
                        original_value = row_data.get(original_name, '')
                        control_type = control_config.get('type', '')
                        
                        # Spezielle Formatierung für Date-Felder (nicht date_*)
                        if control_type == 'date' and isinstance(original_value, (int, float)) and original_value > 0:
                            try:
                                from pdvm_datetime import Pdvm_DateTime
                                dt_formatter = Pdvm_DateTime("DEU")
                                dt_formatter.PdvmDateTime = original_value
                                formatted_value = dt_formatter.Date_formatted
                                row_data[control_name] = formatted_value
                                logger.debug(f"📅 {control_name}: {original_value} → {formatted_value} (formatiert)")
                            except Exception as e:
                                row_data[control_name] = str(original_value)
                                logger.debug(f"⚠️ {control_name}: Formatierung fehlgeschlagen: {e}")
                        else:
                            # Spezielle Behandlung für uid_show (nur erste 8 Zeichen)
                            if control_name == 'uid_show' and isinstance(original_value, str):
                                row_data[control_name] = original_value[:8] + "..." if len(original_value) > 8 else original_value
                                logger.debug(f"🔧 {control_name}: {original_value} → {row_data[control_name]} (verkürzt)")
                            else:
                                # Normale 1:1 Übertragung für alle anderen Felder
                                row_data[control_name] = original_value
                
                # STEP 6.4: Dummy-Spalte
                row_data['dummy'] = ''
                
                self.display_matrix.append(row_data)
                
                if record_idx % 5 == 0:  # Alle 5 Datensätze loggen
                    logger.debug(f"📋 Zeile {record_idx + 1}: {len(row_data)} Felder gefüllt")
                
            except Exception as e:
                logger.warning(f"⚠️ Fehler bei Datensatz {record['uid']}: {e}")
                continue
        
        logger.info(f"✅ Display-Matrix erstellt: {len(self.display_matrix)} Zeilen × {len(row_data) if self.display_matrix else 0} Spalten")
    
    def _get_field_value_by_stichtag(self, temp_db: PdvmCentralDatenbank, gruppe: str, feld: str, stichtag: float):
        """
        🔧 Extrahiert einen Feldwert zum Stichtag aus einer temporären DB-Instanz.
        
        Args:
            temp_db: Temporäre PdvmCentralDatenbank Instanz mit set_data gesetzten Daten
            gruppe: Gruppe des Feldes (z.B. PERSDATEN)
            feld: Name des gesuchten Feldes
            stichtag: Stichtag als Float-Wert
            
        Returns:
            Der Wert des Feldes zum Stichtag oder leerer String falls nicht gefunden
        """
        try:
            # Mit get_value den stichtagsbasierten Wert holen
            result = temp_db.get_value(gruppe, feld, stichtag)
            
            if result and 'wert' in result:
                return result['wert']
            else:
                # Fallback: Direkter Zugriff auf Daten ohne Stichtag
                if gruppe in temp_db.data and feld in temp_db.data[gruppe]:
                    gruppe_data = temp_db.data[gruppe][feld]
                    if isinstance(gruppe_data, dict) and 'wert' in gruppe_data:
                        return gruppe_data['wert']
                    elif not isinstance(gruppe_data, dict):
                        return str(gruppe_data)
                        
                return ''
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Extrahieren von Feld '{gruppe}.{feld}': {e}")
            return ''
    
    def _format_date_field(self, date_value, date_type):
        """
        🔧 Formatiert Date-Zusatzfelder (alter, jahr, monat, tag) - ORIGINAL-LOGIK
        
        Args:
            date_value: Der ursprüngliche Datumswert (float)
            date_type: Art der Formatierung (alter, jahr, monat, tag)
            
        Returns:
            Formatierter Wert als String oder Int
        """
        try:
            if not date_value:
                return ''
                
            # Stelle sicher, dass date_value eine Zahl ist
            if isinstance(date_value, str):
                try:
                    date_value = float(date_value)
                except (ValueError, TypeError):
                    return ''
            
            if not isinstance(date_value, (int, float)) or date_value <= 0:
                return ''
            
            # ORIGINAL-LOGIK: PdvmDateTime verwenden für Jahr/Monat/Tag
            if date_type in ['jahr', 'monat', 'tag']:
                try:
                    from pdvm_datetime import Pdvm_DateTime
                    dt_formatter = Pdvm_DateTime("DEU")
                    dt_formatter.PdvmDateTime = date_value
                    
                    if date_type == 'jahr':
                        return dt_formatter.Year
                    elif date_type == 'monat':
                        return dt_formatter.Month
                    elif date_type == 'tag':
                        return dt_formatter.Day
                        
                except Exception as e:
                    logger.warning(f"⚠️ PdvmDateTime Fehler für {date_type}: {e}")
                    return ''
            
            # ORIGINAL-LOGIK: Präzise tagesexakte Altersberechnung
            elif date_type == 'alter':
                current_stichtag = gcs.stichtag
                if current_stichtag and isinstance(current_stichtag, (int, float)):
                    return self._berechne_alter(current_stichtag, date_value)
                else:
                    return ''
            
            else:
                logger.warning(f"⚠️ Unbekannter Date-Type: {date_type}")
                return str(date_value)
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Formatieren von Date-Feld '{date_type}': {e}")
            return str(date_value) if date_value else ''
    
    def _berechne_alter(self, stichtag, datum):
        """
        🔧 ORIGINAL-ALTERSBERECHNUNG: Präzise tagesexakte Berechnung
        
        Args:
            stichtag: Aktueller Stichtag (float)
            datum: Geburtsdatum (float)
            
        Returns:
            Alter in Jahren (int)
        """
        try:
            stdiff = int(stichtag) - int(datum)
            strest = stdiff % 1000
            alter_jahre = int((stdiff - strest) / 1000)
            return alter_jahre
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Altersberechnung: {e}")
            return 0
    
    def _create_and_show_display(self):
        """7. UI-Display als Widget erstellen (kein show() - wird vom Parent gesteuert)"""
        logger.info("🔹 Erstelle UI-Display...")
        
        self.display = PdvmViewDisplay(self)
        
        logger.info("✅ Display erstellt")
    
    def get_display_widget(self):
        """Widget für Integration in Arbeitsbereich zurückgeben"""
        if not self.display:
            self._create_and_show_display()
        return self.display
    
    def reload(self):
        """🔄 STICHTAG-RELOAD: Reaktion auf Stichtag-Änderungen"""
        logger.info("🔄 Dialog-Reload wegen Stichtag-Änderung...")
        
        try:
            # Stichtag hat sich geändert → Display-Matrix neu erstellen
            self._build_display_matrix()
            
            # UI-Display aktualisieren
            if self.display:
                self.display.refresh_table()
                logger.info("✅ Dialog-Reload erfolgreich abgeschlossen")
            else:
                logger.warning("⚠️ Kein Display für Reload verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Dialog-Reload: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def refresh_on_stichtag_change(self):
        """6. Refresh bei Stichtagswechsel - ALIAS für reload()"""
        self.reload()
    
    def refresh_on_control_change(self):
        """7. Refresh nach Änderung im Spalten-Dialog"""
        logger.info("🔄 Refresh wegen Control-Änderung...")
        
        # Controls neu laden
        self._sync_controls_with_systemsteuerung()
        
        if self.display:
            self.display.refresh_table()
    
    def open_spalten_dialog(self):
        """🔧 2. SPALTEN-DIALOG PARAMETER FIX: Korrekte Parameter verwenden"""
        logger.info("🔧 Öffne Spalten-Dialog...")
        
        try:
            # 🔧 KORRIGIERTE PARAMETER-SIGNATUR aus pdvm_spalten_parameter_dialog_clean.py:
            # __init__(self, parent, mode, controls, provider, daten_manager, user_guid, view_config)
            
            # Temporären DatenManager für Dialog erstellen
            from pdvm_view_daten_manager import PdvmViewDatenManager
            temp_daten_manager = PdvmViewDatenManager(
                view_guid=self.view_guid,
                user_guid=self.user_guid,
                stichtag_manager=gcs  # Als Stichtag-Provider
            )
            
            dialog = PdvmSpaltenParameterDialog(
                parent=self.display,              # parent
                mode='edit',                      # mode 
                controls=self.controls_config['ColumnControls'],  # controls
                provider=gcs,    # provider
                daten_manager=temp_daten_manager, # daten_manager
                user_guid=self.user_guid,         # user_guid (nicht view_guid!)
                view_config=self.view_config      # view_config
            )
            
            if dialog.exec_() == QDialog.Accepted:
                logger.info("✅ Spalten-Dialog mit OK beendet")
                self.refresh_on_control_change()
            else:
                logger.info("❌ Spalten-Dialog abgebrochen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Spalten-Dialogs: {e}")
            # Benutzerfreundliche Fehlermeldung
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self.display, "Spalten-Dialog Fehler", 
                              f"Der Spalten-Dialog konnte nicht geöffnet werden:\n\n{str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


class PdvmViewDisplay(QWidget):
    """
    UI-Display für PdvmViewDialog als Arbeitsbereich-Widget
    Nur Verantwortung für Oberfläche, alle Daten kommen vom Dialog
    """
    
    def __init__(self, view_dialog):
        super().__init__(view_dialog.parent)
        self.view_dialog = view_dialog
        
        # Header-Label für dynamische Updates
        self.header_label = None
        
        self._setup_ui()
        self._refresh_table()
        self.update_header_text()
    
    def _setup_ui(self):
        """UI-Setup als Arbeitsbereich-Widget"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)  # Keine Margins für Arbeitsbereich
        
        # Header-Bereich
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Dynamischer Header-Text aus call_daten
        self.header_label = QLabel()
        header_font = QFont("Segoe UI", 12, QFont.Bold)
        self.header_label.setFont(header_font)
        self.header_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border: 1px solid #bdc3c7;
            }
        """)
        header_layout.addWidget(self.header_label)
        
        header_layout.addStretch()
        
        # Settings-Button
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙️")
        self.settings_button.setToolTip("Einstellungen")
        self.settings_button.setPopupMode(QToolButton.InstantPopup)
        self.settings_button.setStyleSheet("""
            QToolButton {
                font-size: 16px;
                padding: 6px;
                border: 1px solid #95a5a6;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QToolButton:hover {
                background-color: #d5dbdb;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        
        self._create_settings_menu()
        header_layout.addWidget(self.settings_button)
        
        layout.addLayout(header_layout)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                selection-background-color: #3498db;
                selection-color: white;
                alternate-background-color: #f8f9fa;
                background-color: white;
                border: 1px solid #bdc3c7;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
            }
        """)
        layout.addWidget(self.table)
        
        # Status-Zeile (ohne Buttons)
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 10pt;
                padding: 4px;
            }
        """)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
    
    def _create_settings_menu(self):
        """Settings-Menü wie im Original erstellen"""
        settings_menu = QMenu(self)
        
        # Spalten-Dialog
        spalten_action = QAction("📊 Spalten konfigurieren", self)
        spalten_action.triggered.connect(self.view_dialog.open_spalten_dialog)
        settings_menu.addAction(spalten_action)
        
        settings_menu.addSeparator()
        
        # Expert-Mode Toggle (nur bei Admin-Mode verfügbar)
        if gcs.is_expert_mode_available():
            expert_action = QAction("🔧 Expert-Mode", self)
            expert_action.setCheckable(True)
            expert_action.setChecked(gcs.expert_mode)
            expert_action.triggered.connect(self._toggle_expert_mode)
            settings_menu.addAction(expert_action)
            settings_menu.addSeparator()
        
        # Filter (noch inaktiv)
        filter_action = QAction("🔍 Filter", self)
        filter_action.triggered.connect(self._toggle_filter)
        settings_menu.addAction(filter_action)
        
        self.settings_button.setMenu(settings_menu)
    
    def update_header_text(self):
        """Header-Text aus call_daten mit Stichtag im Expert-Mode"""
        try:
            # Basis-Text aus call_daten
            header_text = self.view_dialog.title
            
            # Im Expert-Mode Stichtag hinzufügen
            if gcs.expert_mode:
                stichtag = gcs.stichtag
                if stichtag:
                    header_text += f" | Stichtag: {stichtag}"
                header_text += " | Expert-Mode"
            
            self.header_label.setText(header_text)
            
        except Exception as e:
            logger.warning(f"Fehler beim Update des Header-Texts: {e}")
            self.header_label.setText(self.view_dialog.title)
    
    def refresh_table(self):
        """Tabelle neu aufbauen"""
        self._refresh_table()
        self.update_header_text()
    
    def _refresh_table(self):
        """🔧 4. DATEN-DISPLAY FIX: Tabelle nach ExpertMode/NormalMode aufbauen"""
        try:
            logger.info("🔧 Starte Tabellen-Refresh...")
            
            # Daten-Matrix prüfen
            if not self.view_dialog.display_matrix:
                logger.warning("⚠️ Keine Display-Matrix verfügbar - erstelle Fallback")
                self._create_fallback_table()
                return
                
            expert_mode = gcs.expert_mode
            controls = self.view_dialog.controls_config.get('ColumnControls', {})
            
            # Controls nach Typ aufschlüsseln
            original_count = len([name for name in controls.keys() if name.endswith('_original')])
            show_count = len([name for name in controls.keys() if name.endswith('_show')])
            dummy_count = len([name for name in controls.keys() if name == 'dummy_control'])
            other_count = len(controls) - original_count - show_count - dummy_count
            
            logger.info(f"📊 Expert-Mode: {expert_mode}, Controls: {len(controls)} gesamt")
            logger.info(f"    📋 _original: {original_count}, _show: {show_count}, dummy: {dummy_count}, andere: {other_count}")
            logger.info(f"    📈 Matrix: {len(self.view_dialog.display_matrix)} Zeilen")
            
            if not controls:
                logger.warning("⚠️ Keine Controls verfügbar - erstelle Fallback")
                self._create_fallback_table()
                return
            
            # 🎯 PROJEKTION: ExpertMode vs NormalMode
            visible_columns = []
            display_headers = []
            
            if expert_mode:
                # EXPERT-MODE: Alle Spalten nach expertOrder sortiert
                logger.debug("🔧 Expert-Mode: Zeige ALLE Spalten (_original + _show + dummy)")
                all_controls = [(name, config) for name, config in controls.items()]
                
                # Nach expertOrder sortieren
                all_controls.sort(key=lambda x: x[1].get('expertOrder', 999))
                
                for control_name, control_config in all_controls:
                    # UI-Parameter-Prüfung für Date-Zusätze
                    is_visible = True
                    if '_jahr_' in control_name or '_monat_' in control_name or '_tag_' in control_name:
                        ui_visible = control_config.get('ui_visible', True)
                        if not ui_visible:
                            is_visible = False
                            logger.debug(f"🚫 {control_name}: UI-Parameter show_YMD=False → nicht sichtbar")
                    
                    elif '_alter_' in control_name:
                        ui_visible = control_config.get('ui_visible', True)
                        if not ui_visible:
                            is_visible = False
                            logger.debug(f"🚫 {control_name}: UI-Parameter show_alter=False → nicht sichtbar")
                    
                    if is_visible:
                        visible_columns.append(control_name)
                        
                        # Header-Text aus Control-Config
                        header_text = control_config.get('spaltenueberschrift')
                        if not header_text:
                            clean_name = control_name.replace('_original', '').replace('_show', '')
                            header_text = clean_name.title()
                        
                        display_headers.append(header_text)
                        
            else:
                # NORMAL-MODE: Nur _show Spalten nach displayOrder sortiert
                logger.debug("👤 Normal-Mode: Zeige nur _show Spalten")
                show_controls = [(name, config) for name, config in controls.items() 
                               if config.get('show', False) and name.endswith('_show')]
                
                # Nach displayOrder sortieren
                show_controls.sort(key=lambda x: x[1].get('displayOrder', 999))
                
                for control_name, control_config in show_controls:
                    # UI-Parameter-Prüfung für Date-Zusätze
                    is_visible = True
                    if '_jahr_' in control_name or '_monat_' in control_name or '_tag_' in control_name:
                        ui_visible = control_config.get('ui_visible', True)
                        if not ui_visible:
                            is_visible = False
                            logger.debug(f"🚫 {control_name}: UI-Parameter show_YMD=False → nicht sichtbar")
                    
                    elif '_alter_' in control_name:
                        ui_visible = control_config.get('ui_visible', True)
                        if not ui_visible:
                            is_visible = False
                            logger.debug(f"🚫 {control_name}: UI-Parameter show_alter=False → nicht sichtbar")
                    
                    if is_visible:
                        visible_columns.append(control_name)
                        
                        # Header-Text aus Control-Config
                        header_text = control_config.get('spaltenueberschrift')
                        if not header_text:
                            clean_name = control_name.replace('_show', '')
                            header_text = clean_name.title()
                        
                        display_headers.append(header_text)
            
            logger.info(f"📊 Sichtbare Spalten: {len(visible_columns)} - {visible_columns[:3]}...")
            
            if not visible_columns:
                logger.warning("⚠️ Keine sichtbaren Spalten - erstelle Fallback")
                self._create_fallback_table()
                return
            
            # 🔧 TABELLE AUFBAUEN
            matrix_rows = len(self.view_dialog.display_matrix)
            matrix_cols = len(visible_columns)
            
            self.table.setRowCount(matrix_rows)
            self.table.setColumnCount(matrix_cols)
            
            logger.info(f"📊 Tabelle: {matrix_rows} Zeilen × {matrix_cols} Spalten")
            
            # Enhanced Headers setzen
            self._set_enhanced_headers(display_headers, visible_columns, expert_mode)
            
            # 🔧 DATEN EINFÜLLEN MIT FEHLERBEHANDLUNG
            filled_cells = 0
            for row_idx, row_data in enumerate(self.view_dialog.display_matrix):
                for col_idx, column_name in enumerate(visible_columns):
                    try:
                        # Wert aus Matrix holen mit Fallback
                        value = row_data.get(column_name, '')
                        if value is None:
                            value = ''
                        
                        item = QTableWidgetItem(str(value))
                        
                        # Tooltip für Expert-Mode
                        if expert_mode:
                            tooltip_parts = [f"Feld: {column_name}"]
                            if value:
                                tooltip_parts.append(f"Wert: {value}")
                            item.setToolTip(" | ".join(tooltip_parts))
                        
                        self.table.setItem(row_idx, col_idx, item)
                        filled_cells += 1
                        
                    except Exception as cell_error:
                        logger.warning(f"⚠️ Fehler bei Zelle [{row_idx}, {col_idx}]: {cell_error}")
                        # Leere Zelle bei Fehler
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(''))
            
            logger.info(f"📊 {filled_cells} Zellen gefüllt")
            
            # Tabelle konfigurieren
            self.table.resizeColumnsToContents()
            header = self.table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.Interactive)
            
            # Status aktualisieren
            mode_text = "Expert-Mode" if expert_mode else "Normal-Mode"
            projected_columns = len(visible_columns)
            self.status_label.setText(
                f"{matrix_rows} Datensätze | {projected_columns} Spalten | {mode_text} | {filled_cells} Zellen"
            )
            
            logger.info(f"✅ Tabelle erfolgreich aufgebaut: {matrix_rows} Zeilen, {projected_columns} Spalten ({mode_text})")
            logger.info(f"🎯 Projektion: {projected_columns} von {len(controls)} Controls sichtbar")
            
        except Exception as e:
            logger.error(f"❌ Kritischer Fehler beim Tabellen-Aufbau: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self._create_fallback_table()
    
    def _set_enhanced_headers(self, headers, col_names, expert_mode):
        """Enhanced Headers wie im Original Widget setzen"""
        header = self.table.horizontalHeader()
        
        if expert_mode:
            # Expert-Mode: Zweizeilige Header mit \n
            enhanced_headers = []
            for header_text, col_name in zip(headers, col_names):
                two_line_header = f"{header_text}\n({col_name})"
                enhanced_headers.append(two_line_header)
            
            self.table.setHorizontalHeaderLabels(enhanced_headers)
            
            # Expert-Mode Styling
            header.setMinimumHeight(55)
            header.setStyleSheet("""
                QHeaderView::section {
                    font-weight: bold;
                    font-size: 10pt;
                    padding: 6px 4px;
                    border: 1px solid #ddd;
                    background-color: #e8f4fd;
                    color: #2c3e50;
                    text-align: center;
                }
                QHeaderView::section:hover {
                    background-color: #d4edda;
                }
            """)
        else:
            # Normal-Mode: Standard einzeilige Header
            self.table.setHorizontalHeaderLabels([str(h) for h in headers])
            
            # Normal-Mode Styling
            header.setMinimumHeight(35)
            header.setStyleSheet("""
                QHeaderView::section {
                    font-weight: bold;
                    font-size: 11pt;
                    padding: 6px;
                    border: 1px solid #ddd;
                    background-color: #f5f5f5;
                    color: #2c3e50;
                }
            """)
    
    def _create_fallback_table(self):
        """Fallback-Tabelle wie im Original Widget"""
        logger.info("🔧 Erstelle Fallback-Tabelle...")
        
        headers = ["GUID", "Vorname", "Nachname", "Geburtsdatum", "Status"]
        col_names = ["guid", "vorname", "nachname", "geburtsdatum", "status"]
        
        self.table.setColumnCount(len(headers))
        self._set_enhanced_headers(headers, col_names, False)
        
        # Test-Daten
        test_data = [
            ["54073c2c", "Test", "Person", "01.01.1980", "Aktiv"],
            ["test-guid", "Fallback", "Modus", "Dialog Error", "Debug"]
        ]
        
        self.table.setRowCount(len(test_data))
        for row_idx, row_data in enumerate(test_data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                self.table.setItem(row_idx, col_idx, item)
        
        self.table.resizeColumnsToContents()
        self.status_label.setText(f"{len(test_data)} Test-Datensätze | Fallback-Modus")
        
        logger.info(f"✅ Fallback-Tabelle erstellt mit {len(test_data)} Test-Zeilen")
    
    def _toggle_expert_mode(self):
        """🔧 3. EXPERT-MODE FIX: Korrekte Systemsteuerung-Synchronisation"""
        try:
            current_mode = gcs.expert_mode
            new_mode = not current_mode
            
            logger.info(f"🔧 Expert-Mode umschalten: {current_mode} → {new_mode}")
            
            # 🔧 GLOBALE SYSTEMSTEUERUNG-SYNCHRONISATION:
            # Direkter Property-Zugriff auf globale Instanz
            gcs.expert_mode = new_mode
            
            logger.info(f"✅ Expert-Mode umgeschaltet und gespeichert: {new_mode}")
            
            # UI aktualisieren
            self.refresh_table()
            
            # Settings-Menü aktualisieren (Expert-Mode Checkbox)
            self._create_settings_menu()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Expert-Mode Umschalten: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Benutzerfreundliche Fehlermeldung
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Expert-Mode Fehler", 
                              f"Expert-Mode konnte nicht umgeschaltet werden:\n\n{str(e)}")
    
    def _toggle_filter(self):
        """Filter Toggle (noch ohne Funktion)"""
        logger.info("🔍 Filter Toggle geklickt (noch ohne Funktion)")
        QMessageBox.information(self, "Filter", "Filter-Funktion ist noch nicht implementiert.")


# Integration in MainApp
def integrate_pdvm_modern_view(main_app):
    """9. Integration in MainApp.pdvm_modern_view"""
    
    def pdvm_modern_view(self, view_guid, user_guid, title=None):
        """
        Moderne View-Widget Integration
        
        Args:
            view_guid: Die View-GUID
            user_guid: Die User-GUID 
            title: Optionaler Titel (default: "View: {view_guid}")
        
        Returns:
            QWidget: Das View-Widget für den Arbeitsbereich
        """
        logger.info(f"🚀 Starte moderne View: {view_guid} für User: {user_guid}")
        
        try:
            # call_daten vorbereiten
            call_daten = {
                "view_guid": view_guid,
                "user_guid": user_guid,
                "title": title or f"View: {view_guid}"
            }
            
            # PdvmViewDialog erstellen
            view_dialog = PdvmViewDialog(call_daten, parent=self)
            
            # Widget für Arbeitsbereich zurückgeben
            widget = view_dialog.get_display_widget()
            
            logger.info(f"✅ Moderne View erstellt: {view_guid}")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der modernen View: {e}")
            # Fallback-Widget erstellen
            from PyQt5.QtWidgets import QLabel
            error_widget = QLabel(f"Fehler beim Laden der View: {e}")
            error_widget.setStyleSheet("color: red; padding: 20px;")
            return error_widget
    
    # Methode in MainApp einbinden
    main_app.pdvm_modern_view = pdvm_modern_view.__get__(main_app, main_app.__class__)
    logger.info("✅ pdvm_modern_view in MainApp integriert")


if __name__ == "__main__":
    # Test der neuen Architektur
    print("=== Test PdvmViewDialog ===")
    
    # Test-call_daten
    test_call_daten = {
        "view_guid": "test-view-guid",
        "user_guid": "test-user-guid", 
        "title": "Test Persondaten-View"
    }
    
    try:
        dialog = PdvmViewDialog(test_call_daten)
        widget = dialog.get_display_widget()
        print("✅ PdvmViewDialog und Widget erfolgreich erstellt")
    except Exception as e:
        print(f"❌ Fehler: {e}")
