#!/usr/bin/env python3
"""
PDVM View Daten Manager - LINEARE ARCHITEKTUR
===============================================

Vollständig neu aufgebaut mit linearer Logik:
1. Controls aus ViewDaten mit echten Types aufbauen
2. Date-Zusatzspalten bei type=date automatisch erstellen  
3. _show Spalten linear aus _original ableiten
4. PdvmCentralDatenbank pro Zeile/Feld verwenden
5. Zusatzspalten aus Ursprungsspalte berechnen
"""

import logging
import traceback
from typing import Any, Dict, List, Optional
from pdvm_central_datenbank import PdvmCentralDatenbank

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
                    # date_* Zusatzspalte: Aus Ursprungsspalte ableiten
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
    
    # ===========================================
    # LEGACY KOMPATIBILITÄT
    # ===========================================
    
    def get_columns(self):
        """Legacy: Gibt Spalten zurück"""
        return self.basis_columns
    
    def get_data(self):
        """Legacy: Gibt Daten zurück"""
        data, columns = self.get_table_data_for_display()
        return data
    
    def reload_data(self):
        """Legacy: Daten neu laden"""
        try:
            logger.info("🔄 Daten neu laden...")
            if hasattr(self, 'view_table') and self.view_table:
                records_loaded = self._load_records_data(limit=100)
                logger.info(f"✅ {records_loaded} Datensätze neu geladen")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Fehler beim Neu-Laden: {e}")
            return False



