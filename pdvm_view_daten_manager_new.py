#!/usr/bin/env python3
"""
NEUER PdvmViewDatenManager - Vollständig linear aufgebaut
Alle Methoden neu erstellt basierend auf der linearen Architektur
"""

import logging
import traceback
from typing import Any, Dict, List, Optional

# Logging Setup
logger = logging.getLogger(__name__)

class ColumnControl:
    """Vereinfachte Column Control Klasse"""
    
    def __init__(self):
        self.columns = []
        self.row_guids = []
        self.column_data = {}
        
        # Sortierungsstack für Mehrebenen-Sortierung
        self.sort_stack = []   # [('anrede_show', 'asc'), ('familienname_show', 'asc'), ...]
        
    def add_column(self, name: str, col_type: str, order: int, **kwargs):
        """Fügt eine Spalte hinzu"""
        column = {
            'name': name,
            'type': col_type,
            'order': order,
            **kwargs
        }
        self.columns.append(column)
        
    def set_row_data(self, guid: str, row_dict: dict):
        """Setzt alle Spaltenwerte für eine GUID"""
        if guid not in self.row_guids:
            self.row_guids.append(guid)
        
        for column_name, value in row_dict.items():
            if column_name not in self.column_data:
                self.column_data[column_name] = {}
            self.column_data[column_name][guid] = value
            
    def get_row_data(self, guid: str):
        """Holt alle Spaltenwerte für eine GUID"""
        row_data = {}
        for column_name in self.column_data.keys():
            row_data[column_name] = self.column_data[column_name].get(guid, "")
        return row_data
    
    def get_display_table_data(self, show_columns_only=True):
        """
        Bereitet Daten für Tabellenanzeige vor
        """
        # Zeilen in der Reihenfolge der row_guids
        display_data = []
        for guid in self.row_guids:
            row_dict = {'uid_original': guid}  # GUID immer dabei
            for column_name in self.column_data.keys():
                row_dict[column_name] = self.column_data[column_name].get(guid, "")
            display_data.append(row_dict)
        
        # Spalten filtern wenn gewünscht (nur _show Spalten)
        if show_columns_only:
            display_columns = [col['name'] for col in self.columns if col['name'].endswith('_show') or col['name'] == 'uid_original']
        else:
            display_columns = [col['name'] for col in self.columns]
        
        # Gefilterte Daten
        filtered_data = []
        for row in display_data:
            display_row = {col: row.get(col, "") for col in display_columns}
            filtered_data.append(display_row)
        
        return filtered_data, display_columns
    
    def get_expert_mode_headers(self, display_columns):
        """
        Erstellt zweizeilige Header für ExpertMode
        """
        headers = []
        for col_name in display_columns:
            if col_name.endswith('_show'):
                # Basis-Namen extrahieren
                base_name = col_name.replace('_show', '')
                headers.append(f"{base_name}\n(Show)")
            elif col_name.endswith('_original'):
                base_name = col_name.replace('_original', '')
                headers.append(f"{base_name}\n(Original)")
            else:
                headers.append(col_name)
        return headers
    
    def add_sort_level(self, column_name: str, direction: str = 'asc'):
        """
        Fügt eine Sortierebene hinzu
        Beispiel: add_sort_level('anrede_show', 'asc')
        """
        # Entferne existing level für diese Spalte
        self.sort_stack = [(col, dir) for col, dir in self.sort_stack if col != column_name]
        # Füge als neue oberste Ebene hinzu
        self.sort_stack.insert(0, (column_name, direction))
    
    def remove_sort_level(self, column_name: str):
        """Entfernt eine Sortierebene"""
        self.sort_stack = [(col, dir) for col, dir in self.sort_stack if col != column_name]
    
    def apply_multi_level_sort(self):
        """
        Wendet Mehrebenen-Sortierung an
        Sortiert self.row_guids basierend auf sort_stack
        """
        if not self.sort_stack:
            return
            
        # Sortierungsschlüssel-Funktion
        def sort_key(guid):
            key_values = []
            for column_name, direction in reversed(self.sort_stack):  # Reverse für korrekte Priorität
                value = self.column_data.get(column_name, {}).get(guid, "")
                
                # Wert für Sortierung aufbereiten
                if isinstance(value, str):
                    sort_value = value.lower()  # Case-insensitive
                elif isinstance(value, (int, float)):
                    sort_value = value
                else:
                    sort_value = str(value).lower()
                
                # Bei DESC-Sortierung negieren (für numerische Werte) oder umkehren
                if direction == 'desc':
                    if isinstance(sort_value, (int, float)):
                        sort_value = -sort_value
                    else:
                        # Für Strings: reverse ordering durch Umkehrung
                        sort_value = ''.join(chr(255-ord(c)) for c in str(sort_value)[:50])  # Limit für Performance
                        
                key_values.append(sort_value)
            return tuple(key_values)
        
        # Sortierung anwenden
        self.row_guids.sort(key=sort_key)


