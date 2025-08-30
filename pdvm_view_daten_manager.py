
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
        self.first_call = call_daten.get("first_call", True)

        # Lese 'mode' aus zentraler Systemsteuerung
        try:
            import pdvm_central_systemsteuerung_global
            self.gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung
            mode_data = self.gcs.get_value(gruppe=self.gcs.user_guid, feld="mode", ab_zeit=None)
            self.mode = mode_data.get("wert", "user") if mode_data else "user"
            logger.info(f"✅ Mode aus zentraler Systemsteuerung geladen: {self.mode}")
        except Exception as e:
            logger.warning(f"⚠️ Mode aus Systemsteuerung nicht verfügbar: {e}")
            self.mode = "user"

        # Column Control System
        self.column_control = None
        self.basis_columns = []
        self.basis_data = []

        logger.info(f"🔧 NEUER LINEAR aufgebauter DatenManager gestartet")
        logger.info(f"📋 View: {self.view_guid}, First Call: {self.first_call}")

        # Daten laden
        self._build_system()

    @property
    def current_view_mode(self):
        """
        Dynamisch: 'expert' wenn globaler ExpertMode True, sonst 'normal'.
        """
        try:
            return 'expert' if getattr(self.gcs, 'global_expert_mode', False) else 'normal'
        except Exception:
            return 'normal'
    
    @property
    def stichtag(self):
        """Zentrale Stichtag-Property: Holt immer den Wert aus der globalen Systemsteuerung."""
        try:
            import pdvm_central_systemsteuerung_global
            gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung
            if gcs:
                return gcs.global_stichtag
            return 1001.0
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Zugriff auf zentralen Stichtag: {e}")
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


    def get_abdatum_matrix(self, show_only=True):
        """Gibt die Abdatum-Matrix für die aktuelle Projektion zurück (wie im Matrix-Prototyp)."""
        if not hasattr(self, '_abdatum_matrix') or self._abdatum_matrix is None:
            return None
        # Projektion wie bei get_table_data_for_display
        if show_only:
            columns = sorted([col for col in self.basis_columns if col.get('show', False)], key=lambda c: c.get('displayOrder', 999))
        else:
            columns = sorted(self.basis_columns, key=lambda c: c.get('expertOrder', 999))
        col_names = [col['name'] for col in columns]
        abdatum_matrix = []
        for ab_row in self._abdatum_matrix:
            abdatum_matrix.append([ab_row.get(col, None) for col in col_names])
        return abdatum_matrix
    
    def _load_or_init_column_controls(self, view_felder):
        """
        Linearer Aufbau der ColumnControls:
        - Control-Key ist immer feldname (klein) + _original, Zusatzfelder für date als feldname_alter_original etc.
        - _show-Spalten als feldname_show, Dummy als 'dummy'.
        - Spaltenüberschrift: _original → name (aus Viewdaten) + ' (orig.)', _show → name (aus Viewdaten), Dummy → ''.
        - Das Feld 'anzeige' entfällt, der interne Spaltenname ist immer der Control-Key.
        """
        try:
            import pdvm_central_systemsteuerung_global
            gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=None)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                logger.info(f"✅ ColumnControl-Attribute aus Systemsteuerung geladen für {self.view_guid}")
                attr_map = cc_data["wert"]
            else:
                attr_map = {}
        except Exception as e:
            logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht aus Systemsteuerung laden: {e}")
            attr_map = {}

        columns = []
        expert_order = 0
        display_order = 0

        for feld_config in view_felder:
            feldname_gross = feld_config["feld"]
            feld_name = feldname_gross.lower()
            feld_type = feld_config.get("type", "string")
            gruppe = feld_config.get("gruppe", "PERSDATEN")
            spaltenname = feld_config.get("name", feld_name)

            # _original Control
            name_orig = f"{feld_name}_original"
            attr = attr_map.get(name_orig, {})
            columns.append({
                'name': name_orig,
                'type': feld_type,
                'gruppe': gruppe,
                'feld': feldname_gross,
                'show': attr.get('show', False),
                'expertOrder': attr.get('expertOrder', expert_order),
                'displayOrder': attr.get('displayOrder', display_order),
                'field_config': feld_config,
                'spaltenueberschrift': f"{spaltenname} (orig.)"
            })
            expert_order += 1
            display_order += 1

            # Zusatzfelder für date
            if feld_type == "date":
                for zusatz in ["alter", "jahr", "monat", "tag"]:
                    zusatz_field_config = feld_config.copy()
                    zusatz_field_config["type"] = f"date_{zusatz}"
                    name_zusatz = f"{feld_name}_{zusatz}_original"
                    attr = attr_map.get(name_zusatz, {})
                    columns.append({
                        'name': name_zusatz,
                        'type': f"date_{zusatz}",
                        'gruppe': gruppe,
                        'feld': feldname_gross,
                        'show': attr.get('show', False),
                        'expertOrder': attr.get('expertOrder', expert_order),
                        'displayOrder': attr.get('displayOrder', display_order),
                        'field_config': zusatz_field_config,
                        'spaltenueberschrift': f"{spaltenname} {zusatz} (orig.)"
                    })
                    expert_order += 1
                    display_order += 1

        # _show Controls für alle _original (außer dummy)
        for col in columns[:]:
            if col['name'].endswith('_original'):
                show_name = col['name'].replace('_original', '_show')
                attr = attr_map.get(show_name, {})
                columns.append({
                    'name': show_name,
                    'type': col['type'],
                    'gruppe': col.get('gruppe'),
                    'feld': col.get('feld'),
                    'show': attr.get('show', True),
                    'expertOrder': attr.get('expertOrder', expert_order),
                    'displayOrder': attr.get('displayOrder', display_order),
                    'field_config': col.get('field_config', {}),
                    'spaltenueberschrift': feld_config.get("name", col['name'].replace('_show', ''))
                })
                expert_order += 1
                display_order += 1

        # Dummy Control
        attr = attr_map.get('dummy', {})
        columns.append({
            'name': 'dummy',
            'type': 'dummy',
            'show': attr.get('show', False),
            'expertOrder': attr.get('expertOrder', expert_order),
            'displayOrder': attr.get('displayOrder', display_order),
            'field_config': {},
            'spaltenueberschrift': ''
        })

        # Persistiere nur die Attribute show, expertOrder, displayOrder pro Feldname
        persist_map = {col['name']: {
            'show': col['show'],
            'expertOrder': col['expertOrder'],
            'displayOrder': col['displayOrder']
        } for col in columns}
        try:
            gcs.set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
            gcs.save_values()
            logger.info(f"💾 ColumnControl-Attribute in Systemsteuerung gespeichert für {self.view_guid}")
        except Exception as e:
            logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht speichern: {e}")
        return columns
    
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
        SCHRITT 2: Column Controls linear aufbauen oder aus Systemsteuerung laden
        """
        try:
            columns = self._load_or_init_column_controls(view_felder)
            # displayOrder-Vergabe: show=True ab 0, show=False = expertOrder+1000
            show_counter = 0
            for col in columns:
                if col.get('show', False):
                    col['displayOrder'] = show_counter
                    show_counter += 1
                else:
                    col['displayOrder'] = col.get('expertOrder', 0) + 1000

            # ColumnControl-Objekt für interne Nutzung
            column_control = ColumnControl()
            for col in columns:
                # Verhindere doppelte Schlüsselwörter
                col_kwargs = {k: v for k, v in col.items() if k not in ('name', 'type', 'order')}
                column_control.add_column(
                    col['name'],
                    col.get('type', 'string'),
                    col.get('displayOrder', 9999),
                    **col_kwargs
                )
            logger.info(f"✅ {len(columns)} Column Controls geladen/erstellt")
            return column_control
        except Exception as e:
            logger.error(f"❌ Fehler beim Column Control Aufbau: {e}")
            traceback.print_exc()
            raise
    
    def _get_columns_from_controls(self):
        """SCHRITT 3: Basis-Spalten aus Controls ableiten (KEINE Filterung nach Modus!)"""
        try:
            columns = []
            for col_dict in self.column_control.columns:
                simple_col = {
                    'name': col_dict['name'],
                    'label': col_dict.get('anzeige', col_dict['name']),
                    'type': col_dict.get('type', 'string'),
                    'show': col_dict.get('show', True),
                    'display_order': col_dict.get('order', 999),
                    'display_expert': col_dict.get('expert', False),
                    'field_config': col_dict.get('field_config', {}),
                    'gruppe': col_dict.get('gruppe'),
                    'feld': col_dict.get('feld')
                }
                columns.append(simple_col)
            logger.info(f"✅ {len(columns)} Basis-Spalten (ungefiltert, Modus-Filterung nur in get_columns_for_mode)")
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

            abdatum_matrix = []

            for i, record_info in enumerate(all_records):
                try:
                    data_guid = record_info["uid"]
                    data_dict = record_info["daten_dict"]

                    # 3. set_data pro Zeile
                    working_db.set_data(data_dict, data_guid)

                    # Row-Record erstellen
                    row_record = {'uid_original': data_guid}

                    # 4. get_value pro _original Feld
                    abdatum_row = self._fill_original_columns(row_record, working_db, dt_formatter, collect_abdatum=True)

                    # 5. _show Spalten aus _original übertragen (erstmal 1:1)
                    self._fill_show_columns(row_record)

                    # In Column Control speichern
                    self.column_control.set_row_data(data_guid, row_record)
                    abdatum_matrix.append(abdatum_row)
                    successful_records += 1

                    if (i + 1) % 20 == 0:
                        logger.info(f"   📊 {i+1}/{len(all_records)} Datensätze verarbeitet...")

                except Exception as e:
                    logger.warning(f"⚠️ Fehler bei Datensatz {record_info.get('uid', 'unbekannt')}: {e}")
                    continue

            self._abdatum_matrix = abdatum_matrix
            logger.info(f"✅ {successful_records} Datensätze erfolgreich geladen")
            return successful_records

        except Exception as e:
            logger.error(f"❌ Fehler beim Daten-Laden: {e}")
            traceback.print_exc()
            return 0
    
    def _fill_original_columns(self, row_record: dict, working_db, dt_formatter, collect_abdatum=False):
        """
        SCHRITT 4: _original Spalten befüllen
        Linear durch alle _original Spalten, mit get_value + Zusatzspalten-Logik
        Wenn collect_abdatum=True, wird eine dict-Liste mit ab_zeit pro Spalte zurückgegeben.
        """
        import copy
        abdatum_row = {} if 'collect_abdatum' in locals() or 'collect_abdatum' in globals() else None
        import inspect
        frame = inspect.currentframe()
        args, _, _, values = inspect.getargvalues(frame)
        collect_abdatum = values.get('collect_abdatum', False)
        try:
            for col in self.basis_columns:
                col_name = col['name']
                if not col_name.endswith('_original') or col_name == 'uid_original':
                    continue
                col_type = col.get('type', '')
                gruppe = col.get('gruppe', 'PERSDATEN')
                feld = col.get('feld')
                if gruppe:
                    gruppe = str(gruppe).upper()
                if feld:
                    feld = str(feld).upper()
                if not col_type.startswith("date_"):
                    if feld and gruppe:
                        try:
                            wert = working_db.get_value(gruppe, feld, ab_zeit=self.stichtag)
                            ab_zeit = None
                            if isinstance(wert, dict):
                                ab_zeit = wert.get('ab_zeit', None)
                                if not wert:
                                    row_record[col_name] = ""
                                else:
                                    row_record[col_name] = wert.get('wert', "")
                            else:
                                row_record[col_name] = wert if wert is not None else ""
                            if collect_abdatum:
                                abdatum_row[col_name] = ab_zeit
                            logger.debug(f"✅ {col_name} = {row_record[col_name]} (get_value {gruppe}, {feld}) ab_zeit={ab_zeit}")
                        except Exception as e:
                            logger.debug(f"⚠️ get_value Fehler für {col_name} ({gruppe}, {feld}): {e}")
                            row_record[col_name] = ""
                            if collect_abdatum:
                                abdatum_row[col_name] = None
                    else:
                        row_record[col_name] = ""
                        if collect_abdatum:
                            abdatum_row[col_name] = None
                else:
                    zusatz_typ = col_type.replace("date_", "")
                    basis_col_name = col_name.replace(f"_{zusatz_typ}_original", "_original")
                    if basis_col_name in row_record:
                        basis_wert_raw = row_record[basis_col_name]
                        if isinstance(basis_wert_raw, dict) and 'wert' in basis_wert_raw:
                            basis_wert = basis_wert_raw['wert']
                        else:
                            basis_wert = basis_wert_raw
                        if isinstance(basis_wert, (int, float)) and basis_wert > 0:
                            zusatz_wert = self._berechne_datum_zusatz(basis_wert, zusatz_typ, dt_formatter)
                            row_record[col_name] = zusatz_wert
                        else:
                            row_record[col_name] = ""
                        if collect_abdatum:
                            abdatum_row[col_name] = None
                    else:
                        if feld and gruppe:
                            try:
                                basis_wert_raw = working_db.get_value(gruppe, feld, ab_zeit=self.stichtag)
                                ab_zeit = basis_wert_raw.get('ab_zeit', None) if isinstance(basis_wert_raw, dict) else None
                                basis_wert = basis_wert_raw['wert'] if isinstance(basis_wert_raw, dict) else basis_wert_raw
                                if isinstance(basis_wert, (int, float)) and basis_wert > 0:
                                    zusatz_wert = self._berechne_datum_zusatz(basis_wert, zusatz_typ, dt_formatter)
                                    row_record[col_name] = zusatz_wert
                                else:
                                    row_record[col_name] = ""
                                if collect_abdatum:
                                    abdatum_row[col_name] = ab_zeit
                            except Exception as e:
                                logger.debug(f"⚠️ get_value Fehler für Zusatzspalte {col_name}: {e}")
                                row_record[col_name] = ""
                                if collect_abdatum:
                                    abdatum_row[col_name] = None
                        else:
                            row_record[col_name] = ""
                            if collect_abdatum:
                                abdatum_row[col_name] = None
            if collect_abdatum:
                return abdatum_row
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der _original Spalten: {e}")
            if collect_abdatum:
                return abdatum_row
    
    def _berechne_datum_zusatz(self, original_datum: float, zusatz_typ: str, dt_formatter):
        """Berechnet Datum-Zusatzwerte"""
        try:
            dt_formatter.PdvmDateTime = original_datum
            
            if zusatz_typ == "alter":
                # PRÄZISE TAGESEXAKTE ALTERSBERECHNUNG
                return self._berechne_alter(self.stichtag, original_datum)
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
    
    def _berechne_alter(self, stichtag, datum):
        stdiff = int(stichtag) - int(datum)
        strest = stdiff % 1000
        return int((stdiff - strest) / 1000)

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
    
    def get_table_data_for_display(self):
        """Gibt die Tabellendaten und Spaltennamen für den aktuellen Modus zurück.
        - ExpertMode: alle basis_columns
        - NormalMode: nur show==True, sortiert nach displayOrder
        """
        try:
            if not self.column_control:
                return [], []

            if self.gcs.global_expert_mode:
                columns = list(self.basis_columns)
            else:
                columns = sorted([col for col in self.basis_columns if col.get('show', False)], key=lambda c: c.get('displayOrder', 999))
            display_columns = [col['name'] for col in columns]

            display_data = []
            guids_to_remove = []
            for guid in list(self.column_control.row_guids):
                row_data = self.column_control.get_row_data(guid)
                # Prüfe, ob alle Felder leer sind (außer uid_original und uid_show)
                all_empty = True
                for col in display_columns:
                    if col in ('uid_original', 'uid_show'):
                        continue
                    if str(row_data.get(col, "")).strip() != "":
                        all_empty = False
                        break
                if all_empty:
                    guids_to_remove.append(guid)
                    continue
                display_row = tuple(row_data.get(col, "") for col in display_columns)
                display_data.append(display_row)

            # Entferne leere Zeilen aus Controls
            for guid in guids_to_remove:
                if guid in self.column_control.row_guids:
                    self.column_control.row_guids.remove(guid)
                for col_data in self.column_control.column_data.values():
                    if guid in col_data:
                        del col_data[guid]

            return display_data, display_columns

        except Exception as e:
            logger.error(f"❌ Fehler bei get_table_data_for_display: {e}")
            return [], []
    