class PdvmViewDatenManager:
    """
    FINAL EINFACHER Daten Manager
    Direkte DB-Kommunikation ohne Provider-Umwege
    """
    
    def __init__(self, call_daten, widget=None, parent_app=None):
        self.call_daten = call_daten
        self.widget = widget
        self._parent_app = parent_app  # Referenz auf MainApp für StichtagManager-Zugriff
        
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        # BEREINIGT: self.stichtag entfernt - verwende zentrale StichtagManager Property
        self.mode = call_daten.get("mode", "user")
        
        # NEU: First Call Logic für effizienten Stichtag-Refresh
        self.first_call = call_daten.get("first_call", True)
        
        # Aktueller View-Mode (normal/expert)
        self.current_view_mode = "expert"  # FIXIERT auf Expert bis System funktioniert
        
        # Column Control System
        self.column_control = None
        
        # EINFACHE Datenstrukturen
        self.basis_data = []
        self.basis_columns = []  # Spalten mit display_* Feldern
        
        logger.info(f"🔧 SCHRITTWEISER DatenManager gestartet - View: {self.view_guid}, First Call: {self.first_call}")
        
        # Daten laden mit First Call Logic
        self._load_data()
    
    @property
    def stichtag(self):
        """
        ZENTRALE STICHTAG-PROPERTY
        
        Holt den Stichtag aus dem zentralen StichtagManager.
        Diese Property ersetzt alle direkten Stichtag-Zugriffe.
        
        Returns:
            float: Aktueller Stichtag aus zentralem Manager oder Fallback
        """
        try:
            # ANSATZ 1: Über Parent-App versuchen
            if (hasattr(self, '_parent_app') and self._parent_app and 
                hasattr(self._parent_app, 'stichtag_manager') and 
                self._parent_app.stichtag_manager):
                return self._parent_app.stichtag_manager.akt_stichtag
            
            # ANSATZ 2: Über globale Funktion (ohne Logging bei Fehler)
            try:
                import sys
                import os
                import importlib.util
                
                spec = importlib.util.spec_from_file_location("systemstart", "PDVM-Systemstart.py")
                systemstart_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(systemstart_module)
                
                stichtag_manager = systemstart_module.get_global_stichtag_manager()
                if stichtag_manager and hasattr(stichtag_manager, 'akt_stichtag'):
                    return stichtag_manager.akt_stichtag
            except:
                pass  # Kein Logging bei Fehler
            
            # FALLBACK: Standard-Stichtag
            return 1001.0
            
        except:
            return 1001.0
    
    def _load_data(self):
        """
        SCHRITTWEISER AUFBAU: ViewDaten laden, Column Controls bilden, Tabelle darstellen
        NEU: Berücksichtigt first_call Parameter für effizienten Refresh
        """
        try:
            logger.info("� SCHRITTWEISER AUFBAU - Beginne mit ViewDaten laden")
            
            # SCHRITT 1: ViewDaten-Felder laden (nur view_felder, nicht tables separat)
            view_felder, view_table = self._load_view_felder()
            
            # SCHRITT 2: Column Controls bilden (für jede Spalte ein Control)
            self.column_control = self._create_column_controls(view_felder)
            
            # SCHRITT 3: Basis für Tabelle bilden und darstellen
            self.basis_columns = self._get_columns_from_controls()
            self.basis_data = []  # Daten folgen in nächstem Schritt
            
            logger.info(f"✅ Grundsystem aufgebaut: {len(self.basis_columns)} Column Controls")
            
            # SCHRITT 4: AUTOMATISCH DATENSÄTZE LADEN
            logger.info("📊 AUTOMATISCHES LADEN: Lade Datensätze für View")
            try:
                records_loaded = self.load_records_data(limit=100)  # Standard-Limit
                
                if records_loaded > 0:
                    logger.info(f"✅ ViewManager vollständig initialisiert: {records_loaded} Datensätze geladen")
                else:
                    logger.warning("⚠️ ViewManager initialisiert, aber keine Datensätze geladen")
            except Exception as data_error:
                logger.warning(f"⚠️ Automatisches Datenladen fehlgeschlagen: {data_error}")
                logger.info("📊 ViewManager trotzdem bereit (ohne Daten)")
            
        except Exception as e:
            logger.error(f"❌ FEHLER beim Grundsystem-Aufbau: {e}")
            raise RuntimeError(f"Grundsystem-Aufbau fehlgeschlagen: {e}") from e
    
    def _load_view_felder(self):
        """
        SCHRITT 1: ViewDaten-Felder laden (nur view_felder, tables nicht separat)
        Hinweis: Datenstrukturen sind in Großbuchstaben gehalten
        """
        try:
            # NEU: First Call Logic - bei Refresh keine DB-Abfrage
            if not self.first_call:
                logger.info("📊 SKIP: DB-Laden übersprungen (first_call=False)")
                # Verwende bereits geladene Daten für Stichtag-Update
                return
            
            logger.info("📊 VOLLSTÄNDIGES LADEN: Daten aus DB (first_call=True)")
            
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # ViewDaten-Datenbank öffnen
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=self.view_guid
            )
            
            # ViewDaten über get_value laden
            view_table = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')

            if view_table:
                # Felder aus METADATEN extrahieren: GRUPPE=METADATEN, FELD=view_table.upper()
                # Da ViewDaten historie=false hat, können wir get_static_value verwenden
                view_metadaten = view_db.get_static_value(gruppe='METADATEN', feld=view_table.upper())
                felder = view_metadaten['felder']  # Hier sind die tatsächlichen Felder drin
                logger.info(f"📋 ViewDaten-Felder geladen: {len(felder)} für Tabelle '{view_table}' aus GRUPPE=METADATEN, FELD={view_table.upper()} (get_static_value)")
                return felder, view_table
                    
            logger.error("❌ Keine ViewDaten gefunden")
            raise ValueError("ViewDaten nicht gefunden oder unvollständig")
                
        except Exception as e:
            logger.error(f"❌ FEHLER beim ViewDaten-Laden: {e}")
            raise RuntimeError(f"ViewDaten-Zugriff fehlgeschlagen: {e}") from e
    
    def _create_column_controls(self, view_felder):
        """
        SCHRITT 2: Column Controls bilden - für jede Spalte ein Control mit Attributen
        Reihenfolge:
        1. uid_original + für jedes Feld eine _original Spalte 
        2. Bei type=date: Zusatzspalten _original (alter, jahr, monat, tag)
        3. Zu jeder _original eine _show Spalte hinzufügen
        4. Dummy Spalte am Ende
        """
        try:
            logger.info("🔧 SCHRITT 2: Bilde Column Controls")
            
            column_control = ColumnControl()
            order = 0

            # PHASE 1: System uid_original Spalte
            column_control.add_column(
                "uid_original", "system_original", order,
                field_config={"anzeige": "ID (Original)", "label": "uid_original"},
                gruppe=None, feld=None, anzeige="ID (Original)",
                show=False, expert=True
            )
            order += 1
            logger.info(f"   ✅ uid_original Control erstellt")

            # PHASE 2: Für jedes Feld eine _original Spalte + bei Datum Zusatzspalten
            original_count = 0
            for feld_config in view_felder:
                feldname_gross = feld_config["feld"]  # Korrekte Feldname (kleinbuchstaben im JSON)
                feld_name = feldname_gross.lower()
                feld_type = feld_config.get("type", "string")
                gruppe = feld_config.get("gruppe", "DATEN")
                anzeige = feld_config.get("name") or feld_name.capitalize()
                
                # _original Spalte hinzufügen
                column_control.add_column(
                    f"{feld_name}_original", "field_original", order,
                    field_config=feld_config, gruppe=gruppe, feld=feldname_gross, 
                    anzeige=f"{anzeige} (Original)", show=False, expert=True
                )
                order += 1
                original_count += 1
                logger.info(f"   ✅ {feld_name}_original Control erstellt")

                # Bei Date-Feldern: Zusatzspalten _original hinzufügen
                if feld_type == "date":
                    for zusatz in ["alter", "jahr", "monat", "tag"]:
                        # 🎯 NEU: Spezifische Field-Config für jeden Zusatz-Typ
                        zusatz_field_config = feld_config.copy()
                        zusatz_field_config["type"] = f"date_{zusatz}"  # date_alter, date_jahr, etc.
                        
                        column_control.add_column(
                            f"{feld_name}_{zusatz}_original", "field_original", order,
                            field_config=zusatz_field_config, gruppe=gruppe, feld=feldname_gross,
                            anzeige=f"{anzeige} {zusatz.capitalize()} (Original)", 
                            show=False, expert=True
                        )
                        order += 1
                        original_count += 1
                        logger.info(f"   ✅ {feld_name}_{zusatz}_original Control erstellt (field_type: date_{zusatz})")

            logger.info(f"   📊 PHASE 2 abgeschlossen: {original_count} _original Controls erstellt")

            # PHASE 3: Zu jeder _original eine _show Spalte hinzufügen (eigener Durchlauf)
            show_count = 0
            
            # System uid_show Spalte
            column_control.add_column(
                "uid_show", "system_show", order,
                field_config={"anzeige": "ID", "label": "uid_show"},
                gruppe=None, feld=None, anzeige="ID",
                show=True, expert=False
            )
            order += 1
            show_count += 1
            logger.info(f"   ✅ uid_show Control erstellt")
            
            # Für jedes Feld die _show Spalten
            for feld_config in view_felder:
                feldname_gross = feld_config["feld"]  # Korrekte Feldname
                feld_name = feldname_gross.lower()
                feld_type = feld_config.get("type", "string")
                gruppe = feld_config.get("gruppe", "DATEN")
                anzeige = feld_config.get("name") or feld_name.capitalize()
                
                # UI-Parameter aus feld_config extrahieren
                ui_params = feld_config.get("ui", {})
                
                # Haupt _show Spalte hinzufügen  
                column_control.add_column(
                    f"{feld_name}_show", "field_show", order,
                    field_config=feld_config, gruppe=gruppe, feld=feldname_gross,
                    anzeige=anzeige, show=True, expert=False
                )
                order += 1
                show_count += 1
                logger.info(f"   ✅ {feld_name}_show Control erstellt")
                
                # Bei Date-Feldern: Zusatz _show Spalten hinzufügen
                if feld_type == "date":
                    ui_show_alter = ui_params.get("show_alter", False)
                    ui_show_YMD = ui_params.get("show_YMD", False)
                    
                    for zusatz in ["alter", "jahr", "monat", "tag"]:
                        # 🎯 NEU: Spezifische Field-Config für jeden Zusatz-Typ
                        zusatz_field_config = feld_config.copy()
                        zusatz_field_config["type"] = f"date_{zusatz}"  # date_alter, date_jahr, etc.
                        
                        show_zusatz = (zusatz == "alter" and ui_show_alter) or (zusatz in ["jahr", "monat", "tag"] and ui_show_YMD)
                        column_control.add_column(
                            f"{feld_name}_{zusatz}_show", "field_show", order,
                            field_config=zusatz_field_config, gruppe=gruppe, feld=feldname_gross,
                            anzeige=f"{anzeige} {zusatz.capitalize()}", show=show_zusatz, expert=False
                        )
                        order += 1
                        show_count += 1
                        logger.info(f"   ✅ {feld_name}_{zusatz}_show Control erstellt (show: {show_zusatz}, field_type: date_{zusatz})")

            logger.info(f"   📊 PHASE 3 abgeschlossen: {show_count} _show Controls erstellt")

            # PHASE 4: Dummy Spalte hinzufügen (für den Fall dass alle Spalten abgewählt werden)
            column_control.add_column(
                "dummy", "dummy", order,
                field_config={}, gruppe=None, feld=None,
                anzeige="", show=False, expert=True
            )
            logger.info(f"   ✅ dummy Control erstellt")

            logger.info(f"✅ COLUMN CONTROLS erstellt: {len(column_control.columns)} Controls insgesamt")
            return column_control
            
        except Exception as e:
            logger.error(f"❌ -: {e}")
            import traceback
            traceback.print_exc()
            raise
    def _get_columns_from_controls(self):
        """
        SCHRITT 3: Basis für Tabelle aus Column Controls ableiten
        """
        try:
            logger.info("🔧 SCHRITT 3: Leite Basis-Tabellen-Struktur aus Column Controls ab")
            
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
                
                # Mode-Filter: Im Normal-Mode keine Expert-Spalten
                if self.current_view_mode == "normal" and simple_col.get('display_expert'):
                    continue
                    
                columns.append(simple_col)

            logger.info(f"✅ Basis-Tabellen-Struktur: {len(columns)} Spalten für Mode: {self.current_view_mode}")
            
            # Debug-Ausgabe der ersten Spalten
            for i, col in enumerate(columns[:5]):
                logger.info(f"   � [{i+1}] {col['name']} -> {col['label']} (show: {col['display_show']})")
            
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Basis-Tabellen-Aufbau: {e}")
            return []
    
    def _fill_all_original_columns(self, record: dict, data_dict: dict, dt_formatter, stichtag: float):
        """
        SCHRITT 2: Alle _original Spalten befüllen (übernommen aus PdvmCentralDatenbank)
        """
        logger.info(f"🔍 _fill_all_original_columns aufgerufen mit {len(self.basis_columns)} Spalten")
        logger.info(f"🔍 data_dict keys: {list(data_dict.keys()) if data_dict else 'None'}")
        
        befuellt_count = 0
        for col in self.basis_columns:
            col_name = col['name']
            
            # Nur _original Spalten verarbeiten (außer uid_original, das ist schon gesetzt)
            if not col_name.endswith("_original") or col_name == "uid_original":
                continue
                
            col_type = col.get('type', '')
            field_config = col.get('field_config', {})
            feld = col.get('feld')
            gruppe = col.get('gruppe', 'PERSDATEN')
            field_type = field_config.get('type', 'string')
            
            # 🎯 ELEGANTE LINEARE LÖSUNG: Basierend auf field_type direkt berechnen
            if field_type == 'date':
                # Haupt-Datumsspalte
                if feld and gruppe in data_dict and feld in data_dict[gruppe]:
                    wert = data_dict[gruppe][feld]
                    record[col_name] = wert
                    logger.info(f"✅ {col_name} = {wert}")
                    befuellt_count += 1
                else:
                    record[col_name] = ""
                    logger.info(f"⚠️ {col_name} = '' (nicht gefunden: feld={feld}, gruppe={gruppe})")
                    
            elif field_type.startswith('date_'):
                # Zusatzspalten: date_alter, date_jahr, date_monat, date_tag
                zusatz_typ = field_type.replace('date_', '')  # "alter", "jahr", etc.
                
                # Original-Datumswert aus der DB holen
                if feld and gruppe in data_dict and feld in data_dict[gruppe]:
                    original_datum = data_dict[gruppe][feld]
                    logger.info(f"🔍 {col_name} Original-Datum: {original_datum} (feld={feld}, gruppe={gruppe})")
                    # Basierend auf Zusatz-Typ berechnen
                    if isinstance(original_datum, (float)) and original_datum > 0:
                        zusatz_wert = self._berechne_datum_zusatz(original_datum, zusatz_typ, dt_formatter, stichtag)
                        record[col_name] = zusatz_wert
                        logger.info(f"✅ {col_name} = {zusatz_wert} (berechnet aus {original_datum})")
                        befuellt_count += 1
                    else:
                        record[col_name] = ""
                        logger.info(f"⚠️ {col_name} = '' (kein gültiges Datum: {original_datum})")
                else:
                    record[col_name] = ""
                    logger.info(f"⚠️ {col_name} = '' (nicht gefunden: feld={feld}, gruppe={gruppe})")
                    
            else:
                # Alle anderen Felder (string, dropdown, etc.)
                if feld and gruppe in data_dict and feld in data_dict[gruppe]:
                    wert = data_dict[gruppe][feld]
                    record[col_name] = wert
                    logger.info(f"✅ {col_name} = {wert}")
                    befuellt_count += 1
                else:
                    record[col_name] = ""
                    logger.info(f"⚠️ {col_name} = '' (nicht gefunden: feld={feld}, gruppe={gruppe})")
        
        logger.info(f"🔍 _original Spalten befüllt: {befuellt_count} von {len([c for c in self.basis_columns if c['name'].endswith('_original') and c['name'] != 'uid_original'])}")
    
    def _berechne_datum_zusatz(self, original_datum: float, zusatz_typ: str, dt_formatter, stichtag: float):
        """
        🎯 EINFACHE LINEARE BERECHNUNG: Datum-Zusatzwerte direkt berechnen
        
        Args:
            original_datum: PdvmDateTime Wert (z.B. 1972218.0)
            zusatz_typ: "alter", "jahr", "monat", "tag"  
            dt_formatter: Pdvm_DateTime Instanz
            stichtag: Stichtag für Alter-Berechnung
            
        Returns:
            Berechneter Zusatzwert als int/string
        """
        try:
            # Datum setzen
            dt_formatter.PdvmDateTime = original_datum
            logger.info(f"🔍 Datum gesetzt: {dt_formatter.PdvmDateTime} (Original: {original_datum})")
            logger.info(f"🔍 Jahr: {dt_formatter.Year}, Monat: {dt_formatter.Month}, Tag: {dt_formatter.Day}")
            logger.info(f"🔍 zusatz_typ: {zusatz_typ}")
            if zusatz_typ == "alter":
                # Alter berechnen
                try:
                    from pdvm_datetime import Pdvm_DateTime
                    dt_stichtag = Pdvm_DateTime("DEU")
                    dt_stichtag.PdvmDateTime = stichtag
                    alter = dt_stichtag.Year - dt_formatter.Year
                    return alter
                except:
                    # Fallback: Aktuelles Jahr verwenden
                    import datetime
                    return datetime.datetime.now().year - dt_formatter.Year
                    
            elif zusatz_typ == "jahr":
                return dt_formatter.Year
                
            elif zusatz_typ == "monat":
                return dt_formatter.Month
                
            elif zusatz_typ == "tag":
                return dt_formatter.Day
                
            else:
                logger.warning(f"⚠️ Unbekannter Zusatz-Typ: {zusatz_typ}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Datum-Zusatz-Berechnung ({zusatz_typ}): {e}")
            return ""
                    
    def _fill_all_show_columns(self, record: dict, dt_formatter):
        """
        SCHRITT 3: Alle _show Spalten befüllen (EINFACH und LINEAR)
        Geht durch alle _original Spalten und überträgt in _show Spalten
        Case-Struktur nur für 'dropdown' und 'date', alles andere 1:1
        """
        # System-Show-Spalte
        if "uid_show" in record and "uid_original" in record:
            record["uid_show"] = record["uid_original"][:8] + "..." if record["uid_original"] else ""
        
        # 🔍 DEBUG: Was haben wir in record für _original Werte?
        original_values = {k: v for k, v in record.items() if k.endswith("_original")}
        logger.info(f"🔍 DEBUG: Record _original Werte: {original_values}")
        
        # 🎯 EINFACH: Durch alle _original Spalten gehen und _show Spalten erstellen
        verarbeitet = 0
        for col in self.basis_columns:
            col_name = col['name']
            
            # Nur _original Spalten verarbeiten (außer uid_original, das ist schon behandelt)
            if not col_name.endswith("_original") or col_name == "uid_original":
                continue
                
            verarbeitet += 1
            original_wert = record.get(col_name)
                
            # Entsprechende _show Spalte ermitteln
            show_col_name = col_name.replace("_original", "_show")
            field_config = col.get('field_config', {})
            field_type = field_config.get("type", "string")
            col_type = col.get('type', '')  # Column-Typ (date_plus, field_original, etc.)
            
            # 🔍 DEBUG: Zeige Details für date_plus Spalten
            if "alter" in col_name or "jahr" in col_name or "monat" in col_name or "tag" in col_name:
                logger.info(f"🔍 DEBUG: ZUSATZ-SPALTE {col_name}:")
                logger.info(f"   original_wert = '{original_wert}'")
                logger.info(f"   show_col_name = '{show_col_name}'")
                logger.info(f"   col_type = '{col_type}'")
                logger.info(f"   field_type = '{field_type}'")
                logger.info(f"   field_config = {field_config}")
            
            # 🎯 ELEGANTE CASE-STRUKTUR: Eindeutige Field-Types
            if field_type == "dropdown":
                # Dropdown-Übersetzung
                record[show_col_name] = self._translate_dropdown_value(original_wert, field_config.get("dropdown", {}))
                logger.info(f"📊 DROPDOWN: {show_col_name} = '{record[show_col_name]}' (übersetzt aus {original_wert})")
                
            elif field_type == "date":
                # Haupt-Datum formatieren
                if isinstance(original_wert, (int, float)) and original_wert > 0:
                    dt_formatter.PdvmDateTime = original_wert
                    record[show_col_name] = dt_formatter.Date
                else:
                    record[show_col_name] = ""
                logger.info(f"📊 DATE: {show_col_name} = '{record[show_col_name]}' (formatiert aus {original_wert})")
                
            elif field_type in ["date_alter", "date_jahr", "date_monat", "date_tag"]:
                # Date-Zusatzspalten: Bereits berechnet - 1:1 übertragen
                record[show_col_name] = original_wert if original_wert is not None else ""
                logger.info(f"📊 {field_type.upper()}: {show_col_name} = '{original_wert}' (1:1 bereits berechnet)")
                
            else:
                # 🎯 DEFAULT: Alle anderen - 1:1 Übertragung
                record[show_col_name] = original_wert if original_wert is not None else ""
                logger.debug(f"📊 DEFAULT: {show_col_name} = '{original_wert}' (1:1 aus {col_name})")
                
        logger.info(f"🔍 DEBUG: {verarbeitet} _original Spalten verarbeitet")
    def _translate_dropdown_value(self, wert: Any, dropdown_config: dict) -> str:
        """
        Übersetzt Dropdown-Werte basierend auf Konfiguration
        VEREINFACHT - kann später erweitert werden für echte Dropdown-Übersetzung
        """
        if not wert:
            return ""
            
        # Für Demo: Einfache Übersetzung
        if str(wert) == "1":
            return "Frau"
        elif str(wert) == "2":
            return "Herr"
        else:
            return str(wert)
    
    def _build_columns_with_display_fields_from_viewdaten(self, view_felder):
        """
        KERNPUNKT: display_* Felder aus ViewDaten aufbauen
        Erstellt _original und _show Spalten basierend auf ViewDaten-Struktur
        KOMPLETT übernommen aus PdvmCentralDatenbank._create_column_control
        """
        try:
            
            # ColumnControl-Struktur aufbauen (wie in PdvmCentralDatenbank)
            column_structure = ColumnControl()
            order = 0

            # System-Spalten zuerst (wie im Original)
            column_structure.add_column(
                "uid_original", "system", order,
                field_config={"anzeige": "ID (Original)", "label": "uid_original"},
                gruppe=None, feld=None, anzeige="ID (Original)",
                show=False, expert=True
            )
            order += 1
            column_structure.add_column(
                "uid_show", "system", order,
                field_config={"anzeige": "ID", "label": "uid_show"},
                gruppe=None, feld=None, anzeige="ID",
                show=True, expert=False
            )
            order += 1

            # Felder aus ViewDaten verarbeiten
            for feld_config in view_felder:
                feldname_gross = feld_config["feld"]
                feld_name = feldname_gross.lower()
                feld_type = feld_config.get("type", "string")
                gruppe = feld_config.get("gruppe", "DATEN")
                anzeige = feld_config.get("name") or feld_name.capitalize()
                
                # UI-Parameter aus feld_config extrahieren
                ui_params = feld_config.get("ui", {})
                ui_sortable = ui_params.get("sortable", True)
                ui_sort_direction = ui_params.get("sortDirection", "asc")
                ui_sort_by_original = ui_params.get("sortByOriginal", False)
                ui_filter_type = ui_params.get("filterType", "contains")

                # _original Spalte hinzufügen
                column_structure.add_column(
                    f"{feld_name}_original", "original", order,
                    field_config=feld_config, gruppe=gruppe, feld=feldname_gross, 
                    anzeige=f"{anzeige} (Original)", show=False, expert=True,
                    sortable=ui_sortable, sort_direction=ui_sort_direction,
                    sort_by_original=ui_sort_by_original, filter_type=ui_filter_type
                )
                order += 1

                # _show Spalte hinzufügen  
                column_structure.add_column(
                    f"{feld_name}_show", "show", order,
                    field_config=feld_config, gruppe=gruppe, feld=feldname_gross,
                    anzeige=anzeige, show=True, expert=False,
                    sortable=ui_sortable, sort_direction=ui_sort_direction,
                    sort_by_original=ui_sort_by_original, filter_type=ui_filter_type
                )
                order += 1
                
                # Bei Date-Feldern: Zusatzspalten hinzufügen (wie im Original)
                if feld_type == "date":
                    ui_show_alter = ui_params.get("show_alter", False)
                    ui_show_YMD = ui_params.get("show_YMD", False)
                    
                    for zusatz in ["alter", "jahr", "monat", "tag"]:
                        # Original-Zusatzspalte
                        column_structure.add_column(
                            f"{feld_name}_{zusatz}_original", "date_plus", order,
                            field_config=feld_config, gruppe=gruppe, feld=feldname_gross,
                            anzeige=f"{zusatz.capitalize()} (Original)", show=False, expert=True,
                            sortable=True, sort_direction="desc" if zusatz == "alter" else "asc",
                            sort_by_original=True, filter_type="number"
                        )
                        order += 1
                        
                        # Show-Zusatzspalte
                        show_zusatz = (zusatz == "alter" and ui_show_alter) or (zusatz in ["jahr", "monat", "tag"] and ui_show_YMD)
                        column_structure.add_column(
                            f"{feld_name}_{zusatz}_show", "date_plus", order,
                            field_config=feld_config, gruppe=gruppe, feld=feldname_gross,
                            anzeige=zusatz.capitalize(), show=show_zusatz, expert=False,
                            sortable=True, sort_direction="desc" if zusatz == "alter" else "asc",
                            sort_by_original=True, filter_type="number"
                        )
                        order += 1

            # Dummy-Spalte hinzufügen (wie im Original)
            column_structure.add_column(
                "dummy", "dummy", order,
                field_config={}, gruppe=None, feld=None,
                anzeige="", show=False, expert=True
            )

            # In einfache Spalten-Liste konvertieren für Widget-Kompatibilität
            columns = []
            for col_dict in column_structure.columns:
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
                
                # Mode-Filter: Im Normal-Mode keine Expert-Spalten
                if self.current_view_mode == "normal" and simple_col.get('display_expert'):
                    continue
                    
                columns.append(simple_col)

            logger.info(f"🔧 {len(columns)} Spalten mit _original/_show aus ViewDaten aufgebaut (Mode: {self.current_view_mode})")
            
            # Debug-Ausgabe der generierten Spalten
            for col in columns[:10]:  # Erste 10 zur Kontrolle
                logger.info(f"   📋 {col['name']} -> {col['label']} (show: {col['display_show']})")
            
            return columns
            
        except Exception as e:
            logger.error(f"❌ Fehler beim ViewDaten-Spalten-Aufbau: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _load_column_config_from_systemsteuerung(self, mode):
        """
        DIREKT: Lädt gespeicherte Spalten-Konfiguration aus Systemsteuerung
        """
        try:
            # 🎯 GLOBALE ZENTRALE SYSTEMSTEUERUNG verwenden
            try:
                import sys
                import os
                import importlib.util
                
                spec = importlib.util.spec_from_file_location("systemstart", "PDVM-Systemstart.py")
                systemstart_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(systemstart_module)
                
                sys_db = systemstart_module.get_global_central_systemsteuerung()
                logger.info("✅ Globale zentrale Systemsteuerung verwendet")
            except Exception as import_error:
                logger.warning(f"⚠️ Fallback: Eigene Systemsteuerung-Instanz - {import_error}")
                from pdvm_central_datenbank import PdvmCentralDatenbank
                
                sys_db = PdvmCentralDatenbank(
                    db_name="PdvmManager.db",
                    table_name="systemsteuerung",
                    guid=self.user_guid
                )
            
            # Gespeicherte Config laden
            config_data = sys_db.lesen_gruppe(self.view_guid)
            
            if config_data and f"columns_{mode}" in config_data:
                config = config_data[f"columns_{mode}"]
                logger.info(f"📋 Spalten-Config aus Systemsteuerung geladen für Mode '{mode}'")
                return config
            else:
                logger.info(f"📋 Keine gespeicherte Config für Mode '{mode}' - verwende Fallback")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Systemsteuerung-Config-Laden: {e}")
            return None
    
    # ========================================
    # EINFACHE API für Dialog (bleibt gleich)
    # ========================================
    
    def get_columns_for_mode(self, mode):
        """
        DIREKT: Lädt zunächst Systemsteuerung-Config, dann display_* Felder
        """
        try:
            # Erst gespeicherte Systemsteuerung-Config laden
            config = self._load_column_config_from_systemsteuerung(mode)
            
            if config:
                # Gespeicherte Config verwenden
                columns = []
                for col_config in config.get("columns", []):
                    column = {
                        'name': col_config.get('name'),
                        'display_show': col_config.get('show', True),
                        'display_order': col_config.get('order', 999),
                        'display_expert': col_config.get('expert', False)
                    }
                    
                    # Mode-Filter: Im Normal-Mode keine Expert-Spalten
                    if mode == "normal" and column['display_expert']:
                        continue
                        
                    columns.append(column)
                
                # Nach display_order sortieren
                columns.sort(key=lambda x: x.get('display_order', 999))
                
                logger.info(f"📋 {len(columns)} Spalten aus Systemsteuerung für Mode '{mode}' geladen")
                return columns
            
            # Fallback: Wenn keine Config vorhanden, dann auf basis_columns zurückfallen
            # Mode wechseln falls nötig
            if mode != self.current_view_mode:
                self.current_view_mode = mode
                self._load_data()  # Neu laden für anderen Mode
            
            logger.info(f"📋 {len(self.basis_columns)} Spalten für Mode '{mode}' (display_* schon da)")
            return self.basis_columns.copy()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei get_columns_for_mode: {e}")
            return []
    
    # ==========================================
    # NEU: Datenverarbeitung mit Column Control
    # ==========================================
    
    def refresh_with_central_stichtag(self):
        """
        ZENTRALE STICHTAG-ARCHITEKTUR: Refresh mit zentralem StichtagManager
        
        NEUE ARCHITEKTUR:
        - Kein Stichtag als Parameter mehr!
        - Stichtag wird zentral aus PdvmCentralStichtagManager abgerufen
        - Eliminiert Synchronisationsfehler zwischen Komponenten
        - Verwendet die erweiterte Column Control Integration
        - OHNE alle_lesen - nutzt bereits geladene Daten für effizienten Refresh
        
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
            central_manager = PdvmCentralStichtagManager()
            new_stichtag = central_manager.get_stichtag_float()
            
            logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - Effizienter Refresh mit zentralem Stichtag: {new_stichtag}")
            logger.info(f"📍 Alter ViewManager-Stichtag: {getattr(self, 'stichtag', 'N/A')}")
            
            if not self.column_control or not self.column_control.row_guids:
                logger.warning("⚠️ Keine Daten zum Refreshen vorhanden")
                return 0
                
            # BEREINIGT: Stichtag-Synchronisation entfernt - zentrale Property verwendet
            old_stichtag = getattr(self, 'stichtag', None)
            # BEREINIGT: Kein self.stichtag = - zentrale Property verwendet
            
            # BEREINIGT: call_daten Synchronisation entfernt - schädlich
            logger.info(f"🔄 Verwende zentralen Stichtag für Refresh: {new_stichtag}")
            
            # View-Tabelle ermitteln
            view_table = self._get_view_table()
            if not view_table:
                raise ValueError("View-Tabelle nicht ermittelbar")
            
            # Datetime-Formatter für Formatierung
            from pdvm_datetime import Pdvm_DateTime
            dt_formatter = Pdvm_DateTime("DEU")
            
            # Eine DB-Instanz für alle Datensätze wiederverwenden
            from pdvm_central_datenbank import PdvmCentralDatenbank
            working_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=view_table,
                guid=None
            )
            
            refreshed_records = 0
            total_records = len(self.column_control.row_guids)
            
            logger.info(f"📊 EFFIZIENTER REFRESH: {total_records} Datensätze mit zentralem Stichtag...")
            
            # Für jeden bereits geladenen Datensatz
            for i, data_guid in enumerate(self.column_control.row_guids):
                try:
                    # Bereits gespeicherte Rohdaten holen
                    existing_row = self.column_control.get_row_data(data_guid)
                    if not existing_row:
                        continue
                        
                    # EFFIZIENT: GUID direkt setzen (Daten sind bereits im ColumnControl)
                    working_db.guid = data_guid
                    
                    # Original-Spalten mit neuem zentralem Stichtag refreshen
                    self._refresh_original_columns_with_stichtag(existing_row, working_db, dt_formatter)
                    
                    # Show-Spalten mit neuen Original-Werten refreshen  
                    self._fill_all_show_columns_optimized(existing_row, dt_formatter)
                    
                    # Aktualisierte Daten zurück in ColumnControl speichern
                    self.column_control.set_row_data(data_guid, existing_row)
                    
                    refreshed_records += 1
                    
                    if (i + 1) % 20 == 0:
                        logger.info(f"   🔄 {i+1}/{total_records} Datensätze mit zentralem Stichtag refresht...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Refresh-Fehler bei Datensatz {data_guid}: {e}")
                    continue
            
            logger.info(f"✅ ZENTRALER STICHTAG-REFRESH abgeschlossen: {refreshed_records} Datensätze aktualisiert")
            logger.info(f"📅 Neuer zentraler Stichtag: {new_stichtag} (vorher: {old_stichtag})")
            
            # DEAKTIVIERT: Sortierung erneut anwenden (mit neuen Werten)
            # if self.column_control.sort_stack:
            #     self.column_control.apply_multi_level_sort()
            #     logger.info("✅ Sortierung mit neuen Werten angewendet")
                
            return refreshed_records
            
        except Exception as e:
            logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Bei Fehler: Stichtag zurücksetzen falls möglich
            if 'old_stichtag' in locals() and old_stichtag is not None:
                logger.warning(f"🔄 Setze Stichtag zurück: {new_stichtag} → {old_stichtag}")
                # BEREINIGT: Stichtag wird zentral über StichtagManager verwaltet
                # (Kein Rollback mehr möglich bei zentraler Architektur)
                pass
            
            return 0
    
    def refresh_with_stichtag(self, new_stichtag):
        """
        KOMPATIBILITÄTS-METHODE: Ruft zentrale refresh_with_central_stichtag() auf
        
        WICHTIGER HINWEIS:
        Diese Methode ist nur noch für Kompatibilität da!
        Neue Architektur: Verwende refresh_with_central_stichtag() ohne Parameter!
        
        Args:
            new_stichtag (float): Wird ignoriert - zentraler Stichtag wird verwendet
            
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        logger.warning("⚠️ refresh_with_stichtag() ist deprecated! Verwende refresh_with_central_stichtag() mit zentralem Stichtag")
        logger.info(f"📍 Übergebener Stichtag {new_stichtag} wird ignoriert - verwende zentralen Stichtag")
        
        # Zentrale Refresh-Methode aufrufen
        return self.refresh_with_central_stichtag()

    # ============================================
    # DATENVERARBEITUNG MIT COLUMN CONTROL
    # ============================================
    
    def load_records_data(self, limit=100):
        """
        OPTIMIERT: Lädt Datensätze nur bei first_call=True
        Bei first_call=False wird übersprungen (für effizienten Stichtag-Refresh)
        """
        try:
            logger.info(f"🔧 SCHRITT 4: Load Records Data (first_call={self.first_call}, limit={limit})")
            
            # EINFACHE LOGIK: Bei Refresh (first_call=False) überspringen
            if not self.first_call:
                logger.info("📊 SKIP: Datensätze-Laden übersprungen (first_call=False)")
                return 0
                
            logger.info("� VOLLSTÄNDIGES LADEN: Datensätze aus DB (first_call=True)")
            
            # 1. Datentabelle ermitteln
            view_table = self._get_view_table()
            if not view_table:
                raise ValueError("View-Tabelle nicht ermittelbar")
            
            # 2. OPTIMIERT: Alle Datensätze in einem Zug laden (ohne SYSTEM_ID)
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db", 
                table_name=view_table,
                guid=None  # Keine spezifische GUID
            )
            
            # Neue optimierte Methode verwenden
            all_records = data_db.lesen_alle_ohne_system(limit=limit)
            logger.info(f"📊 {len(all_records)} Datensätze in einem Zug geladen")
            
            # 3. Datetime-Formatter einmalig erstellen
            from pdvm_datetime import Pdvm_DateTime
            dt_formatter = Pdvm_DateTime("DEU")
            
            # 4. OPTIMIERT: Eine PdvmCentralDatenbank-Instanz wiederverwenden
            working_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=view_table,
                guid=None  # Wird für jeden Datensatz via set_data() gesetzt
            )
            
            # 5. Für jeden Datensatz alle Spalten befüllen
            successful_records = 0
            for i, record_info in enumerate(all_records):
                try:
                    data_guid = record_info["uid"]
                    data_dict = record_info["daten_dict"]
                    
                    # OPTIMIERT: Daten direkt setzen statt neuen DB-Zugriff
                    working_db.set_data(data_dict, data_guid)
                    
                    # Row-Record für alle Spalten erstellen
                    row_record = {'uid_original': data_guid}
                    
                    # Original-Spalten befüllen (mit unserer korrigierten linearen Methode)
                    self._fill_all_original_columns(row_record, data_dict, dt_formatter, self.stichtag)
                    
                    # Show-Spalten befüllen (mit unserer korrigierten Methode)
                    self._fill_all_show_columns(row_record, dt_formatter)
                    
                    # In Column Control speichern
                    self.column_control.set_row_data(data_guid, row_record)
                    
                    successful_records += 1
                    
                    if (i + 1) % 20 == 0:
                        logger.info(f"   📊 {i+1}/{len(all_records)} Datensätze verarbeitet...")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Fehler bei Datensatz {record_info.get('uid', 'unbekannt')}: {e}")
                    continue
            
            logger.info(f"✅ {successful_records} Datensätze in Column Control geladen (OPTIMIERT)")
            
            # 6. Standardsortierung anwenden (falls noch keine definiert)
            if not self.column_control.sort_stack:
                # Standard: Nach erstem _show Feld sortieren
                show_columns = [col['name'] for col in self.column_control.columns 
                              if col['name'].endswith('_show') and col['name'] != 'uid_show']
                # DEAKTIVIERT: Standard-Sortierung
                # if show_columns:
                #     self.column_control.add_sort_level(show_columns[0], 'asc')
                #     self.column_control.apply_multi_level_sort()
            
            return successful_records
            
        except Exception as e:
            logger.error(f"❌ Fehler beim optimierten Laden der Datensätze: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _get_view_table(self):
        """Ermittelt die View-Tabelle aus ViewDaten"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            view_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=self.view_guid
            )
            return view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
        except Exception as e:
            logger.error(f"❌ Fehler beim Ermitteln der View-Tabelle: {e}")
            return None
    
    def _fill_all_original_columns_for_guid(self, row_record: dict, data_dict: dict, data_guid: str):
        """Befüllt alle _original Spalten für einen Datensatz"""
        try:
            # Datetime-Formatter für Datumsverarbeitung
            from pdvm_datetime import Pdvm_DateTime
            dt_formatter = Pdvm_DateTime("DEU")
            
            for col in self.column_control.columns:
                col_name = col['name']
                
                # Nur _original Spalten verarbeiten (außer uid_original)
                if not col_name.endswith("_original") or col_name == "uid_original":
                    continue
                
                col_type = col.get('type', '')
                field_config = col.get('field_config', {})
                
                if col_type == "field_original":
                    # Haupt-Original-Spalte
                    feld = col.get('feld')
                    gruppe = col.get('gruppe', 'DATEN')
                    
                    if feld and gruppe in data_dict and feld in data_dict[gruppe]:
                        wert = data_dict[gruppe][feld]
                        row_record[col_name] = wert
                        
                        # Falls Datumsfeld: Zusatzspalten direkt befüllen
                        if field_config.get('type') == 'date' and isinstance(wert, (int, float)) and wert > 0:
                            self._fill_date_additional_original_for_guid(row_record, feld, wert, dt_formatter)
                    else:
                        row_record[col_name] = ""
                
                elif col_type == "date_plus":
                    # Zusatzspalten für Datum werden von _fill_date_additional_original_for_guid befüllt
                    # Falls nicht befüllt, leer lassen
                    if col_name not in row_record:
                        row_record[col_name] = ""
                        
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Original-Spalten für {data_guid}: {e}")
    
    def _fill_all_original_columns_optimized(self, row_record: dict, working_db: 'PdvmCentralDatenbank', dt_formatter):
        """
        OPTIMIERT: Befüllt alle _original Spalten mit bereits gesetzter DB-Instanz
        """
        try:
            for col in self.column_control.columns:
                col_name = col['name']
                
                # Nur _original Spalten verarbeiten (außer uid_original)
                if not col_name.endswith("_original") or col_name == "uid_original":
                    continue
                
                col_type = col.get('type', '')
                field_config = col.get('field_config', {})
                
                if col_type == "field_original":
                    # Haupt-Original-Spalte
                    feld = col.get('feld')
                    gruppe = col.get('gruppe', 'DATEN')
                    
                    # OPTIMIERT: get_value auf bereits geladene DB-Instanz mit Stichtag
                    value_result = working_db.get_value(gruppe, feld, ab_zeit=self.stichtag)
                    if value_result and 'wert' in value_result:
                        wert = value_result['wert']
                        row_record[col_name] = wert
                        
                        # Falls Datumsfeld: Zusatzspalten direkt befüllen
                        if field_config.get('type') == 'date' and isinstance(wert, (int, float)) and wert > 0:
                            self._fill_date_additional_original_optimized(row_record, feld, wert, dt_formatter)
                    else:
                        row_record[col_name] = ""
                
                elif col_type == "date_plus":
                    # Zusatzspalten für Datum werden von _fill_date_additional_original_optimized befüllt
                    # Falls nicht befüllt, leer lassen
                    if col_name not in row_record:
                        row_record[col_name] = ""
                        
        except Exception as e:
            logger.error(f"❌ Fehler beim optimierten Befüllen der Original-Spalten für {working_db.guid}: {e}")
    
    def _fill_all_show_columns_optimized(self, row_record: dict, dt_formatter):
        """
        OPTIMIERT: Befüllt alle _show Spalten basierend auf _original Werten
        """
        try:
            # System-Show-Spalte
            if "uid_original" in row_record:
                data_guid = row_record["uid_original"]
                row_record["uid_show"] = data_guid[:8] + "..." if data_guid else ""
            
            for col in self.column_control.columns:
                col_name = col['name']
                col_type = col.get('type', '')
                
                # Nur _show Spalten verarbeiten (außer uid_show)
                if not col_name.endswith("_show") or col_name == "uid_show":
                    continue
                
                if col_type == "field_show":
                    # Haupt-Show-Spalte
                    original_col_name = col_name.replace("_show", "_original")
                    original_wert = row_record.get(original_col_name)
                    field_config = col.get('field_config', {})
                    self._format_show_value(row_record, col_name, original_wert, field_config, dt_formatter)
                    
                elif col_type == "date_additional_show":
                    # Zusatz-Show-Spalten für Datum (3.1 Zusatzspalten über Pdvm_DateTime)
                    original_col_name = col_name.replace("_show", "_original")
                    original_wert = row_record.get(original_col_name)
                    self._fill_date_additional_show_column(row_record, col_name, original_wert)
                    
                elif col_type == "dummy" and col_name == "dummy":
                    # 4. DUMMY: fix für jeden Satz 'keine Daten'
                    row_record[col_name] = "keine Daten"
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim optimierten Befüllen der Show-Spalten: {e}")
    
    def _fill_date_additional_original_optimized(self, row_record: dict, feld_name: str, original_wert: Any, dt_formatter):
        """OPTIMIERT: Befüllt Zusatzspalten für Datumsfelder"""
        try:
            if not isinstance(original_wert, (int, float)) or original_wert <= 0:
                return
            
            # Datum setzen
            dt_formatter.PdvmDateTime = original_wert
            
            # Stichtag für Alter-Berechnung
            try:
                from pdvm_datetime import Pdvm_DateTime
                dt_stichtag = Pdvm_DateTime("DEU")
                dt_stichtag.PdvmDateTime = self.stichtag
                alter = dt_stichtag.Year - dt_formatter.Year
            except:
                import datetime
                alter = datetime.datetime.now().year - dt_formatter.Year
            
            # Werte berechnen
            zusatz_werte = {
                "alter": alter,
                "jahr": dt_formatter.Year,
                "monat": dt_formatter.Month,
                "tag": dt_formatter.Day
            }
            
            # Original-Zusatzspalten befüllen
            for zusatz, wert in zusatz_werte.items():
                key = f"{feld_name.lower()}_{zusatz}_original"
                # Prüfen ob diese Spalte im Column Control existiert
                if key in [col['name'] for col in self.column_control.columns]:
                    row_record[key] = wert
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim optimierten Befüllen der Datums-Zusatzspalten für {feld_name}: {e}")
    
    def _fill_date_additional_original_for_guid(self, row_record: dict, feld_name: str, original_wert: Any, dt_formatter):
        """Befüllt Zusatzspalten für Datumsfelder"""
        try:
            if not isinstance(original_wert, (int, float)) or original_wert <= 0:
                return
            
            # Datum setzen
            dt_formatter.PdvmDateTime = original_wert
            
            # Stichtag für Alter-Berechnung
            try:
                from pdvm_datetime import Pdvm_DateTime
                dt_stichtag = Pdvm_DateTime("DEU")
                dt_stichtag.PdvmDateTime = self.stichtag
                alter = dt_stichtag.Year - dt_formatter.Year
            except:
                import datetime
                alter = datetime.datetime.now().year - dt_formatter.Year
            
            # Werte berechnen
            zusatz_werte = {
                "alter": alter,
                "jahr": dt_formatter.Year,
                "monat": dt_formatter.Month,
                "tag": dt_formatter.Day
            }
            
            # Original-Zusatzspalten befüllen
            for zusatz, wert in zusatz_werte.items():
                key = f"{feld_name.lower()}_{zusatz}_original"
                # Prüfen ob diese Spalte im Column Control existiert
                if key in [col['name'] for col in self.column_control.columns]:
                    row_record[key] = wert
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Datums-Zusatzspalten für {feld_name}: {e}")
    
    def _fill_all_show_columns_for_guid(self, row_record: dict, data_guid: str):
        """Befüllt alle _show Spalten für einen Datensatz"""
        try:
            # Datetime-Formatter für Datumsverarbeitung
            from pdvm_datetime import Pdvm_DateTime
            dt_formatter = Pdvm_DateTime("DEU")
            
            # System-Show-Spalte
            row_record["uid_show"] = data_guid[:8] + "..." if data_guid else ""
            
            for col in self.column_control.columns:
                col_name = col['name']
                col_type = col.get('type', '')
                
                # Nur _show Spalten verarbeiten (außer uid_show)
                if not col_name.endswith("_show") or col_name == "uid_show":
                    continue
                
                if col_type == "field_show":
                    # Haupt-Show-Spalte
                    original_col_name = col_name.replace("_show", "_original")
                    original_wert = row_record.get(original_col_name)
                    field_config = col.get('field_config', {})
                    self._format_show_value(row_record, col_name, original_wert, field_config, dt_formatter)
                    
                elif col_type == "date_additional_show":
                    # Zusatz-Show-Spalten für Datum (3.1 Zusatzspalten über Pdvm_DateTime)
                    original_col_name = col_name.replace("_show", "_original")
                    original_wert = row_record.get(original_col_name)
                    self._fill_date_additional_show_column(row_record, col_name, original_wert)
                    
                elif col_type == "dummy" and col_name == "dummy":
                    # 4. DUMMY: fix für jeden Satz 'keine Daten'
                    row_record[col_name] = "keine Daten"
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Show-Spalten für {data_guid}: {e}")
    
    def _format_show_value(self, row_record: dict, col_name: str, original_wert: Any, field_config: dict, dt_formatter):
        """
        Formatiert einen Original-Wert für die Show-Spalte
        
        Unterstützte Typen:
        1. type=string show=original
        2. type=dropdown show=übersetzen mit PdvmDropDownManager  
        3. type=date show=Pdvm_DateTime.Date
        3.1 Zusatzspalten über Pdvm_DateTime setzen
        """
        try:
            field_type = field_config.get("type", "string")
            
            if field_type == "string":
                # 1. STRING: show=original
                row_record[col_name] = str(original_wert) if original_wert is not None else ""
                
            elif field_type == "dropdown":
                # 2. DROPDOWN: show=übersetzen mit PdvmDropDownManager
                row_record[col_name] = self._translate_dropdown_value_with_manager(original_wert, field_config)
                
            elif field_type == "date":
                # 3. DATE: show=Pdvm_DateTime.Date
                if isinstance(original_wert, (int, float)) and original_wert > 0:
                    dt_formatter.PdvmDateTime = original_wert
                    row_record[col_name] = dt_formatter.Date
                else:
                    row_record[col_name] = ""
            else:
                # Fallback: Als String behandeln
                row_record[col_name] = str(original_wert) if original_wert is not None else ""
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Formatieren der Show-Spalte {col_name}: {e}")
            row_record[col_name] = str(original_wert) if original_wert is not None else ""
    
    def _translate_dropdown_value_with_manager(self, wert: Any, field_config: dict) -> str:
        """
        Übersetzt Dropdown-Werte mit dem PdvmDropDownManager
        """
        try:
            if not wert:
                return ""
            
            # PdvmDropDownManager für die Übersetzung verwenden
            dropdown_config = field_config.get("dropdown", {})
            dropdown_guid = dropdown_config.get("guid")
            dropdown_gruppe = dropdown_config.get("gruppe")
            
            if dropdown_guid and dropdown_gruppe:
                # Importiere PdvmDropDownManager
                try:
                    from pdvm_dropdown_manager import PdvmDropDownManager
                    
                    # DropDown-Manager erstellen
                    dropdown_manager = PdvmDropDownManager(dropdown_guid, dropdown_gruppe)
                    
                    # Wert übersetzen
                    translated = dropdown_manager.get_display_value(str(wert))
                    return translated if translated else str(wert)
                    
                except ImportError:
                    logger.warning(f"⚠️ PdvmDropDownManager nicht verfügbar - verwende Fallback-Übersetzung")
                    return self._translate_dropdown_value_fallback(wert)
                except Exception as e:
                    logger.error(f"❌ Fehler beim DropDown-Manager: {e}")
                    return self._translate_dropdown_value_fallback(wert)
            else:
                # Keine DropDown-Config vorhanden - verwende Fallback
                return self._translate_dropdown_value_fallback(wert)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei DropDown-Übersetzung: {e}")
            return str(wert) if wert else ""
    
    def _translate_dropdown_value_fallback(self, wert: Any) -> str:
        """
        Fallback-Übersetzung für DropDown-Werte (für Demo/Test)
        """
        try:
            wert_str = str(wert)
            
            # Einfache Übersetzungen für häufige Werte
            fallback_translations = {
                "1": "Frau",
                "2": "Herr", 
                "3": "Divers",
                "m": "Männlich",
                "w": "Weiblich",
                "d": "Divers",
                "ja": "Ja",
                "nein": "Nein",
                "true": "Ja",
                "false": "Nein"
            }
            
            return fallback_translations.get(wert_str.lower(), wert_str)
            
        except:
            return str(wert) if wert else ""
    
    def get_table_data_for_display(self, show_only=True, apply_sorting=True):
        """
        NEU: Holt die Tabellendaten aus dem Column Control System
        """
        try:
            # DEAKTIVIERT: Sortierung anwenden wenn gewünscht
            # if apply_sorting:
            #     self.column_control.apply_multi_level_sort()
            
            # Daten für Anzeige holen
            display_data, display_columns = self.column_control.get_display_table_data(show_columns_only=show_only)
            
            # Im ExpertMode: Spezielle Header mit zweizeiliger Darstellung
            if self.current_view_mode == "expert":
                display_headers = self.column_control.get_expert_mode_headers(display_columns)
                logger.info(f"🔧 ExpertMode: {len(display_headers)} zweizeilige Header erstellt")
            else:
                # Normal-Mode: Standard-Header
                display_headers = display_columns
            
            logger.info(f"📋 {len(display_data)} Zeilen mit {len(display_columns)} Spalten für Anzeige bereit (Mode: {self.current_view_mode})")
            
            return display_data, display_headers
            
            return display_data, display_headers
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen der Tabellendaten: {e}")
            return [], []
    
    def get_filtered_data(self):
        """
        KOMPATIBILITÄTS-METHODE: Für ViewWidget Integration
        
        Verwendet die Column Control Architektur für gefilterte Tabellenausgabe.
        Diese Methode wird vom PdvmViewWidget erwartet.
        
        Returns:
            tuple: (data, headers) für Tabellendarstellung
        """
        try:
            logger.info("📊 get_filtered_data() für ViewWidget Integration")
            
            # Im ExpertMode alle Spalten zeigen, nicht nur show_only
            show_only = (self.current_view_mode != "expert")
            logger.info(f"🔧 ExpertMode aktiv: {self.current_view_mode == 'expert'} -> show_only: {show_only}")
            
            # Nutzt die erweiterte Column Control Implementierung
            data, headers = self.get_table_data_for_display(show_only=show_only, apply_sorting=False)
            
            if not data:
                logger.warning("⚠️ get_filtered_data: Keine Daten verfügbar - erzeuge Fallback")
                return [], []
                
            logger.info(f"✅ get_filtered_data: {len(data)} Zeilen mit {len(headers)} Spalten für ViewWidget bereit")
            return data, headers
            
        except Exception as e:
            logger.error(f"❌ get_filtered_data Fehler: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Fallback: Leere Tabelle mit Fehlermeldung
            return [["Fehler beim Laden der Daten"]], ["Hinweis"]
    
    def set_multi_level_sorting(self, sort_levels: list):
        """
        NEU: Setzt Mehrebenen-Sortierung
        sort_levels = [('anrede_show', 'asc'), ('familienname_show', 'asc'), ...]
        """
        try:
            self.column_control.clear_all_sorting()
            for column_name, direction in sort_levels:
                self.column_control.add_sort_level(column_name, direction)
            
            logger.info(f"🔧 Mehrebenen-Sortierung konfiguriert: {len(sort_levels)} Ebenen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen der Sortierung: {e}")
            return False
    
    def set_columns_for_mode(self, mode, columns):
        """
        DIREKT: Speichert Spalten-Konfiguration für einen Mode
        """
        try:
            # Direkt in Systemsteuerung speichern (verwende gleiche Methode wie Dialog)
            success = self._save_to_systemsteuerung_direct(columns, mode)
            
            if success:
                # Nach dem Speichern neue Daten laden um aktuell zu sein
                self._load_data()
                logger.info(f"✅ {len(columns)} Spalten für Mode '{mode}' gespeichert und neu geladen")
                return True
            else:
                logger.error(f"❌ Speichern fehlgeschlagen für Mode '{mode}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Spalten-Speichern für Mode '{mode}': {e}")
            return False
    
    def save_columns_from_dialog(self, columns, mode):
        """
        DIREKT: Spalten direkt in Systemsteuerung speichern - OHNE PROVIDER
        """
        try:
            logger.info(f"💾 Speichere {len(columns)} Spalten DIREKT - OHNE PROVIDER")
            
            # DIREKT in systemsteuerung speichern
            success = self._save_to_systemsteuerung_direct(columns, mode)
            
            if success:
                # Daten neu laden (damit display_* neu aufgebaut wird)
                self._load_data()
                
                # Widget-Tabelle neu aufbauen
                if self.widget and hasattr(self.widget, 'load_data'):
                    logger.info("🔄 Aktualisiere Widget-Tabelle...")
                    self.widget.load_data()
                
                logger.info("✅ DIREKT gespeichert und Tabelle neu aufgebaut")
                return True
            else:
                logger.error("❌ Direktes Speichern fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim direkten Speichern: {e}")
            return False
    
    def refresh_stichtag_only(self, new_stichtag):
        """
        EFFIZIENTE STICHTAG-AKTUALISIERUNG ohne DB-Neuladen
        Aktualisiert nur berechnete Felder mit neuem Stichtag
        """
        try:
            logger.info(f"🔄 EFFIZIENTER STICHTAG-REFRESH: {self.stichtag} -> {new_stichtag}")
            old_stichtag = self.stichtag
            # BEREINIGT: Stichtag wird zentral über StichtagManager verwaltet
            
            # Nur berechnete Felder aktualisieren
            if self.column_control and hasattr(self.column_control, 'row_guids'):
                refreshed_count = 0
                
                for row_guid in self.column_control.row_guids:
                    # Für jede Zeile die berechneten _show Werte neu berechnen
                    for col in self.column_control.columns:
                        if col['name'].endswith('_show'):
                            # Original-Feld finden
                            original_field = col['name'].replace('_show', '_original')
                            original_value = self.column_control.get_column_data(original_field, row_guid)
                            
                            # _show Wert neu berechnen mit neuem Stichtag
                            if col['type'] == 'date' and original_value:
                                try:
                                    from pdvm_datetime import Pdvm_DateTime
                                    pd_dt = Pdvm_DateTime(original_value)
                                    show_value = pd_dt.format_for_stichtag(new_stichtag)
                                    self.column_control.set_column_data(col['name'], row_guid, show_value)
                                except Exception as e:
                                    logger.debug(f"Datumskonvertierung fehlgeschlagen für {original_value}: {e}")
                            
                    refreshed_count += 1
                
                logger.info(f"✅ EFFIZIENTER REFRESH: {refreshed_count} Zeilen aktualisiert (ohne DB-Zugriff)")
                return refreshed_count
            else:
                logger.warning("⚠️ Keine Column Control verfügbar für Refresh")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Effizienter Stichtag-Refresh fehlgeschlagen: {e}")
            return 0
    
    def update_call_data_and_refresh(self, new_call_data):
        """
        Aktualisiert call_daten und führt entsprechenden Refresh durch
        """
        try:
            old_first_call = self.first_call
            old_stichtag = self.stichtag
            
            # Call-Daten aktualisieren
            self.call_daten.update(new_call_data)
            self.first_call = new_call_data.get("first_call", True)
            # BEREINIGT: Stichtag wird zentral über StichtagManager verwaltet
            
            logger.info(f"🔧 Call-Data Update: first_call {old_first_call}->{self.first_call}, stichtag {old_stichtag}->{self.stichtag}")
            
            if self.first_call:
                # Vollständiger Reload
                logger.info("📊 VOLLSTÄNDIGER RELOAD")
                self._load_data()
                return "full_reload"
            else:
                # Nur Stichtag-Refresh
                logger.info("🔄 NUR STICHTAG-REFRESH")
                refreshed = self.refresh_stichtag_only(self.stichtag)
                return f"stichtag_refresh_{refreshed}"
                
        except Exception as e:
            logger.error(f"❌ Call-Data Update fehlgeschlagen: {e}")
            return "error"
    
    def _save_to_systemsteuerung_direct(self, columns, mode):
        """DIREKT in Systemsteuerung speichern - OHNE PROVIDER-UMWEGE"""
        try:
            # 🎯 GLOBALE ZENTRALE SYSTEMSTEUERUNG verwenden
            try:
                import sys
                import os
                import importlib.util
                
                spec = importlib.util.spec_from_file_location("systemstart", "PDVM-Systemstart.py")
                systemstart_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(systemstart_module)
                
                sys_db = systemstart_module.get_global_central_systemsteuerung()
                logger.info("✅ Speichern über globale zentrale Systemsteuerung")
            except Exception as import_error:
                logger.warning(f"⚠️ Fallback: Eigene Systemsteuerung-Instanz für Speichern - {import_error}")
                from pdvm_central_datenbank import PdvmCentralDatenbank
                
                # Systemsteuerung für User
                sys_db = PdvmCentralDatenbank(
                    db_name="PdvmManager.db",
                    table_name="systemsteuerung",
                    guid=self.user_guid
                )
            
            # Spalten-Konfiguration vorbereiten
            config = {
                "mode": mode,
                "columns": []
            }
            
            for col in columns:
                config["columns"].append({
                    "name": col.get("name"),
                    "show": col.get("display_show", True),
                    "order": col.get("display_order", 999),
                    "expert": col.get("display_expert", False)
                })
            
            # DIREKT speichern unter view_guid Gruppe
            sys_db.set_value(
                gruppe=self.view_guid,
                feld=f"columns_{mode}",
                wert=config
            )
            
            # WICHTIG: Daten auch in DB-Datei schreiben!
            sys_db.save_values()
            
            logger.info(f"💾 DIREKT in Systemsteuerung gespeichert UND PERSISTIERT")
            return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim direkten Systemsteuerung-Speichern: {e}")
            return False
    
    # ========================================
    # EINFACHE Tabellen-API (bleibt gleich)
    # ========================================
    
    def get_table_data(self):
        """DIREKT: Tabellendaten zurückgeben - Widget-kompatibel"""
        # Nur anzuzeigende Spalten filtern
        display_columns = [col for col in self.basis_columns if col.get('display_show', True)]
        
        # Nach display_order sortieren
        display_columns.sort(key=lambda x: x.get('display_order', 999))
        
        # Spalten-Namen extrahieren (für Widget-Kompatibilität)
        column_names = [col.get('name', 'Unknown') for col in display_columns]
        
        return self.basis_data, column_names
    
    def switch_view_mode(self, new_mode):
        """DIREKT: Mode wechseln"""
        if new_mode != self.current_view_mode:
            self.current_view_mode = new_mode
            self._load_data()
            return True
        return False
    
    def is_expert_mode(self):
        """Kompatibilität"""
        return self.current_view_mode == "expert"
        
    def _create_column_control(self, felder: list) -> ColumnControl:
        """
        Erstellt die Control-Struktur mit einheitlicher Namensgebung und Kopfzeilen-Logik.
        - Feldname (klein) für _original/_show
        - 'name' als Anzeigeüberschrift (show), bei original: '(Original)' anhängen
        - Zusatzfelder: 'Alter', 'Jahr', 'Monat', 'Tag'
        - Im Expert-Mode: 2 Kopfzeilen (Zeile 1: name, Zeile 2: feldname)
        """
        control = ColumnControl()
        order = 0

        # System-Spalten zuerst
        control.add_column(
            "uid_original", "system", order,
            field_config={"anzeige": "ID (Original)", "label": "uid_original"},
            gruppe=None, feld=None, anzeige="ID (Original)",
            show=False, expert=True
        )
        order += 1
        control.add_column(
            "uid_show", "system", order,
            field_config={"anzeige": "ID", "label": "uid_show"},
            gruppe=None, feld=None, anzeige="ID",
            show=True, expert=False
        )
        order += 1

        for feld_config in felder:
            feldname_gross = feld_config["feld"]
            feld_name = feldname_gross.lower()
            feld_type = feld_config.get("type", "string")
            gruppe = feld_config.get("gruppe", "DATEN")
            anzeige = feld_config.get("name") or feld_name.capitalize()
            
            # UI-Parameter aus feld_config extrahieren
            ui_params = feld_config.get("ui", {})
            ui_sortable = ui_params.get("sortable", True)
            ui_sort_direction = ui_params.get("sortDirection", "asc")
            ui_sort_by_original = ui_params.get("sortByOriginal", False)
            ui_filter_type = ui_params.get("filterType", "contains")
            ui_width = ui_params.get("width", "auto")
            ui_searchable = ui_params.get("searchable", True)

            # Original-Spalte (Expert-Mode: label = feld_name (klein))
            orig_label = feld_name  # <--- Feldname klein für die zweite Zeile im Header
            orig_anzeige = f"{anzeige} (Original)"
            orig_field_config = dict(feld_config)
            orig_field_config["anzeige"] = orig_anzeige
            orig_field_config["label"] = orig_label
            control.add_column(
                f"{feld_name}_original",
                "original",
                order,
                original_field=feld_name,
                field_config=orig_field_config,
                gruppe=gruppe,
                feld=feld_name,
                anzeige=orig_anzeige,
                show=False,
                expert=True,
                # UI-Parameter hinzufügen
                sortable=ui_sortable,
                sortDirection=ui_sort_direction,
                sortByOriginal=True,  # Original-Spalten sortieren immer nach Original
                filterType=ui_filter_type,
                width=ui_width,
                searchable=ui_searchable
            )
            order += 1

            # Zusatzfelder für Datum
            if feld_type == "date":
                for zusatz, zusatz_label in zip(
                    ["alter", "jahr", "monat", "tag"],
                    ["Alter", "Jahr", "Monat", "Tag"]):
                    col_name = f"{feld_name}_{zusatz}_original"
                    auto_field_config = dict(feld_config)
                    auto_field_config["anzeige"] = f"{anzeige} {zusatz_label} (Original)"
                    auto_field_config["label"] = f"{feldname_gross}_{zusatz}"
                    control.add_column(
                        col_name,
                        "date_plus",
                        order,
                        original_field=feld_name,
                        field_config=auto_field_config,
                        is_auto_generated=True,
                        gruppe=gruppe,
                        feld=feld_name,
                        anzeige=auto_field_config["anzeige"],
                        show=False,
                        expert=True,
                        # UI-Parameter für Datums-Zusatzfelder
                        sortable=ui_sortable,
                        sortDirection=ui_sort_direction,
                        sortByOriginal=True,
                        filterType=ui_filter_type,
                        width=ui_width,
                        searchable=ui_searchable
                    )
                    order += 1

            # Show-Spalte (label = feldname_gross)
            show_field_config = dict(feld_config)
            show_field_config["anzeige"] = anzeige
            show_field_config["label"] = feldname_gross
            control.add_column(
                f"{feld_name}_show",
                "show",
                order,
                original_field=feld_name,
                field_config=show_field_config,
                gruppe=gruppe,
                feld=feld_name,
                anzeige=anzeige,
                show=True,
                expert=False,
                # UI-Parameter für Show-Spalten
                sortable=ui_sortable,
                sortDirection=ui_sort_direction,
                sortByOriginal=ui_sort_by_original,  # Wie in ViewDaten definiert
                filterType=ui_filter_type,
                width=ui_width,
                searchable=ui_searchable
            )
            order += 1

            # Zusatzfelder für Datum (show)
            if feld_type == "date":
                for zusatz, zusatz_label in zip(
                    ["alter", "jahr", "monat", "tag"],
                    ["Alter", "Jahr", "Monat", "Tag"]):
                    col_name = f"{feld_name}_{zusatz}_show"
                    auto_field_config = dict(feld_config)
                    auto_field_config["anzeige"] = f"{anzeige} {zusatz_label}"
                    auto_field_config["label"] = f"{feldname_gross}_{zusatz}"
                    control.add_column(
                        col_name,
                        "date_plus",
                        order,
                        original_field=feld_name,
                        field_config=auto_field_config,
                        is_auto_generated=True,
                        gruppe=gruppe,
                        feld=feld_name,
                        anzeige=auto_field_config["anzeige"],
                        show=True,
                        expert=False,
                        # UI-Parameter für Show-Datums-Zusatzfelder
                        sortable=ui_sortable,
                        sortDirection=ui_sort_direction,
                        sortByOriginal=ui_sort_by_original,
                        filterType=ui_filter_type,
                        width=ui_width,
                        searchable=ui_searchable
                    )
                    order += 1

        # Dummy-Spalte immer am Ende hinzufügen
        control.add_column(
            "dummy", "dummy", order,
            field_config={"anzeige": "Keine Daten", "label": "dummy"},
            gruppe=None, feld=None, anzeige="Keine Daten",
            show=False, expert=False
        )
        order += 1

        # Control sortieren
        control.sort_columns()

        logger.info(f"🏗️ Control-Struktur erstellt: {len(control.columns)} Spalten (inkl. Dummy)")
        logger.info("📋 Reihenfolge: System → Original → Auto-Original → Show → Auto-Show → Dummy")
        logger.info(f"📋 Spaltennamen: {[col['name'] for col in control.columns]}")
        return control
    
    def get_default_column_visibility(self, view_config: dict) -> dict:
        """
        Erstellt eine Standard-Spalten-Sichtbarkeits-Konfiguration.
        
        Standard-Verhalten:
        - Haupt-Felder: sichtbar (show=true)
        - Original-Spalten: unsichtbar (show=false)  
        - Show-Spalten: unsichtbar (show=false)
        - YMD/Alter-Spalten: unsichtbar (show=false)
        
        Args:
            view_config: View-Konfiguration
            
        Returns:
            dict: Standard-Spalten-Sichtbarkeits-Konfiguration
        """
        try:
            column_visibility = {}
            
            # Flexible Behandlung verschiedener view_config Strukturen
            if "ROOT" in view_config and "metadata" in view_config:
                # Vollständige view_config Struktur
                table_name = view_config["ROOT"]["view_table"]
                felder = view_config["metadata"][table_name]["felder"]
            elif "fields" in view_config:
                # Einfache fields-basierte Struktur
                felder = [{"feld": field, "type": "string"} for field in view_config["fields"]]
            else:
                logger.error("❌ Fehler beim Erstellen der Standard-Spalten-Sichtbarkeit: Unbekannte view_config Struktur")
                return {}
            
            for feld_config in felder:
                if isinstance(feld_config, str):
                    feld_name = feld_config
                    feld_type = "string"
                else:
                    feld_name = feld_config["feld"]
                    feld_type = feld_config.get("type", "string")
                
                # Standard: Haupt-Feld sichtbar
                column_visibility[feld_name] = True
                
                # Original/Show-Spalten: Standard unsichtbar (für Debugging/Entwicklung verfügbar)
                column_visibility[f"{feld_name}_original"] = False
                column_visibility[f"{feld_name}_show"] = False
                
                # Datums-Spalten: Standard unsichtbar
                if feld_type == "date":
                    column_visibility[f"{feld_name}_jahr"] = False
                    column_visibility[f"{feld_name}_monat"] = False
                    column_visibility[f"{feld_name}_tag"] = False
                    column_visibility[f"{feld_name}_alter"] = False
            
            logger.info(f"📊 Standard-Spalten-Sichtbarkeit erstellt: {len(column_visibility)} Spalten-Regeln")
            return column_visibility
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Standard-Spalten-Sichtbarkeit: {e}")
            return {}