class PdvmViewDatenManager:
    """
    NEUER LINEAR AUFGEBAUTER Daten Manager
    Komplett neu erstellt mit linearer Architektur
    """
    
    def __init__(self, call_daten, widget=None, parent_app=None):
        self.call_daten = call_daten
        self.widget = widget
        self._parent_app = parent_app
        
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.mode = call_daten.get("mode", "user")
        self.first_call = call_daten.get("first_call", True)
        
        # Aktueller View-Mode
        self.current_view_mode = "expert"
        
        # Column Control System
        self.column_control = None
        self.basis_columns = []
        self.basis_data = []
        
        logger.info(f"🔧 NEUER LINEAR aufgebauter DatenManager gestartet")
        logger.info(f"📋 View: {self.view_guid}, First Call: {self.first_call}")
        
        # Daten laden
        self._build_system()
    
    @property
    def stichtag(self):
        """Zentrale Stichtag-Property"""
        try:
            if (hasattr(self, '_parent_app') and self._parent_app and 
                hasattr(self._parent_app, 'stichtag_manager') and 
                self._parent_app.stichtag_manager):
                return self._parent_app.stichtag_manager.akt_stichtag
            return 1001.0
        except:
            return 1001.0
    
    def _build_system(self):
        """
        SCHRITT-FÜR-SCHRITT AUFBAU:
        1. ViewDaten laden
        2. Controls aufbauen
        3. Daten laden
        """
        try:
            logger.info("🔧 SCHRITT 1: ViewDaten laden")
            view_felder = self._load_view_felder()
            
            logger.info("🔧 SCHRITT 2: Column Controls aufbauen")
            self.column_control = self._build_column_controls(view_felder)
            
            logger.info("🔧 SCHRITT 3: Basis-Spalten ableiten")
            self.basis_columns = self._get_columns_from_controls()
            
            logger.info("🔧 SCHRITT 4: Daten laden (falls first_call)")
            if self.first_call:
                records_loaded = self._load_records_data(limit=100)
                logger.info(f"✅ {records_loaded} Datensätze geladen")
            else:
                logger.info("📊 SKIP: Datenladen übersprungen (first_call=False)")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim System-Aufbau: {e}")
            traceback.print_exc()
            raise
    
    def _load_view_felder(self):
        """SCHRITT 1: ViewDaten-Felder laden"""
        try:
            if not self.first_call:
                logger.info("📊 SKIP: ViewDaten bereits geladen")
                return []
            
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten", 
                guid=self.view_guid
            )
            
            view_table = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not view_table:
                raise ValueError("VIEW_TABLE nicht gefunden")
            
            view_metadaten = view_db.get_static_value(gruppe='METADATEN', feld=view_table.upper())
            if not view_metadaten or 'felder' not in view_metadaten:
                raise ValueError("ViewDaten-Felder nicht gefunden")
                
            felder = view_metadaten['felder']
            logger.info(f"📋 {len(felder)} ViewDaten-Felder geladen für Tabelle '{view_table}'")
            
            # Tabelle für spätere Verwendung speichern
            self.view_table = view_table
            
            return felder
            
        except Exception as e:
            logger.error(f"❌ Fehler beim ViewDaten-Laden: {e}")
            raise
    
    def _build_column_controls(self, view_felder):
        """
        SCHRITT 2: Column Controls linear aufbauen
        1. _original Spalten mit Zusatzspalten für date
        2. _show Spalten aus allen _original Spalten
        3. dummy Spalte
        """
        try:
            column_control = ColumnControl()
            order = 0
            
            # PHASE 1: System uid_original
            column_control.add_column(
                "uid_original", "system_original", order,
                field_config={"anzeige": "ID (Original)"},
                anzeige="ID (Original)", show=False, expert=True
            )
            order += 1
            logger.info("   ✅ uid_original Control erstellt")
            
            # PHASE 2: Alle _original Spalten (inkl. date Zusatzspalten)
            for feld_config in view_felder:
                feldname_gross = feld_config["feld"]
                feld_name = feldname_gross.lower()
                feld_type = feld_config.get("type", "string")
                gruppe = feld_config.get("gruppe", "PERSDATEN")
                anzeige = feld_config.get("name", feld_name.capitalize())
                
                # Haupt _original Spalte
                column_control.add_column(
                    f"{feld_name}_original", feld_type, order,
                    field_config=feld_config, gruppe=gruppe, feld=feldname_gross,
                    anzeige=f"{anzeige} (Original)", show=False, expert=True
                )
                order += 1
                logger.info(f"   ✅ {feld_name}_original Control erstellt (type: {feld_type})")
                
                # Bei Date: Zusatzspalten
                if feld_type == "date":
                    for zusatz in ["alter", "jahr", "monat", "tag"]:
                        zusatz_field_config = feld_config.copy()
                        zusatz_field_config["type"] = f"date_{zusatz}"
                        
                        column_control.add_column(
                            f"{feld_name}_{zusatz}_original", f"date_{zusatz}", order,
                            field_config=zusatz_field_config, gruppe=gruppe, feld=feldname_gross,
                            anzeige=f"{anzeige} {zusatz.capitalize()} (Original)", 
                            show=False, expert=True
                        )
                        order += 1
                        logger.info(f"   ✅ {feld_name}_{zusatz}_original Control erstellt (type: date_{zusatz})")
            
            # PHASE 3: Alle _show Spalten aus _original Spalten ableiten
            logger.info("🔧 PHASE 3: _show Spalten aus _original ableiten")
            
            # System uid_show
            column_control.add_column(
                "uid_show", "system_show", order,
                field_config={"anzeige": "ID"},
                anzeige="ID", show=True, expert=False
            )
            order += 1
            logger.info("   ✅ uid_show Control erstellt")
            
            # Für jede _original Spalte eine _show erstellen
            original_columns = [col for col in column_control.columns 
                              if col['name'].endswith('_original') and col['name'] != 'uid_original']
            
            for orig_col in original_columns:
                orig_name = orig_col['name']
                show_name = orig_name.replace('_original', '_show')
                
                # Type bleibt gleich (aus ViewDaten)
                orig_type = orig_col['type']
                show_type = orig_type  # Type aus ViewDaten beibehalten
                
                # UI-Parameter für Sichtbarkeit
                field_config = orig_col.get('field_config', {})
                ui_params = field_config.get('ui', {})
                
                # Standard: Haupt-Show-Spalten sind sichtbar, Zusatz-Spalten nur bei UI-Flag
                if not orig_type.startswith("date_"):
                    # Normale Felder (string, date, etc.)
                    show_visible = True
                elif orig_type == "date_alter":
                    show_visible = ui_params.get("show_alter", False)
                elif orig_type in ["date_jahr", "date_monat", "date_tag"]:
                    show_visible = ui_params.get("show_YMD", False)
                else:
                    show_visible = False
                
                column_control.add_column(
                    show_name, show_type, order,
                    field_config=field_config,
                    gruppe=orig_col.get('gruppe'), 
                    feld=orig_col.get('feld'),
                    anzeige=orig_col.get('anzeige', '').replace(' (Original)', ''),
                    show=show_visible, expert=False
                )
                order += 1
                logger.debug(f"   ✅ {show_name} Control erstellt (type: {show_type}, show: {show_visible})")
            
            # PHASE 4: Dummy Spalte
            column_control.add_column(
                "dummy", "dummy", order,
                field_config={}, anzeige="", show=False, expert=True
            )
            order += 1
            logger.info("   ✅ dummy Control erstellt")
            
            logger.info(f"✅ {len(column_control.columns)} Column Controls linear erstellt")
            return column_control
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Column Control Aufbau: {e}")
            traceback.print_exc()
            raise
    
    def _get_columns_from_controls(self):
        """SCHRITT 3: Basis-Spalten aus Controls ableiten"""
        try:
            columns = []
            for col_dict in self.column_control.columns:
                simple_col = {
                    'name': col_dict['name'],
                    'label': col_dict.get('anzeige', col_dict['name']),
                    'type': col_dict.get('type', 'string'),
                    'display_show': col_dict.get('show', True),
                    'display_order': col_dict.get('order', 999),
                    'display_expert': col_dict.get('expert', False),
                    'field_config': col_dict.get('field_config', {}),
                    'gruppe': col_dict.get('gruppe'),
                    'feld': col_dict.get('feld')
                }
                
                # Mode-Filter
                if self.current_view_mode == "normal" and simple_col.get('display_expert'):
                    continue
                    
                columns.append(simple_col)
            
            logger.info(f"✅ {len(columns)} Basis-Spalten für Mode: {self.current_view_mode}")
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Basis-Spalten-Aufbau: {e}")
            return []
    
    def _load_records_data(self, limit=100):
        """
        SCHRITT 4: Daten laden
        3. set_data pro Zeile 
        4. get_value pro Feld mit Zusatzspalten-Logik
        """
        try:
            if not hasattr(self, 'view_table') or not self.view_table:
                raise ValueError("view_table nicht verfügbar")
                
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Alle Datensätze laden
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.view_table,
                guid=None
            )
            
            all_records = data_db.lesen_alle_ohne_system(limit=limit)
            logger.info(f"📊 {len(all_records)} Datensätze geladen")
            
            # Datetime-Formatter
            from pdvm_datetime import Pdvm_DateTime
            dt_formatter = Pdvm_DateTime("DEU")
            
            # Pro Datensatz verarbeiten
            successful_records = 0
            working_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db", 
                table_name=self.view_table,
                guid=None
            )
            
            for i, record_info in enumerate(all_records):
                try:
                    data_guid = record_info["uid"]
                    data_dict = record_info["daten_dict"]
                    
                    # 3. set_data pro Zeile
                    working_db.set_data(data_dict, data_guid)
                    
                    # Row-Record erstellen
                    row_record = {'uid_original': data_guid}
                    
                    # 4. get_value pro _original Feld
                    self._fill_original_columns(row_record, working_db, dt_formatter)
                    
                    # 5. _show Spalten aus _original übertragen (erstmal 1:1)
                    self._fill_show_columns(row_record)
                    
                    # In Column Control speichern
                    self.column_control.set_row_data(data_guid, row_record)
                    successful_records += 1
                    
                    if (i + 1) % 20 == 0:
                        logger.info(f"   📊 {i+1}/{len(all_records)} Datensätze verarbeitet...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Fehler bei Datensatz {record_info.get('uid', 'unbekannt')}: {e}")
                    continue
            
            logger.info(f"✅ {successful_records} Datensätze erfolgreich geladen")
            return successful_records
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Daten-Laden: {e}")
            traceback.print_exc()
            return 0
    
    def _fill_original_columns(self, row_record: dict, working_db, dt_formatter):
        """
        SCHRITT 4: _original Spalten befüllen
        Linear durch alle _original Spalten, mit get_value + Zusatzspalten-Logik
        """
        try:
            for col in self.basis_columns:
                col_name = col['name']
                
                if not col_name.endswith('_original') or col_name == 'uid_original':
                    continue
                
                col_type = col.get('type', '')
                gruppe = col.get('gruppe', 'PERSDATEN') 
                feld = col.get('feld')
                
                # Unterscheidung: Normale _original Spalten vs. date_* Zusatzspalten
                if not col_type.startswith("date_"):
                    # Normale _original Spalte (date, string, etc.): get_value
                    if feld and gruppe:
                        try:
                            wert = working_db.get_value(gruppe, feld, ab_zeit=self.stichtag)
                            row_record[col_name] = wert if wert is not None else ""
                            logger.debug(f"✅ {col_name} = {wert} (get_value)")
                        except Exception as e:
                            logger.debug(f"⚠️ get_value Fehler für {col_name}: {e}")
                            row_record[col_name] = ""
                    else:
                        row_record[col_name] = ""
                        
                else:
                    # Zusatzspalte: Aus Ursprungsspalte ableiten
                    zusatz_typ = col_type.replace("date_", "")  # alter, jahr, monat, tag
                    
                    # Ursprungsspalten-Name ermitteln (z.B. geburtsdatum_alter_original -> geburtsdatum_original)
                    basis_col_name = col_name.replace(f"_{zusatz_typ}_original", "_original")
                    
                    # Prüfen ob Basis-Spalte schon befüllt ist
                    if basis_col_name in row_record:
                        basis_wert_raw = row_record[basis_col_name]
                        # Wenn es ein Dict ist (historische Daten), den Wert extrahieren
                        if isinstance(basis_wert_raw, dict) and 'wert' in basis_wert_raw:
                            basis_wert = basis_wert_raw['wert']
                        else:
                            basis_wert = basis_wert_raw
                            
                        if isinstance(basis_wert, (int, float)) and basis_wert > 0:
                            zusatz_wert = self._berechne_datum_zusatz(basis_wert, zusatz_typ, dt_formatter)
                            row_record[col_name] = zusatz_wert
                            logger.debug(f"✅ {col_name} = {zusatz_wert} (berechnet aus {basis_wert})")
                        else:
                            row_record[col_name] = ""
                    else:
                        # Basis-Spalte noch nicht da, aus DB holen
                        if feld and gruppe:
                            try:
                                basis_wert_raw = working_db.get_value(gruppe, feld, ab_zeit=self.stichtag)
                                # Wenn es ein Dict ist (historische Daten), den Wert extrahieren
                                if isinstance(basis_wert_raw, dict) and 'wert' in basis_wert_raw:
                                    basis_wert = basis_wert_raw['wert']
                                else:
                                    basis_wert = basis_wert_raw
                                    
                                if isinstance(basis_wert, (int, float)) and basis_wert > 0:
                                    zusatz_wert = self._berechne_datum_zusatz(basis_wert, zusatz_typ, dt_formatter)
                                    row_record[col_name] = zusatz_wert
                                    logger.debug(f"✅ {col_name} = {zusatz_wert} (berechnet aus DB: {basis_wert})")
                                else:
                                    row_record[col_name] = ""
                            except Exception as e:
                                logger.debug(f"⚠️ get_value Fehler für Zusatzspalte {col_name}: {e}")
                                row_record[col_name] = ""
                        else:
                            row_record[col_name] = ""
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der _original Spalten: {e}")
    
    def _berechne_datum_zusatz(self, original_datum: float, zusatz_typ: str, dt_formatter):
        """Berechnet Datum-Zusatzwerte"""
        try:
            dt_formatter.PdvmDateTime = original_datum
            
            if zusatz_typ == "alter":
                try:
                    from pdvm_datetime import Pdvm_DateTime
                    dt_stichtag = Pdvm_DateTime("DEU")
                    dt_stichtag.PdvmDateTime = self.stichtag
                    return dt_stichtag.Year - dt_formatter.Year
                except:
                    import datetime
                    return datetime.datetime.now().year - dt_formatter.Year
            elif zusatz_typ == "jahr":
                return dt_formatter.Year
            elif zusatz_typ == "monat":
                return dt_formatter.Month
            elif zusatz_typ == "tag":
                return dt_formatter.Day
            else:
                return ""
        except Exception as e:
            logger.debug(f"❌ Datum-Zusatz-Berechnung Fehler ({zusatz_typ}): {e}")
            return ""
    
    def _fill_show_columns(self, row_record: dict):
        """
        SCHRITT 5: _show Spalten befüllen
        Erstmal einfach: 1:1 aus _original übertragen mit besserer Behandlung
        """
        try:
            # System uid_show
            if 'uid_original' in row_record:
                guid = row_record['uid_original']
                row_record['uid_show'] = guid[:8] + "..." if guid else ""
            
            # Alle anderen _show Spalten
            for col in self.basis_columns:
                col_name = col['name']
                col_type = col['type']
                
                if not col_name.endswith('_show') or col_name == 'uid_show':
                    continue
                
                # Entsprechende _original Spalte finden
                original_col_name = col_name.replace('_show', '_original')
                
                if original_col_name in row_record:
                    original_wert = row_record[original_col_name]
                    
                    # Bei normalen Feldern: Historische Dictionaries zu lesbaren Werten
                    if not col_type.startswith("date_") and isinstance(original_wert, dict) and 'wert' in original_wert:
                        # Für Datum: PdvmDateTime Formatierung
                        if col_type == "date" and isinstance(original_wert['wert'], (int, float)):
                            try:
                                from pdvm_datetime import Pdvm_DateTime
                                dt_formatter = Pdvm_DateTime("DEU")
                                dt_formatter.PdvmDateTime = original_wert['wert']
                                formatted_value = dt_formatter.Date_formatted
                                row_record[col_name] = formatted_value
                                logger.debug(f"✅ {col_name} = {formatted_value} (formatiert aus {original_wert['wert']})")
                            except Exception as e:
                                row_record[col_name] = str(original_wert['wert'])
                                logger.debug(f"⚠️ {col_name} = {original_wert['wert']} (Fallback: {e})")
                        else:
                            # Normaler Wert aus dict
                            row_record[col_name] = str(original_wert['wert']) if original_wert['wert'] is not None else ""
                    else:
                        # Bei date_* types: 1:1 übertragen (bereits berechnet)
                        row_record[col_name] = original_wert if original_wert is not None else ""
                        logger.debug(f"✅ {col_name} = {original_wert} (1:1 aus {original_col_name})")
                else:
                    row_record[col_name] = ""
                    logger.debug(f"⚠️ {col_name} = '' (keine _original Spalte)")
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der _show Spalten: {e}")
    
    # ===========================================
    # API METHODEN für Widget-Integration
    # ===========================================
    
    def get_table_data_for_display(self, show_only=True):
        """Holt Tabellen-Daten für Widget-Anzeige"""
        try:
            if not self.column_control:
                return [], []
            
            # Spalten filtern
            if show_only:
                display_columns = [col['name'] for col in self.basis_columns 
                                 if col['name'].endswith('_show') or col['name'] == 'uid_original']
            else:
                display_columns = [col['name'] for col in self.basis_columns]
            
            # Daten sammeln
            display_data = []
            for guid in self.column_control.row_guids:
                row_data = self.column_control.get_row_data(guid)
                display_row = tuple(row_data.get(col, "") for col in display_columns)
                display_data.append(display_row)
            
            return display_data, display_columns
            
        except Exception as e:
            logger.error(f"❌ Fehler bei get_table_data_for_display: {e}")
            return [], []
    
    def get_columns_for_mode(self, mode):
        """Holt Spalten-Config für einen bestimmten Mode"""
        # Für jetzt: Einfach basis_columns zurückgeben
        return self.basis_columns.copy()
