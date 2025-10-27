
#!/usr/bin/env python3
"""
NEUER PdvmViewDatenManager - VollstÃ¤ndig linear aufgebaut
Alle Methoden neu erstellt basierend auf der linearen Architektur
"""

import logging
import traceback
from typing import Any, Dict, List, Optional

# Logging Setup
logger = logging.getLogger(__name__)

from pdvm_central_systemsteuerung import get_gcs as gcs
from pdvm_projection_manager import get_projection_manager
from pdvm_matrix_pipeline import get_matrix_pipeline


class ColumnControl:
    """Vereinfachte Column Control Klasse"""
    
    def __init__(self):
        self.columns = []
        self.row_guids = []
        self.column_data = {}
        
    def add_column(self, name: str, col_type: str, order: int, **kwargs):
        """FÃ¼gt eine Spalte hinzu"""
        column = {
            'name': name,
            'type': col_type,
            'order': order,
            **kwargs
        }
        self.columns.append(column)
        
    def set_row_data(self, guid: str, row_dict: dict):
        """Setzt alle Spaltenwerte fÃ¼r eine GUID"""
        if guid not in self.row_guids:
            self.row_guids.append(guid)
        
        for column_name, value in row_dict.items():
            if column_name not in self.column_data:
                self.column_data[column_name] = {}
            self.column_data[column_name][guid] = value
            
    def get_row_data(self, guid: str):
        """Holt alle Spaltenwerte fÃ¼r eine GUID"""
        row_data = {}
        for column_name in self.column_data.keys():
            row_data[column_name] = self.column_data[column_name].get(guid, "")
        return row_data


class PdvmViewDatenManager:
    """
    NEUER LINEAR AUFGEBAUTER Daten Manager mit Widget-Kontrolle
    Komplett neu erstellt mit linearer Architektur
    
    NEUE ARCHITEKTUR: DatenManager (persistent) kontrolliert Widget (disposable)
    """
    
    def __init__(self, call_daten, widget=None, parent_app=None):
        self.call_daten = call_daten
        self.widget = widget  # Aktuelles kontrolliertes Widget (kann None sein)
        self._parent_app = parent_app

        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid")
        self.first_call = call_daten.get("first_call", True)

        # Column Control System - PERSISTENT!
        self.column_control = None
        self.basis_columns = []
        self.basis_data = []  # DEPRECATED - wird durch Pipeline ersetzt
        
        # === NEU: Matrix Pipeline (PERSISTENT!) ===
        self.matrix_pipeline = get_matrix_pipeline(self.view_guid)

        logger.info(f"ðŸ”§ NEUER LINEAR aufgebauter DatenManager gestartet (PERSISTENT)")
        logger.info(f"ðŸ“‹ View: {self.view_guid}, First Call: {self.first_call}")
        logger.info(f"ðŸš€ Matrix Pipeline: {self.matrix_pipeline}")

        # Daten laden
        self._build_system()
    
    def update_call_daten(self, new_call_daten: dict):
        """Aktualisiert call_daten fÃ¼r bestehenden Manager (ohne Neuaufbau)."""
        self.call_daten.update(new_call_daten)
        logger.info(f"ðŸ“ Call-Daten fÃ¼r persistenten Manager aktualisiert: {self.view_guid}")
    
    def create_controlled_widget(self, parent=None, reload_callback=None):
        """
        KORREKTE ARCHITEKTUR: DatenManager erstellt bewÃ¤hrtes Widget mit allen Features.
        Verwendet das bewÃ¤hrte, funktionierende Widget - nur Architektur umgekehrt.
        """
        try:
            # Das BEWÃ„HRTE Widget mit allen Features verwenden
            from pdvm_view_widget_corrected_architecture import PdvmViewWidget
            
            # Widget erstellen und persistenten DatenManager Ã¼bergeben
            widget = PdvmViewWidget(
                call_daten=self.call_daten,
                persistent_view_manager=self,  # Persistenter Manager wird Ã¼bergeben
                parent=parent,
                reload_callback=reload_callback
            )
            
            # Widget-Referenz fÃ¼r refresh_controlled_widget
            self.widget = widget
            
            logger.info(f"âœ… BewÃ¤hrtes Widget mit allen Features erfolgreich erstellt")
            return widget
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Erstellen des bewÃ¤hrten Widgets: {e}")
            traceback.print_exc()
            raise
    
    def refresh_controlled_widget(self):
        """
        KORREKTE ARCHITEKTUR: Refresht das bewÃ¤hrte Widget Ã¼ber die persistenten Daten.
        Verwendet die bewÃ¤hrten Refresh-Methoden.
        """
        if self.widget is None:
            logger.warning("âš ï¸ Kein Widget zum Refreshen vorhanden")
            return None
            
        try:
            logger.info("ðŸ”„ Refreshe bewÃ¤hrtes Widget Ã¼ber persistenten DatenManager")
            
            # Persistente Daten aktualisieren (wie original)
            if hasattr(self, 'refresh_controls_and_projection'):
                self.refresh_controls_and_projection()
            
            # Widget Ã¼ber bewÃ¤hrte _load_table_data Methode aktualisieren
            if hasattr(self.widget, '_load_table_data'):
                self.widget._load_table_data()
                
            # Header aktualisieren
            if hasattr(self.widget, 'update_header_text'):
                self.widget.update_header_text()
            
            logger.info(f"âœ… Widget erfolgreich Ã¼ber persistenten DatenManager refresht")
            return self.widget
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Widget-Refresh: {e}")
            traceback.print_exc()
            return None
    
    def _populate_widget(self, widget):
        """FÃ¼llt das Widget mit den aktuellen Daten vom persistenten DatenManager."""
        try:
            if not widget:
                return
                
            # Widget-interne _load_table_data Methode aufrufen wenn vorhanden
            if hasattr(widget, '_load_table_data'):
                widget._load_table_data()
            
            # Header aktualisieren wenn vorhanden  
            if hasattr(widget, 'update_header_text'):
                widget.update_header_text()
                
            logger.info("âœ… Widget mit persistenten DatenManager-Daten befÃ¼llt")
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim BefÃ¼llen des Widgets: {e}")
            traceback.print_exc()

    def _build_system(self):
        """
        SCHRITT-FÃœR-SCHRITT AUFBAU:
        1. ViewDaten laden
        2. Controls aufbauen
        3. Daten laden (nur bei first_call oder Stichtagswechsel)
        """
        try:
            logger.info("ðŸ”§ SCHRITT 1: ViewDaten laden")
            view_felder = self._load_view_felder()

            logger.info("ðŸ”§ SCHRITT 2: Column Controls aufbauen")
            if self.first_call:
                # Neuaufruf: Controls neu aufbauen
                self.column_control = self._build_column_controls(view_felder)
            else:
                # Refresh: Controls aus Systemsteuerung laden
                logger.info("ðŸ“Š Refresh-Modus: Lade Controls aus Systemsteuerung")
                self.column_control = self._build_column_controls_from_systemsteuerung()

            logger.info("ðŸ”§ SCHRITT 3: Basis-Spalten ableiten")
            if self.first_call:
                # Neuaufruf: Basis-Spalten neu ableiten
                self.basis_columns = self._get_columns_from_controls()
            else:
                # Refresh: Basis-Spalten immer neu ableiten (weil Controls geladen wurden)
                logger.info("ðŸ“Š Refresh-Modus: Basis-Spalten aus geladenen Controls ableiten")
                self.basis_columns = self._get_columns_from_controls()

            logger.info("ðŸ”§ SCHRITT 4: Daten laden (nur falls first_call)")
            if self.first_call:
                records_loaded = self._load_records_data(limit=100)
                logger.info(f"âœ… {records_loaded} DatensÃ¤tze geladen")
                
                # === NEU: Pipeline aufbauen nach Daten-Laden ===
                logger.info("ðŸ”§ SCHRITT 5: Matrix Pipeline aufbauen")
                self._build_matrix_pipeline()
            else:
                logger.info("ðŸ“Š SKIP: Datenladen Ã¼bersprungen (first_call=False)")

        except Exception as e:
            logger.error(f"âŒ Fehler beim System-Aufbau: {e}")
            traceback.print_exc()
            raise
        finally:
            # Nach dem ersten Aufruf ist first_call immer False
            if self.first_call:
                self.first_call = False
                logger.info("ðŸ”§ first_call auf False gesetzt nach erstem System-Aufbau")

    def refresh_controls_and_projection(self):
        """
        Aktualisiert nur die Parameter in den bestehenden Controls (show, order) aus der Systemsteuerung
        und baut dann die Projektion neu auf. Die Controls selbst bleiben erhalten - nur die Projektions-Parameter Ã¤ndern sich.
        """
        try:
            logger.info("ðŸ”„ Control-Parameter aus Systemsteuerung laden und Projektion neu aufbauen")
            
            # Lade die aktuellen ColumnControl-Parameter aus der Systemsteuerung
            cc_data = gcs().get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            column_attributes = cc_data.get("wert", {}) if cc_data and "wert" in cc_data else {}
            
            if column_attributes and hasattr(self, 'basis_columns'):
                logger.info(f"ðŸ“¥ Aktualisiere Parameter fÃ¼r {len(self.basis_columns)} bestehende Controls")
                
                # Aktualisiere nur die Parameter in den bestehenden basis_columns
                for col in self.basis_columns:
                    col_name = col['name']
                    if col_name in column_attributes:
                        new_attrs = column_attributes[col_name]
                        # Nur die Projektions-Parameter aktualisieren
                        col['show'] = new_attrs.get('show', col.get('show', False))
                        col['expertOrder'] = new_attrs.get('expertOrder', col.get('expertOrder', 999))
                        col['displayOrder'] = new_attrs.get('displayOrder', col.get('displayOrder', 999))
                        logger.debug(f"  {col_name}: show={col['show']}, eO={col['expertOrder']}, dO={col['displayOrder']}")
                
                logger.info("âœ… Control-Parameter aktualisiert - Projektion wird neu aufgebaut")
                logger.info(f"   Aktuelle Modus-Einstellung: ExpertMode={gcs().global_expert_mode}")
            else:
                logger.warning("âš ï¸ Keine ColumnControls in Systemsteuerung gefunden oder keine basis_columns vorhanden")
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Refresh der Control-Parameter: {e}")
            traceback.print_exc()
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Refresh der Controls/Projektion: {e}")
            traceback.print_exc()

    def _build_matrix_pipeline(self):
        """
        Baut die vollstÃ¤ndige Matrix-Pipeline auf:
        BasisMatrix â†’ FilterMatrix â†’ SortMatrix â†’ Projektion
        
        Wird aufgerufen nach _load_records_data()
        """
        try:
            logger.info("ðŸš€ === MATRIX PIPELINE AUFBAU START ===")
            
            # SCHRITT 1: Alle Spaltennamen sammeln (inkl. _abdatum, _formatiertes_abdatum)
            all_columns = set()
            if self.column_control and hasattr(self.column_control, 'column_data'):
                for col_name in self.column_control.column_data.keys():
                    all_columns.add(col_name)
            all_columns_list = sorted(list(all_columns))
            logger.info(f"ðŸ“‹ {len(all_columns_list)} Spalten gefunden (inkl. _abdatum/_formatiertes_abdatum)")
            
            # SCHRITT 2: BasisMatrix aufbauen
            logger.info("ðŸ”¨ SCHRITT 1: BasisMatrix aufbauen")
            self.matrix_pipeline.build_basis_matrix(self.column_control, all_columns_list)
            
            # SCHRITT 3: FilterMatrix aufbauen (aktuell kein Filter)
            logger.info("ðŸ”¨ SCHRITT 2: FilterMatrix aufbauen")
            self.matrix_pipeline.apply_filter(filter_func=None)  # TODO: Filter-Funktion integrieren
            
            # SCHRITT 4: SortMatrix aufbauen (aktuell keine Sortierung)
            logger.info("ðŸ”¨ SCHRITT 3: SortMatrix aufbauen")
            self.matrix_pipeline.apply_sort(sort_column=None, reverse=False)  # TODO: Sort-Parameter integrieren
            
            # SCHRITT 5: Projektion aufbauen (nur sichtbare _show Spalten)
            logger.info("ðŸ”¨ SCHRITT 4: Projektion aufbauen")
            # Sichtbare Spalten ermitteln (mit name_original/name_show IMMER sichtbar)
            # Hole Projektion aus GCS (berücksichtigt Expert Mode automatisch)
            projection_table = gcs().get_current_projection(self.view_guid, 'table')
            
            if projection_table:
                visible_columns = projection_table
                logger.info(f"👁️ Sichtbare Spalten aus GCS: {len(visible_columns)}")
            else:
                # Fallback: Alle Spalten außer dummy und row_type
                visible_columns = [col['name'] for col in self.basis_columns 
                                 if col['name'] not in ('dummy', 'row_type')]
                logger.warning(f"⚠️ Keine GCS-Projektion - Fallback: {len(visible_columns)} Spalten")
            logger.info(f"ðŸ‘ï¸ Sichtbare Spalten: {len(visible_columns)}")
            self.matrix_pipeline.project(visible_columns)
            
            # Pipeline-Status loggen
            self.matrix_pipeline.log_pipeline_status()
            
            logger.info("âœ… === MATRIX PIPELINE AUFBAU ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Pipeline-Aufbau: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_visible_columns(self):
        """
        Ermittelt sichtbare Spalten mit SPEZIAL-Logik.
        
        WICHTIG: name_original und name_show sind IMMER sichtbar!
        
        Returns:
            list: Liste der sichtbaren Spalten-Namen
        """
        visible_columns = []
        for col in self.basis_columns:
            col_name = col['name']
            is_visible = col.get('show', False)
            
            # SPEZIAL: name_original und name_show sind IMMER sichtbar
            if col_name in ('name_original', 'name_show'):
                is_visible = True
            
            if is_visible:
                visible_columns.append(col_name)
        
        return visible_columns
    
    def rebuild_pipeline_with_stichtag(self):
        """
        Baut Pipeline nach Stichtag-Wechsel neu auf:
        1. Cached Records mit neuem Stichtag in BasisMatrix befÃ¼llen
        2. Pipeline komplett durchlaufen
        
        WICHTIG: Wird von Refresh-Button aufgerufen
        """
        try:
            logger.info("ðŸ”„ === REBUILD PIPELINE MIT NEUEM STICHTAG ===")
            logger.info(f"ðŸ“… Aktueller Stichtag: {gcs().stichtag}")
            
            # SCHRITT 1: BasisMatrix mit cached records neu befÃ¼llen
            if hasattr(self, '_cached_all_records') and self._cached_all_records:
                logger.info("â™»ï¸ Verwende gecachte Records fÃ¼r Stichtag-Wechsel")
                
                # Daten NEU verarbeiten mit neuem Stichtag
                logger.info("ðŸ”„ Verarbeite Daten mit neuem Stichtag...")
                self._reprocess_cached_records_with_new_stichtag()
                
                # BasisMatrix neu aufbauen
                all_columns = list(self.column_control.column_data.keys())
                self.matrix_pipeline.build_basis_matrix(self.column_control, all_columns)
                
                # Pipeline durchlaufen
                self.matrix_pipeline.rebuild_from_basis()
                
                logger.info("âœ… Pipeline mit neuem Stichtag komplett durchlaufen")
                return True
            else:
                logger.warning("âš ï¸ Keine gecachten Records vorhanden - lade Daten neu")
                self._load_records_data(limit=100)
                self._build_matrix_pipeline()
                return True
                
        except Exception as e:
            logger.error(f"âŒ Fehler beim Pipeline-Rebuild: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_search_filter(self, search_string: str, visible_columns: list):
        """
        EINFACHE SUCHE: Wendet Filter auf BasisMatrix an
        
        Args:
            search_string: Suchtext (aus Dialog)
            visible_columns: Sichtbare Spalten fÃ¼r Suche
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"ðŸ” Matrix Manager: Wende Filter an: '{search_string}'")
            
            if not search_string:
                # Leere Suche = Pipeline ohne Filter
                logger.info("ðŸ”„ Leere Suche - Pipeline ohne Filter durchlaufen")
                self.matrix_pipeline.rebuild_from_basis()
                return True
            
            # Filter-Funktion erstellen
            search_lower = search_string.lower()
            
            def search_filter(row_data):
                """Sucht in sichtbaren Spalten mit 'enthÃ¤lt'"""
                for col_key in visible_columns:
                    if col_key in row_data:
                        value_str = str(row_data[col_key]).lower() if row_data[col_key] is not None else ''
                        if search_lower in value_str:
                            return True
                return False
            
            # Filter anwenden â†’ FilterMatrix
            self.matrix_pipeline.apply_filter(search_filter)
            
            # Rest der Pipeline durchlaufen (Sort + Projection)
            # WICHTIG: rebuild_from_basis wÃ¼rde BasisMatrix nehmen!
            # Wir mÃ¼ssen manuell Sort und Projection machen:
            self.matrix_pipeline.apply_sort(
                self.matrix_pipeline.sort_column,
                self.matrix_pipeline.sort_reverse
            )
            # Verwende _get_visible_columns() für konsistente name-Spalten-Logik
            self.matrix_pipeline.project(self._get_visible_columns())
            
            logger.info(f"âœ… Filter angewendet: {self.matrix_pipeline.filter_matrix.get_row_count()} Zeilen")
            return True
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Anwenden des Filters: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _reprocess_cached_records_with_new_stichtag(self):
        """
        Verarbeitet gecachte Records mit neuem Stichtag
        Aktualisiert column_control mit neuen Werten (3-Ebenen)
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from pdvm_datetime import Pdvm_DateTime
            
            # temp_instance und temp_dt initialisieren (NEUE SIGNATUR)
            temp_instance = PdvmCentralDatenbank(
                table_name=self.view_table,
                guid=None
            )
            temp_dt = gcs().temp_dt_inst
            
            logger.info(f"ðŸ”„ Verarbeite {len(self._cached_all_records)} gecachte Records mit neuem Stichtag")
            
            for record_info in self._cached_all_records:
                data_guid = record_info["uid"]
                data_dict = record_info["daten_dict"]
                
                # set_data befÃ¼llt temp_instance
                temp_instance.set_data(data_dict, data_guid)
                
                # Row-Record neu erstellen - ORIGINAL SUFFIX!
                row_record = {'uid_original': data_guid}
                row_record['uid_original_abdatum'] = None
                row_record['uid_original_formatiertes_abdatum'] = None
                
                # _original Felder neu befÃ¼llen mit neuem Stichtag
                self._fill_original_columns(row_record, temp_instance, temp_dt)
                
                # _show Spalten neu befÃ¼llen
                self._fill_show_columns(row_record, temp_dt)
                
                # Column Control aktualisieren
                self.column_control.set_row_data(data_guid, row_record)
            
            logger.info("âœ… Alle Records mit neuem Stichtag verarbeitet")
            
        except Exception as e:
            logger.error(f"âŒ Fehler beim Reprocessing: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_control_parameters_only(self):
        """
        NUR-PARAMETER-REFRESH: Aktualisiert nur die show/order Parameter ohne neue Controls zu erstellen.
        Wird bei Refresh verwendet wenn keine bestehenden Controls vorhanden sind (Notfall).
        """
        try:
            from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
            gcs = PdvmCentralSystemsteuerung()
            
            # Lade gespeicherte Attribute aus Systemsteuerung
            cc_data = gcs().get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                attr_map = cc_data["wert"]
                logger.info(f"ðŸ”„ Parameter-Refresh: {len(attr_map)} gespeicherte Control-Attribute geladen")
                
                # Erstelle minimale Controls nur aus gespeicherten Daten (ohne neue hinzuzufÃ¼gen)
                columns = []
                for col_name, attrs in attr_map.items():
                    col = {
                        'name': col_name,
                        'show': attrs.get('show', False),
                        'expertOrder': attrs.get('expertOrder', 0),
                        'displayOrder': attrs.get('displayOrder', 0),
                        'type': 'unknown',  # Typ ist fÃ¼r Refresh nicht wichtig
                        'spaltenueberschrift': col_name.replace('_', ' ').title()
                    }
                    columns.append(col)
                
                # Simuliere die Controls-Struktur fÃ¼r Refresh
                self.column_control = {'columns': columns}
                logger.info(f"ðŸ”„ Parameter-Refresh: {len(columns)} minimale Controls erstellt")
                
            else:
                logger.error("âŒ Keine gespeicherten Control-Parameter fÃ¼r Refresh gefunden")
                
        except Exception as e:
            logger.error(f"âŒ Fehler beim Parameter-Refresh: {e}")
            traceback.print_exc()

    def _build_column_controls_from_systemsteuerung(self):
        """
        REFRESH-MODUS: Baut Column Controls aus gespeicherten Systemsteuerung-Daten auf.
        Wird nur bei Refresh (first_call=False) verwendet.
        """
        try:
            from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
            gcs = PdvmCentralSystemsteuerung()
            
            # Lade gespeicherte Attribute aus Systemsteuerung
            cc_data = gcs().get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                attr_map = cc_data["wert"]
                logger.info(f"ðŸ”„ Refresh-Modus: {len(attr_map)} Control-Attribute aus Systemsteuerung geladen")
                
                # Erstelle Controls aus gespeicherten Daten
                columns = []
                for col_name, attrs in attr_map.items():
                    col = {
                        'name': col_name,
                        'show': attrs.get('show', False),
                        'expertOrder': attrs.get('expertOrder', 0),
                        'displayOrder': attrs.get('displayOrder', 0),
                        'type': self._guess_column_type(col_name),
                        'spaltenueberschrift': self._create_column_header(col_name),
                        'field_config': {}  # Minimale Config fÃ¼r Refresh
                    }
                    columns.append(col)
                
                logger.info(f"âœ… Refresh-Modus: {len(columns)} Controls aus Systemsteuerung aufgebaut")
                return {'columns': columns}
                
            else:
                logger.error("âŒ Refresh-Modus: Keine ColumnControls in Systemsteuerung gefunden!")
                return None
                
        except Exception as e:
            logger.error(f"âŒ Fehler beim Aufbau der Controls aus Systemsteuerung: {e}")
            traceback.print_exc()
            return None

    def _guess_column_type(self, col_name):
        """ErrÃ¤t den Spaltentyp aus dem Namen (fÃ¼r Refresh-Modus)."""
        if 'geburtsdatum' in col_name:
            if 'alter' in col_name:
                return 'date_alter'
            elif 'jahr' in col_name:
                return 'date_jahr'
            elif 'monat' in col_name:
                return 'date_monat'
            elif 'tag' in col_name:
                return 'date_tag'
            else:
                return 'date'
        elif col_name == 'dummy':
            return 'dummy'
        elif col_name.startswith(('uid', 'name')):
            return 'string'
        else:
            return 'string'

    def _create_column_header(self, col_name):
        """Erstellt eine Spaltenüberschrift aus dem Control-Namen (für Refresh-Modus)."""
        if col_name == 'uid_original':
            return 'UID (orig.)'
        elif col_name == 'uid_show':
            return 'UID'
        elif col_name == 'name_original':
            return 'Name (orig.)'
        elif col_name == 'name_show':
            return 'Name'
        elif col_name == 'dummy':
            return ''
        elif col_name.endswith('_original'):
            base_name = col_name.replace('_original', '').replace('_', ' ').title()
            return f"{base_name} (orig.)"
        elif col_name.endswith('_show'):
            base_name = col_name.replace('_show', '').replace('_', ' ').title()
            return base_name
        else:
            return col_name.replace('_', ' ').title()

    def _debug_print_matrix_row(self, row_data: dict, row_idx: int = 0):
        """
        Erweiterte Debug-Ausgabe einer Matrix-Row mit allen 3 Ebenen
        
        Zeigt speziell:
        - uid_original (GUID)
        - familienname_original mit allen 3 Ebenen
        - Andere wichtige Felder
        """
        logger.info(f"ðŸ” === MATRIX ROW {row_idx} DEBUG (3-EBENEN) ===")
        
        # GUID
        guid = row_data.get('uid_original', 'UNBEKANNT')
        logger.info(f"  ðŸ‘¤ GUID: {guid}")
        
        # Familienname mit 3 Ebenen
        if 'familienname_original' in row_data:
            fn_wert = row_data.get('familienname_original')
            fn_abdatum = row_data.get('familienname_original_abdatum')
            fn_formatiert = row_data.get('familienname_original_formatiertes_abdatum')
            
            logger.info(f"  ðŸ“‹ familienname_original:")
            logger.info(f"    â”œâ”€ ðŸ—„ï¸ EBENE 1 (Wert):       '{fn_wert}'")
            logger.info(f"    â”œâ”€ ðŸ“… EBENE 2 (AB-Datum):   {fn_abdatum}")
            logger.info(f"    â””â”€ ðŸŽ¨ EBENE 3 (Formatiert): '{fn_formatiert}'")
        else:
            logger.warning(f"  âš ï¸ familienname_original NICHT in row_data!")
        
        # Vorname und Geburtsdatum
        for key in ['vorname_original', 'geburtsdatum_original']:
            if key in row_data:
                wert = row_data.get(key)
                abdatum = row_data.get(f"{key}_abdatum")
                formatiert = row_data.get(f"{key}_formatiertes_abdatum")
                logger.info(f"  ðŸ“‹ {key}: '{wert}' | abdatum={abdatum} | formatiert='{formatiert}'")
        
        # Alle Keys zeigen (erste 20)
        all_keys = list(row_data.keys())
        logger.info(f"  ðŸ—ï¸ Alle Keys ({len(all_keys)}): {', '.join(all_keys[:20])}...")

    def get_abdatum_matrix(self, show_only=True):
        """
        Gibt die Abdatum-Matrix fÃ¼r die aktuelle Projektion zurÃ¼ck
        
        VERWENDET EBENE 3 (__formatiert Suffix) fÃ¼r UI-Tooltips
        
        Args:
            show_only: Nur sichtbare Spalten (True) oder alle (False)
        
        Returns:
            List[List[str]]: 2D-Matrix mit formatierten Abdatum-Werten
        """
        logger.info("ðŸ” === get_abdatum_matrix() START ===")
        
        if not self.column_control:
            logger.error("âŒ column_control ist None!")
            return None
            
        # Projektion ermitteln
        if show_only:
            columns = sorted([col for col in self.basis_columns if col.get('show', False)], key=lambda c: c.get('displayOrder', 999))
        else:
            columns = sorted(self.basis_columns, key=lambda c: c.get('expertOrder', 999))
            
        col_names = [col['name'] for col in columns]
        logger.info(f"ðŸ“Š Spaltennamen ({len(col_names)}): {col_names[:5]}...")
        
        abdatum_matrix = []
        
        # Ãœber alle GUIDs iterieren
        guids = list(self.column_control.row_guids)
        logger.info(f"ðŸ‘¤ GUIDs ({len(guids)}): {guids[:3]}...")
        
        for row_idx, guid in enumerate(guids):
            row_data = self.column_control.get_row_data(guid)
            
            # DEBUG: Erste Row detailliert ausgeben
            if row_idx == 0:
                self._debug_print_matrix_row(row_data, row_idx)
            
            abdatum_row = []
            for col_idx, col_name in enumerate(col_names):
                # EBENE 3: Formatiertes Abdatum holen (_formatiertes_abdatum Suffix)
                formatiert = row_data.get(f"{col_name}_formatiertes_abdatum")
                abdatum_row.append(formatiert)
                
                # DEBUG: Log fÃ¼r familienname
                if row_idx == 0 and col_name == 'familienname_original':
                    logger.info(f"  ðŸ” familienname_original_formatiertes_abdatum = '{formatiert}'")
            
            abdatum_matrix.append(abdatum_row)
            
        logger.info(f"âœ… Abdatum-Matrix erstellt: {len(abdatum_matrix)} Zeilen, {len(col_names)} Spalten")
        
        # DEBUG: Zeige erste Zeile
        if abdatum_matrix and abdatum_matrix[0]:
            logger.info(f"ðŸ” Erste Zeile Abdatum-Matrix (erste 5): {abdatum_matrix[0][:5]}")
        
        return abdatum_matrix
    
    def _load_or_init_column_controls(self, view_felder):
        """
        LINEARES VORGEHEN fÃ¼r ColumnControls (vereinfacht):
        
        1. Baue IMMER Standard-Controls mit Standard-Sortierung auf (0, 1, 2, ...)
        2. Synchronisiere Attribute aus Systemsteuerung in bestehende Controls
        3. Fehlende Controls (nicht in Systemsteuerung) bekommen Order +1000 und show=true (_show)
        4. Bei Order >1000 gefunden: Alle neu nummerieren (0, 1, 2, ...) und in Systemsteuerung speichern
        
        Control-Namen:
        - _original-Spalten als feldname_original, uid_original (System).
        - _show-Spalten als feldname_show, Dummy als 'dummy'.
        - SpaltenÃ¼berschrift: _original â†’ name (aus Viewdaten) + ' (orig.)', _show â†’ name (aus Viewdaten), Dummy â†’ ''.
        """
        # SCHRITT 1: Lade gespeicherte Attribute aus Systemsteuerung
        try:
            cc_data = gcs().get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                logger.info(f"âœ… ColumnControl-Attribute aus Systemsteuerung geladen fÃ¼r {self.view_guid}")
                attr_map = cc_data["wert"]
                logger.info(f"ðŸ” Geladene Attribute: {len(attr_map)} Controls")
            else:
                logger.info(f"â„¹ï¸ Keine ColumnControl-Attribute gefunden")
                attr_map = {}
        except Exception as e:
            logger.warning(f"âš ï¸ Konnte ColumnControl-Attribute nicht aus Systemsteuerung laden: {e}")
            attr_map = {}

        # SCHRITT 2: Baue IMMER Standard-Controls mit Standard-Sortierung auf
        columns = []
        order_counter = 0  # Beginne bei 0 für Standard-Sortierung

        # SYSTEM-SPALTEN: uid_original
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

        # SYSTEM-SPALTEN: name_original (analog zu uid)
        name_orig_col = {
            'name': 'name_original',
            'type': 'string',
            'gruppe': 'SYSTEM',
            'feld': 'NAME',
            'show': False,  # Standard: unsichtbar (nur im Expert Mode)
            'expertOrder': order_counter,
            'displayOrder': order_counter,
            'field_config': {'feld': 'NAME', 'name': 'Satzname', 'type': 'string'},
            'spaltenueberschrift': 'Satzname (orig.)'
        }
        columns.append(name_orig_col)
        order_counter += 1

        # VIEW-FELDER: _original Controls erstellen
        for feld_config in view_felder:
            feldname_gross = feld_config["feld"]
            feld_name = feldname_gross.lower()
            feld_type = feld_config.get("type", "string")
            gruppe = feld_config.get("gruppe", "PERSDATEN")
            spaltenname = feld_config.get("name", feld_name)

            # _original Control
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

            # Zusatzfelder fÃ¼r date
            if feld_type == "date":
                zusatz_namen = {
                    "alter": "Alter",
                    "jahr": "Jahr", 
                    "monat": "Monat",
                    "tag": "Tag"
                }
                
                for zusatz in ["alter", "jahr", "monat", "tag"]:
                    zusatz_field_config = feld_config.copy()
                    zusatz_field_config["type"] = f"date_{zusatz}"
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
                        'spaltenueberschrift': f"{spaltenname} {zusatz_anzeige} (orig.)"
                    }
                    columns.append(col)
                    order_counter += 1

        # _show Controls fÃ¼r alle _original (auÃŸer dummy)
        for col in columns[:]:
            if col['name'].endswith('_original'):
                show_name = col['name'].replace('_original', '_show')
                
                # Ãœberschrift: Gleich wie Original-Spalte, aber ohne "(orig.)"
                original_ueberschrift = col.get('spaltenueberschrift', '')
                show_ueberschrift = original_ueberschrift.replace(' (orig.)', '') if original_ueberschrift else show_name
                
                show_col = {
                    'name': show_name,
                    'type': col['type'],
                    'gruppe': col.get('gruppe'),
                    'feld': col.get('feld'),
                    'show': True,  # Standard: _show Spalten sind sichtbar
                    'expertOrder': order_counter,
                    'displayOrder': order_counter,
                    'field_config': col.get('field_config', {}),
                    'spaltenueberschrift': show_ueberschrift
                }
                columns.append(show_col)
                order_counter += 1

        # Dummy Control
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

        # ðŸ†• row_type Control - EnthÃ¤lt Zeilen-Metadaten (data/group_header/group_footer)
        row_type_col = {
            'name': 'row_type',
            'type': 'dict',  # Dict-Typ fÃ¼r flexible Metadaten
            'show': False,  # NIEMALS in Projektion sichtbar
            'expertOrder': order_counter,
            'displayOrder': order_counter,
            'field_config': {},
            'spaltenueberschrift': 'Zeilen-Typ',
            'sortable': False,  # Nicht sortierbar
            'filterable': False  # Nicht filterbar
        }
        columns.append(row_type_col)
        order_counter += 1

        logger.info(f"ðŸ”§ {len(columns)} Standard-Controls mit Standard-Sortierung erstellt (inkl. dummy + row_type)")

        # SCHRITT 3: Synchronisation - Attribute aus Systemsteuerung in bestehende Controls Ã¼bernehmen
        found_new_controls = False
        
        for col in columns:
            col_name = col['name']
            if col_name in attr_map:
                # Bestehende Einstellungen Ã¼bernehmen
                saved_attrs = attr_map[col_name]
                col['show'] = saved_attrs.get('show', col['show'])
                col['expertOrder'] = saved_attrs.get('expertOrder', col['expertOrder'])
                col['displayOrder'] = saved_attrs.get('displayOrder', col['displayOrder'])
            else:
                # NEUES Control nicht in Systemsteuerung gefunden
                logger.debug(f"ðŸ†• Neues Control gefunden: {col_name}")
                col['expertOrder'] += 1000  # Markierung als "neu"
                col['displayOrder'] += 1000  # Markierung als "neu"
                # _show Controls: show=True, andere: show bleibt
                if col_name.endswith('_show'):
                    col['show'] = True
                found_new_controls = True

        logger.info(f"âœ… Synchronisation abgeschlossen - {len(columns)} Controls, neue gefunden: {found_new_controls}")

        # SCHRITT 4: Bei neuen Controls (Order >1000): Alle neu nummerieren
        if found_new_controls:
            logger.info(f"ðŸ”§ Neue Controls gefunden - nummeriere alle Order-Werte neu")
            
            # ExpertOrder neu nummerieren
            expert_sorted = sorted(columns, key=lambda x: x['expertOrder'])
            for i, col in enumerate(expert_sorted):
                col['expertOrder'] = i
                
            # DisplayOrder neu nummerieren
            display_sorted = sorted(columns, key=lambda x: x['displayOrder'])
            for i, col in enumerate(display_sorted):
                col['displayOrder'] = i
                
            logger.info(f"âœ… Order-Werte neu nummeriert: {len(columns)} Controls")

        # SCHRITT 5: Persistierung nur bei neuen Controls UND first_call
        # Bei Refresh (first_call=False) niemals speichern!
        if found_new_controls and self.first_call:
            try:
                # Hole existierendes controls Dictionary aus GCS
                existing_controls, _ = gcs().db.get_value(self.view_guid, "controls")
                if not existing_controls or not isinstance(existing_controls, dict):
                    existing_controls = {}
                    logger.info(f"Erstelle neues controls Dictionary fuer {self.view_guid}")
                else:
                    logger.info(f"Lade existierendes controls Dictionary mit {len(existing_controls)} Controls")
                
                # Merge neue/geaenderte Controls (komplettes Control-Objekt!)
                new_count = 0
                updated_count = 0
                for col in columns:
                    control_name = col['name']
                    if control_name not in existing_controls:
                        # Neues Control - komplettes Objekt speichern
                        existing_controls[control_name] = col
                        new_count += 1
                        logger.debug(f"  Neues Control: {control_name}")
                    else:
                        # Existierendes Control - nur Attribute aktualisieren
                        existing_controls[control_name]['show'] = col['show']
                        existing_controls[control_name]['expertOrder'] = col['expertOrder']
                        existing_controls[control_name]['displayOrder'] = col['displayOrder']
                        updated_count += 1
                
                # Speichere zurueck ins controls Dictionary
                gcs().db.set_value(self.view_guid, "controls", existing_controls)
                gcs().save_values()
                logger.info(f"Controls gespeichert fuer {self.view_guid}: {new_count} neue, {updated_count} aktualisiert, {len(existing_controls)} total")
                
                # Projektionen neu bauen damit neue Controls sichtbar werden
                gcs().rebuild_projection_tables(self.view_guid)
                logger.info(f"Projektions-Tabellen neu gebaut mit allen {len(existing_controls)} Controls")
                
            except Exception as e:
                logger.warning(f"Konnte Controls nicht speichern: {e}")
                import traceback
                logger.error(traceback.format_exc())
        elif found_new_controls and not self.first_call:
            logger.info(f"Neue Controls erkannt aber NICHT gespeichert (Refresh-Modus, first_call=False)")
        else:
            logger.info(f"Keine neuen Controls - keine Persistierung erforderlich")
#            return [], []
    

