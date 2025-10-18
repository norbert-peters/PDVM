
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

import pdvm_central_systemsteuerung_global
from pdvm_projection_manager import get_projection_manager
from pdvm_matrix_pipeline import get_matrix_pipeline
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung


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

        logger.info(f"🔧 NEUER LINEAR aufgebauter DatenManager gestartet (PERSISTENT)")
        logger.info(f"📋 View: {self.view_guid}, First Call: {self.first_call}")
        logger.info(f"🚀 Matrix Pipeline: {self.matrix_pipeline}")

        # Daten laden
        self._build_system()
    
    def update_call_daten(self, new_call_daten: dict):
        """Aktualisiert call_daten für bestehenden Manager (ohne Neuaufbau)."""
        self.call_daten.update(new_call_daten)
        logger.info(f"📝 Call-Daten für persistenten Manager aktualisiert: {self.view_guid}")
    
    def create_controlled_widget(self, parent=None, reload_callback=None):
        """
        KORREKTE ARCHITEKTUR: DatenManager erstellt bewährtes Widget mit allen Features.
        Verwendet das bewährte, funktionierende Widget - nur Architektur umgekehrt.
        """
        try:
            # Das BEWÄHRTE Widget mit allen Features verwenden
            from pdvm_view_widget_corrected_architecture import PdvmViewWidget
            
            # Widget erstellen und persistenten DatenManager übergeben
            widget = PdvmViewWidget(
                call_daten=self.call_daten,
                persistent_view_manager=self,  # Persistenter Manager wird übergeben
                parent=parent,
                reload_callback=reload_callback
            )
            
            # Widget-Referenz für refresh_controlled_widget
            self.widget = widget
            
            logger.info(f"✅ Bewährtes Widget mit allen Features erfolgreich erstellt")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des bewährten Widgets: {e}")
            traceback.print_exc()
            raise
    
    def refresh_controlled_widget(self):
        """
        KORREKTE ARCHITEKTUR: Refresht das bewährte Widget über die persistenten Daten.
        Verwendet die bewährten Refresh-Methoden.
        """
        if self.widget is None:
            logger.warning("⚠️ Kein Widget zum Refreshen vorhanden")
            return None
            
        try:
            logger.info("🔄 Refreshe bewährtes Widget über persistenten DatenManager")
            
            # Persistente Daten aktualisieren (wie original)
            if hasattr(self, 'refresh_controls_and_projection'):
                self.refresh_controls_and_projection()
            
            # Widget über bewährte _load_table_data Methode aktualisieren
            if hasattr(self.widget, '_load_table_data'):
                self.widget._load_table_data()
                
            # Header aktualisieren
            if hasattr(self.widget, 'update_header_text'):
                self.widget.update_header_text()
            
            logger.info(f"✅ Widget erfolgreich über persistenten DatenManager refresht")
            return self.widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Widget-Refresh: {e}")
            traceback.print_exc()
            return None
    
    def _populate_widget(self, widget):
        """Füllt das Widget mit den aktuellen Daten vom persistenten DatenManager."""
        try:
            if not widget:
                return
                
            # Widget-interne _load_table_data Methode aufrufen wenn vorhanden
            if hasattr(widget, '_load_table_data'):
                widget._load_table_data()
            
            # Header aktualisieren wenn vorhanden  
            if hasattr(widget, 'update_header_text'):
                widget.update_header_text()
                
            logger.info("✅ Widget mit persistenten DatenManager-Daten befüllt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen des Widgets: {e}")
            traceback.print_exc()

    def _build_system(self):
        """
        SCHRITT-FÜR-SCHRITT AUFBAU:
        1. ViewDaten laden
        2. Controls aufbauen
        3. Daten laden (nur bei first_call oder Stichtagswechsel)
        """
        try:
            logger.info("🔧 SCHRITT 1: ViewDaten laden")
            view_felder = self._load_view_felder()

            logger.info("🔧 SCHRITT 2: Column Controls aufbauen")
            if self.first_call:
                # Neuaufruf: Controls neu aufbauen
                self.column_control = self._build_column_controls(view_felder)
            else:
                # Refresh: Controls aus Systemsteuerung laden
                logger.info("📊 Refresh-Modus: Lade Controls aus Systemsteuerung")
                self.column_control = self._build_column_controls_from_systemsteuerung()

            logger.info("🔧 SCHRITT 3: Basis-Spalten ableiten")
            if self.first_call:
                # Neuaufruf: Basis-Spalten neu ableiten
                self.basis_columns = self._get_columns_from_controls()
            else:
                # Refresh: Basis-Spalten immer neu ableiten (weil Controls geladen wurden)
                logger.info("📊 Refresh-Modus: Basis-Spalten aus geladenen Controls ableiten")
                self.basis_columns = self._get_columns_from_controls()

            logger.info("🔧 SCHRITT 4: Daten laden (nur falls first_call)")
            if self.first_call:
                records_loaded = self._load_records_data(limit=100)
                logger.info(f"✅ {records_loaded} Datensätze geladen")
                
                # === NEU: Pipeline aufbauen nach Daten-Laden ===
                logger.info("🔧 SCHRITT 5: Matrix Pipeline aufbauen")
                self._build_matrix_pipeline()
            else:
                logger.info("📊 SKIP: Datenladen übersprungen (first_call=False)")

        except Exception as e:
            logger.error(f"❌ Fehler beim System-Aufbau: {e}")
            traceback.print_exc()
            raise
        finally:
            # Nach dem ersten Aufruf ist first_call immer False
            if self.first_call:
                self.first_call = False
                logger.info("🔧 first_call auf False gesetzt nach erstem System-Aufbau")

    def refresh_controls_and_projection(self):
        """
        Aktualisiert nur die Parameter in den bestehenden Controls (show, order) aus der Systemsteuerung
        und baut dann die Projektion neu auf. Die Controls selbst bleiben erhalten - nur die Projektions-Parameter ändern sich.
        """
        try:
            logger.info("🔄 Control-Parameter aus Systemsteuerung laden und Projektion neu aufbauen")
            
            # Lade die aktuellen ColumnControl-Parameter aus der Systemsteuerung
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            column_attributes = cc_data.get("wert", {}) if cc_data and "wert" in cc_data else {}
            
            if column_attributes and hasattr(self, 'basis_columns'):
                logger.info(f"📥 Aktualisiere Parameter für {len(self.basis_columns)} bestehende Controls")
                
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
                
                logger.info("✅ Control-Parameter aktualisiert - Projektion wird neu aufgebaut")
                logger.info(f"   Aktuelle Modus-Einstellung: ExpertMode={gcs.global_expert_mode}")
            else:
                logger.warning("⚠️ Keine ColumnControls in Systemsteuerung gefunden oder keine basis_columns vorhanden")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh der Control-Parameter: {e}")
            traceback.print_exc()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh der Controls/Projektion: {e}")
            traceback.print_exc()

    def _build_matrix_pipeline(self):
        """
        Baut die vollständige Matrix-Pipeline auf:
        BasisMatrix → FilterMatrix → SortMatrix → Projektion
        
        Wird aufgerufen nach _load_records_data()
        """
        try:
            logger.info("🚀 === MATRIX PIPELINE AUFBAU START ===")
            
            # SCHRITT 1: Alle Spaltennamen sammeln (inkl. _abdatum, _formatiertes_abdatum)
            all_columns = set()
            if self.column_control and hasattr(self.column_control, 'column_data'):
                for col_name in self.column_control.column_data.keys():
                    all_columns.add(col_name)
            all_columns_list = sorted(list(all_columns))
            logger.info(f"📋 {len(all_columns_list)} Spalten gefunden (inkl. _abdatum/_formatiertes_abdatum)")
            
            # SCHRITT 2: BasisMatrix aufbauen
            logger.info("🔨 SCHRITT 1: BasisMatrix aufbauen")
            self.matrix_pipeline.build_basis_matrix(self.column_control, all_columns_list)
            
            # SCHRITT 3: FilterMatrix aufbauen (aktuell kein Filter)
            logger.info("🔨 SCHRITT 2: FilterMatrix aufbauen")
            self.matrix_pipeline.apply_filter(filter_func=None)  # TODO: Filter-Funktion integrieren
            
            # SCHRITT 4: SortMatrix aufbauen (aktuell keine Sortierung)
            logger.info("🔨 SCHRITT 3: SortMatrix aufbauen")
            self.matrix_pipeline.apply_sort(sort_column=None, reverse=False)  # TODO: Sort-Parameter integrieren
            
            # SCHRITT 5: Projektion aufbauen (nur sichtbare _show Spalten)
            logger.info("🔨 SCHRITT 4: Projektion aufbauen")
            visible_columns = [col['name'] for col in self.basis_columns if col.get('show', False)]
            logger.info(f"👁️ Sichtbare Spalten: {len(visible_columns)}")
            self.matrix_pipeline.project(visible_columns)
            
            # Pipeline-Status loggen
            self.matrix_pipeline.log_pipeline_status()
            
            logger.info("✅ === MATRIX PIPELINE AUFBAU ABGESCHLOSSEN ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Pipeline-Aufbau: {e}")
            import traceback
            traceback.print_exc()
    
    def rebuild_pipeline_with_stichtag(self):
        """
        Baut Pipeline nach Stichtag-Wechsel neu auf:
        1. Cached Records mit neuem Stichtag in BasisMatrix befüllen
        2. Pipeline komplett durchlaufen
        
        WICHTIG: Wird von Refresh-Button aufgerufen
        """
        try:
            logger.info("🔄 === REBUILD PIPELINE MIT NEUEM STICHTAG ===")
            logger.info(f"📅 Aktueller Stichtag: {gcs.stichtag}")
            
            # SCHRITT 1: BasisMatrix mit cached records neu befüllen
            if hasattr(self, '_cached_all_records') and self._cached_all_records:
                logger.info("♻️ Verwende gecachte Records für Stichtag-Wechsel")
                
                # Daten NEU verarbeiten mit neuem Stichtag
                logger.info("🔄 Verarbeite Daten mit neuem Stichtag...")
                self._reprocess_cached_records_with_new_stichtag()
                
                # BasisMatrix neu aufbauen
                all_columns = list(self.column_control.column_data.keys())
                self.matrix_pipeline.build_basis_matrix(self.column_control, all_columns)
                
                # Pipeline durchlaufen
                self.matrix_pipeline.rebuild_from_basis()
                
                logger.info("✅ Pipeline mit neuem Stichtag komplett durchlaufen")
                return True
            else:
                logger.warning("⚠️ Keine gecachten Records vorhanden - lade Daten neu")
                self._load_records_data(limit=100)
                self._build_matrix_pipeline()
                return True
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Pipeline-Rebuild: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_search_filter(self, search_string: str, visible_columns: list):
        """
        EINFACHE SUCHE: Wendet Filter auf BasisMatrix an
        
        Args:
            search_string: Suchtext (aus Dialog)
            visible_columns: Sichtbare Spalten für Suche
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"🔍 Matrix Manager: Wende Filter an: '{search_string}'")
            
            if not search_string:
                # Leere Suche = Pipeline ohne Filter
                logger.info("🔄 Leere Suche - Pipeline ohne Filter durchlaufen")
                self.matrix_pipeline.rebuild_from_basis()
                return True
            
            # Filter-Funktion erstellen
            search_lower = search_string.lower()
            
            def search_filter(row_data):
                """Sucht in sichtbaren Spalten mit 'enthält'"""
                for col_key in visible_columns:
                    if col_key in row_data:
                        value_str = str(row_data[col_key]).lower() if row_data[col_key] is not None else ''
                        if search_lower in value_str:
                            return True
                return False
            
            # Filter anwenden → FilterMatrix
            self.matrix_pipeline.apply_filter(search_filter)
            
            # Rest der Pipeline durchlaufen (Sort + Projection)
            # WICHTIG: rebuild_from_basis würde BasisMatrix nehmen!
            # Wir müssen manuell Sort und Projection machen:
            self.matrix_pipeline.apply_sort(
                self.matrix_pipeline.sort_column,
                self.matrix_pipeline.sort_reverse
            )
            self.matrix_pipeline.project(self.matrix_pipeline.visible_columns)
            
            logger.info(f"✅ Filter angewendet: {self.matrix_pipeline.filter_matrix.get_row_count()} Zeilen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des Filters: {e}")
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
            
            # temp_instance und temp_dt initialisieren
            temp_instance = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.view_table,
                guid=None
            )
            temp_dt = gcs.temp_dt_inst
            
            logger.info(f"🔄 Verarbeite {len(self._cached_all_records)} gecachte Records mit neuem Stichtag")
            
            for record_info in self._cached_all_records:
                data_guid = record_info["uid"]
                data_dict = record_info["daten_dict"]
                
                # set_data befüllt temp_instance
                temp_instance.set_data(data_dict, data_guid)
                
                # Row-Record neu erstellen - ORIGINAL SUFFIX!
                row_record = {'uid_original': data_guid}
                row_record['uid_original_abdatum'] = None
                row_record['uid_original_formatiertes_abdatum'] = None
                
                # _original Felder neu befüllen mit neuem Stichtag
                self._fill_original_columns(row_record, temp_instance, temp_dt)
                
                # _show Spalten neu befüllen
                self._fill_show_columns(row_record, temp_dt)
                
                # Column Control aktualisieren
                self.column_control.set_row_data(data_guid, row_record)
            
            logger.info("✅ Alle Records mit neuem Stichtag verarbeitet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Reprocessing: {e}")
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
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                attr_map = cc_data["wert"]
                logger.info(f"🔄 Parameter-Refresh: {len(attr_map)} gespeicherte Control-Attribute geladen")
                
                # Erstelle minimale Controls nur aus gespeicherten Daten (ohne neue hinzuzufügen)
                columns = []
                for col_name, attrs in attr_map.items():
                    col = {
                        'name': col_name,
                        'show': attrs.get('show', False),
                        'expertOrder': attrs.get('expertOrder', 0),
                        'displayOrder': attrs.get('displayOrder', 0),
                        'type': 'unknown',  # Typ ist für Refresh nicht wichtig
                        'spaltenueberschrift': col_name.replace('_', ' ').title()
                    }
                    columns.append(col)
                
                # Simuliere die Controls-Struktur für Refresh
                self.column_control = {'columns': columns}
                logger.info(f"🔄 Parameter-Refresh: {len(columns)} minimale Controls erstellt")
                
            else:
                logger.error("❌ Keine gespeicherten Control-Parameter für Refresh gefunden")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Parameter-Refresh: {e}")
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
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                attr_map = cc_data["wert"]
                logger.info(f"🔄 Refresh-Modus: {len(attr_map)} Control-Attribute aus Systemsteuerung geladen")
                
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
                        'field_config': {}  # Minimale Config für Refresh
                    }
                    columns.append(col)
                
                logger.info(f"✅ Refresh-Modus: {len(columns)} Controls aus Systemsteuerung aufgebaut")
                return {'columns': columns}
                
            else:
                logger.error("❌ Refresh-Modus: Keine ColumnControls in Systemsteuerung gefunden!")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der Controls aus Systemsteuerung: {e}")
            traceback.print_exc()
            return None

    def _guess_column_type(self, col_name):
        """Errät den Spaltentyp aus dem Namen (für Refresh-Modus)."""
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
        elif col_name.startswith('uid'):
            return 'string'
        else:
            return 'string'

    def _create_column_header(self, col_name):
        """Erstellt eine Spaltenüberschrift aus dem Control-Namen (für Refresh-Modus)."""
        if col_name == 'uid_original':
            return 'UID (orig.)'
        elif col_name == 'uid_show':
            return 'UID'
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
        logger.info(f"🔍 === MATRIX ROW {row_idx} DEBUG (3-EBENEN) ===")
        
        # GUID
        guid = row_data.get('uid_original', 'UNBEKANNT')
        logger.info(f"  👤 GUID: {guid}")
        
        # Familienname mit 3 Ebenen
        if 'familienname_original' in row_data:
            fn_wert = row_data.get('familienname_original')
            fn_abdatum = row_data.get('familienname_original_abdatum')
            fn_formatiert = row_data.get('familienname_original_formatiertes_abdatum')
            
            logger.info(f"  📋 familienname_original:")
            logger.info(f"    ├─ 🗄️ EBENE 1 (Wert):       '{fn_wert}'")
            logger.info(f"    ├─ 📅 EBENE 2 (AB-Datum):   {fn_abdatum}")
            logger.info(f"    └─ 🎨 EBENE 3 (Formatiert): '{fn_formatiert}'")
        else:
            logger.warning(f"  ⚠️ familienname_original NICHT in row_data!")
        
        # Vorname und Geburtsdatum
        for key in ['vorname_original', 'geburtsdatum_original']:
            if key in row_data:
                wert = row_data.get(key)
                abdatum = row_data.get(f"{key}_abdatum")
                formatiert = row_data.get(f"{key}_formatiertes_abdatum")
                logger.info(f"  📋 {key}: '{wert}' | abdatum={abdatum} | formatiert='{formatiert}'")
        
        # Alle Keys zeigen (erste 20)
        all_keys = list(row_data.keys())
        logger.info(f"  🗝️ Alle Keys ({len(all_keys)}): {', '.join(all_keys[:20])}...")

    def get_abdatum_matrix(self, show_only=True):
        """
        Gibt die Abdatum-Matrix für die aktuelle Projektion zurück
        
        VERWENDET EBENE 3 (__formatiert Suffix) für UI-Tooltips
        
        Args:
            show_only: Nur sichtbare Spalten (True) oder alle (False)
        
        Returns:
            List[List[str]]: 2D-Matrix mit formatierten Abdatum-Werten
        """
        logger.info("🔍 === get_abdatum_matrix() START ===")
        
        if not self.column_control:
            logger.error("❌ column_control ist None!")
            return None
            
        # Projektion ermitteln
        if show_only:
            columns = sorted([col for col in self.basis_columns if col.get('show', False)], key=lambda c: c.get('displayOrder', 999))
        else:
            columns = sorted(self.basis_columns, key=lambda c: c.get('expertOrder', 999))
            
        col_names = [col['name'] for col in columns]
        logger.info(f"📊 Spaltennamen ({len(col_names)}): {col_names[:5]}...")
        
        abdatum_matrix = []
        
        # Über alle GUIDs iterieren
        guids = list(self.column_control.row_guids)
        logger.info(f"👤 GUIDs ({len(guids)}): {guids[:3]}...")
        
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
                
                # DEBUG: Log für familienname
                if row_idx == 0 and col_name == 'familienname_original':
                    logger.info(f"  🔍 familienname_original_formatiertes_abdatum = '{formatiert}'")
            
            abdatum_matrix.append(abdatum_row)
            
        logger.info(f"✅ Abdatum-Matrix erstellt: {len(abdatum_matrix)} Zeilen, {len(col_names)} Spalten")
        
        # DEBUG: Zeige erste Zeile
        if abdatum_matrix and abdatum_matrix[0]:
            logger.info(f"🔍 Erste Zeile Abdatum-Matrix (erste 5): {abdatum_matrix[0][:5]}")
        
        return abdatum_matrix
    
    def _load_or_init_column_controls(self, view_felder):
        """
        LINEARES VORGEHEN für ColumnControls (vereinfacht):
        
        1. Baue IMMER Standard-Controls mit Standard-Sortierung auf (0, 1, 2, ...)
        2. Synchronisiere Attribute aus Systemsteuerung in bestehende Controls
        3. Fehlende Controls (nicht in Systemsteuerung) bekommen Order +1000 und show=true (_show)
        4. Bei Order >1000 gefunden: Alle neu nummerieren (0, 1, 2, ...) und in Systemsteuerung speichern
        
        Control-Namen:
        - _original-Spalten als feldname_original, uid_original (System).
        - _show-Spalten als feldname_show, Dummy als 'dummy'.
        - Spaltenüberschrift: _original → name (aus Viewdaten) + ' (orig.)', _show → name (aus Viewdaten), Dummy → ''.
        """
        # SCHRITT 1: Lade gespeicherte Attribute aus Systemsteuerung
        try:
            cc_data = gcs.get_value(gruppe=self.view_guid, feld="ColumnControls", ab_zeit=1001.0)
            if cc_data and "wert" in cc_data and isinstance(cc_data["wert"], dict):
                logger.info(f"✅ ColumnControl-Attribute aus Systemsteuerung geladen für {self.view_guid}")
                attr_map = cc_data["wert"]
                logger.info(f"🔍 Geladene Attribute: {len(attr_map)} Controls")
            else:
                logger.info(f"ℹ️ Keine ColumnControl-Attribute gefunden")
                attr_map = {}
        except Exception as e:
            logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht aus Systemsteuerung laden: {e}")
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

            # Zusatzfelder für date
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

        # _show Controls für alle _original (außer dummy)
        for col in columns[:]:
            if col['name'].endswith('_original'):
                show_name = col['name'].replace('_original', '_show')
                
                # Überschrift: Gleich wie Original-Spalte, aber ohne "(orig.)"
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

        # 🆕 row_type Control - Enthält Zeilen-Metadaten (data/group_header/group_footer)
        row_type_col = {
            'name': 'row_type',
            'type': 'dict',  # Dict-Typ für flexible Metadaten
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

        logger.info(f"🔧 {len(columns)} Standard-Controls mit Standard-Sortierung erstellt (inkl. dummy + row_type)")

        # SCHRITT 3: Synchronisation - Attribute aus Systemsteuerung in bestehende Controls übernehmen
        found_new_controls = False
        
        for col in columns:
            col_name = col['name']
            if col_name in attr_map:
                # Bestehende Einstellungen übernehmen
                saved_attrs = attr_map[col_name]
                col['show'] = saved_attrs.get('show', col['show'])
                col['expertOrder'] = saved_attrs.get('expertOrder', col['expertOrder'])
                col['displayOrder'] = saved_attrs.get('displayOrder', col['displayOrder'])
            else:
                # NEUES Control nicht in Systemsteuerung gefunden
                logger.debug(f"🆕 Neues Control gefunden: {col_name}")
                col['expertOrder'] += 1000  # Markierung als "neu"
                col['displayOrder'] += 1000  # Markierung als "neu"
                # _show Controls: show=True, andere: show bleibt
                if col_name.endswith('_show'):
                    col['show'] = True
                found_new_controls = True

        logger.info(f"✅ Synchronisation abgeschlossen - {len(columns)} Controls, neue gefunden: {found_new_controls}")

        # SCHRITT 4: Bei neuen Controls (Order >1000): Alle neu nummerieren
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

        # SCHRITT 5: Persistierung nur bei neuen Controls UND first_call
        # Bei Refresh (first_call=False) niemals speichern!
        if found_new_controls and self.first_call:
            persist_map = {col['name']: {
                'show': col['show'],
                'expertOrder': col['expertOrder'],
                'displayOrder': col['displayOrder']
            } for col in columns}
            
            try:
                gcs.set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
                gcs.save_values()
                logger.info(f"💾 Neue Controls in Systemsteuerung gespeichert für {self.view_guid} (first_call=True)")
            except Exception as e:
                logger.warning(f"⚠️ Konnte ColumnControl-Attribute nicht speichern: {e}")
        elif found_new_controls and not self.first_call:
            logger.info(f"🔄 Neue Controls erkannt aber NICHT gespeichert (Refresh-Modus, first_call=False)")
        else:
            logger.info(f"ℹ️ Keine neuen Controls - keine Persistierung erforderlich")

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
            
            # displayOrder-Vergabe nur für neu erstellte Controls ohne displayOrder
            show_counter = 0
            for col in columns:
                if 'displayOrder' not in col or col.get('displayOrder', None) is None:
                    if col.get('show', False):
                        col['displayOrder'] = show_counter
                        show_counter += 1
                    else:
                        col['displayOrder'] = col.get('expertOrder', 0) + 1000
                elif col.get('show', False):
                    show_counter += 1

            # ColumnControl-Objekt für interne Nutzung
            column_control = ColumnControl()
            for col in columns:
                # WICHTIG: Alle relevanten Felder übertragen, aber Namenskonflikte vermeiden
                col_kwargs = {
                    'show': col.get('show', True),
                    'expertOrder': col.get('expertOrder', 999),
                    'displayOrder': col.get('displayOrder', 999),
                    'expert': col.get('expert', False),
                    'field_config': col.get('field_config', {}),
                    'spaltenueberschrift': col.get('spaltenueberschrift', col['name']),
                    'gruppe': col.get('gruppe'),
                    'feld': col.get('feld'),
                    'anzeige': col.get('spaltenueberschrift', col['name'])  # Für ColumnControl
                }
                
                column_control.add_column(
                    col['name'],
                    col.get('type', 'string'),
                    col.get('expertOrder', 999),  # Verwende expertOrder als order
                    **col_kwargs
                )
                
            logger.info(f"✅ {len(columns)} Column Controls aufgebaut")
            return column_control
        except Exception as e:
            logger.error(f"❌ Fehler beim Column Control Aufbau: {e}")
            traceback.print_exc()
            raise
    
    def _get_columns_from_controls(self):
        """SCHRITT 3: Basis-Spalten aus Controls ableiten mit korrekter Struktur für Dialog"""
        try:
            columns = []
            for col_dict in self.column_control.columns:
                # WICHTIG: Alle Felder korrekt mappen und sicherstellen dass sie existieren
                simple_col = {
                    'name': col_dict['name'],
                    'label': col_dict.get('anzeige', col_dict['name']),
                    'type': col_dict.get('type', 'string'),
                    'show': col_dict.get('show', True),
                    'expertOrder': col_dict.get('expertOrder', col_dict.get('order', 999)),  
                    'displayOrder': col_dict.get('displayOrder', col_dict.get('order', 999)),  
                    'expert': col_dict.get('expert', False),  
                    'field_config': col_dict.get('field_config', {}),
                    'spaltenueberschrift': col_dict.get('spaltenueberschrift', col_dict.get('anzeige', col_dict['name'])),
                    'gruppe': col_dict.get('gruppe'),
                    'feld': col_dict.get('feld')
                }
                
                # Sicherheitscheck: Alle Order-Felder müssen valide Zahlen sein
                if not isinstance(simple_col['expertOrder'], (int, float)):
                    simple_col['expertOrder'] = 999
                if not isinstance(simple_col['displayOrder'], (int, float)):
                    simple_col['displayOrder'] = simple_col['expertOrder']
                    
                columns.append(simple_col)
                
            logger.info(f"✅ {len(columns)} Basis-Spalten aufgebaut (mit korrekten Order-Feldern)")
            
            # Debug-Output
            for col in columns[:3]:  # Erste 3 Spalten zur Kontrolle
                logger.debug(f"  {col['name']}: expertOrder={col['expertOrder']}, displayOrder={col['displayOrder']}, show={col['show']}")
                
            return columns
        except Exception as e:
            logger.error(f"❌ Fehler beim Basis-Spalten-Aufbau: {e}")
            traceback.print_exc()
            return []
    
    def _load_records_data(self, limit=100):
        """
        SCHRITT 4: Daten laden - KORREKTE ORIGINAL-LOGIK
        
        1. EINMAL alle Datensätze aus DB lesen
        2. EINE temp_instance für ALLE Datensätze
        3. Pro Datensatz: set_data → get_value mit Stichtag
        4. 3-Ebenen-Struktur befüllen: wert, abdatum, formatiert
        """
        try:
            if not hasattr(self, 'view_table') or not self.view_table:
                raise ValueError("view_table nicht verfügbar")

            from pdvm_central_datenbank import PdvmCentralDatenbank

            # === SCHRITT 1: EINMAL alle Datensätze laden (außer 0000...-GUID) ===
            logger.info("📊 === SCHRITT 1: Lade ALLE Datensätze EINMAL aus DB ===")
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.view_table,
                guid=None  # Kein GUID = Lese-Modus
            )

            all_records = data_db.lesen_alle_ohne_system(limit=limit)
            logger.info(f"✅ {len(all_records)} Datensätze geladen")
            
            # Cache für Stichtags-Wechsel
            self._cached_all_records = all_records

            # === SCHRITT 2: EINE temp_instance + DateTime für ALLE Datensätze ===
            logger.info("🔧 === SCHRITT 2: Initialisiere EINE temp_instance für ALLE Datensätze ===")
            temp_instance = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=self.view_table,
                guid=None  # Ohne GUID = für set_data nutzbar
            )

            # Datetime-Formatter EINMAL initialisieren
            from pdvm_datetime import Pdvm_DateTime
            temp_dt = gcs.temp_dt_inst  # Verwende GCS temp_dt_inst
            if not temp_dt:
                temp_dt = Pdvm_DateTime("DEU")
                logger.warning("⚠️ Kein temp_dt_inst in GCS - verwende lokale Instanz")
            logger.info(f"✅ temp_instance und temp_dt initialisiert")

            # === SCHRITT 3: Pro Datensatz - set_data + get_value ===
            logger.info("🔄 === SCHRITT 3: Verarbeite Datensätze mit set_data + get_value ===")
            successful_records = 0

            for i, record_info in enumerate(all_records):
                try:
                    data_guid = record_info["uid"]
                    data_dict = record_info["daten_dict"]

                    # === KRITISCH: set_data befüllt temp_instance ===
                    temp_instance.set_data(data_dict, data_guid)

                    # Row-Record erstellen
                    row_record = {'uid_original': data_guid}
                    
                    # 🆕 row_type: Normale Daten-Zeile
                    row_record['row_type'] = {'type': 'data'}
                    
                    # === 3-EBENEN für uid_original (hat kein Abdatum) - ORIGINAL SUFFIX! ===
                    row_record['uid_original_abdatum'] = None
                    row_record['uid_original_formatiertes_abdatum'] = None

                    # === SCHRITT 3a: _original Felder befüllen mit 3-EBENEN-STRUKTUR ===
                    self._fill_original_columns(row_record, temp_instance, temp_dt)

                    # === SCHRITT 3b: _show Spalten aus _original kopieren (inkl. 3 Ebenen) ===
                    self._fill_show_columns(row_record, temp_dt)

                    # In Column Control speichern (enthält jetzt alle 3 Ebenen pro Feld)
                    self.column_control.set_row_data(data_guid, row_record)
                    successful_records += 1
                    
                    # DEBUG: Erste Row detailliert ausgeben
                    if successful_records == 1:
                        self._debug_print_matrix_row(row_record, 0)

                    if (i + 1) % 20 == 0:
                        logger.info(f"   📊 {i+1}/{len(all_records)} Datensätze verarbeitet...")

                except Exception as e:
                    logger.warning(f"⚠️ Fehler bei Datensatz {record_info.get('uid', 'unbekannt')}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue

            logger.info(f"✅ {successful_records} Datensätze erfolgreich geladen (mit 3-Ebenen-Struktur)")
            
            # DEBUG: Nochmal erste Row ausgeben nach allen Verarbeitungen
            if self.column_control.row_guids:
                first_guid = list(self.column_control.row_guids)[0]
                first_row = self.column_control.get_row_data(first_guid)
                logger.info("🔍 === FINALE MATRIX-ROW NACH ALLEN VERARBEITUNGEN ===")
                self._debug_print_matrix_row(first_row, 0)
            
            return successful_records

        except Exception as e:
            logger.error(f"❌ Fehler beim Daten-Laden: {e}")
            traceback.print_exc()
            return 0
    
    def _fill_original_columns(self, row_record: dict, temp_instance, temp_dt):
        """
        SCHRITT 3a: _original Spalten befüllen mit 3-EBENEN-STRUKTUR
        
        KORREKTE LOGIK aus pdvm_view_dialog.py:
        1. Sortiere Controls: Basis-Felder vor Zusatzfeldern
        2. Basis-Felder: get_value() → (wert, abdatum)
        3. Zusatzfelder (date_alter etc.): Berechnung aus Basis-Feld
        4. Für jeden control_key: 3 Ebenen befüllen
        """
        try:
            # === Sortiere Controls: Basis-Felder VOR Zusatzfeldern ===
            def sort_key(col):
                col_type = col.get('type', '')
                if col_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                    return 1  # Zusatzfelder später
                else:
                    return 0  # Basis-Felder zuerst
            
            # Nur _original Controls (ohne uid_original)
            original_cols = [col for col in self.basis_columns 
                           if col['name'].endswith('_original') and col['name'] != 'uid_original']
            sorted_cols = sorted(original_cols, key=sort_key)
            
            logger.debug(f"🔄 Verarbeite {len(sorted_cols)} _original Felder (sortiert)")
            
            for col in sorted_cols:
                col_name = col['name']
                col_type = col.get('type', '')
                gruppe = col.get('gruppe', 'PERSDATEN')
                feld = col.get('feld')
                
                if gruppe:
                    gruppe = str(gruppe).upper()
                if feld:
                    feld = str(feld).upper()
                
                # === SPEZIALFALL: Date-Zusatzfelder (alter, jahr, monat, tag) ===
                if col_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                    # Basis-Feld finden
                    zusatz_suffix = col_type.replace('date_', '')
                    base_field = col_name.replace('_original', '').replace(f'_{zusatz_suffix}', '')
                    base_original = f"{base_field}_original"
                    base_wert = row_record.get(base_original)
                    
                    logger.debug(f"  📅 Zusatzfeld {col_name}: Basis={base_original}, Wert={base_wert}")
                    
                    if base_wert and base_wert != 1001.0:
                        try:
                            temp_dt.PdvmDateTime = float(base_wert)
                            
                            if col_type == 'date_alter':
                                calculated_value = str(temp_dt.calc_alter(gcs.stichtag))
                            elif col_type == 'date_jahr':
                                calculated_value = str(temp_dt.Year)
                            elif col_type == 'date_monat':
                                calculated_value = str(temp_dt.Month)
                            elif col_type == 'date_tag':
                                calculated_value = str(temp_dt.Day)
                            else:
                                calculated_value = ""
                            
                            row_record[col_name] = calculated_value
                            logger.debug(f"  ✅ {col_name} = {calculated_value}")
                        except Exception as e:
                            row_record[col_name] = ""
                            logger.debug(f"  ⚠️ Berechnung fehlgeschlagen für {col_name}: {e}")
                    else:
                        row_record[col_name] = ""
                    
                    # Date-Zusatzfelder haben kein eigenes Abdatum - ORIGINAL SUFFIX!
                    row_record[f"{col_name}_abdatum"] = None
                    row_record[f"{col_name}_formatiertes_abdatum"] = None
                    continue
                
                # === NORMALFALL: Basis-Felder aus DB ===
                if feld and gruppe:
                    try:
                        # KRITISCH: get_value() gibt Tupel zurück (wert, abdatum)
                        result = temp_instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
                        
                        # Tupel auspacken
                        if isinstance(result, tuple) and len(result) >= 2:
                            wert, abdatum = result[0], result[1]
                        else:
                            wert, abdatum = result, None
                        
                        logger.debug(f"  🔍 {col_name}: wert={wert}, abdatum={abdatum}")
                        
                        # === 3-EBENEN BEFÜLLEN (ORIGINAL-SUFFIX!) ===
                        
                        # EBENE 1: Wert
                        row_record[col_name] = wert
                        
                        # EBENE 2: AB-Datum (roh) - ORIGINAL SUFFIX!
                        row_record[f"{col_name}_abdatum"] = abdatum
                        
                        # EBENE 3: Formatiertes AB-Datum - ORIGINAL SUFFIX!
                        if abdatum:
                            temp_dt.PdvmDateTime = float(abdatum)
                            formatiert = temp_dt.FormTimeStamp
                            row_record[f"{col_name}_formatiertes_abdatum"] = formatiert
                            logger.debug(f"  🎨 {col_name}_formatiertes_abdatum = {formatiert}")
                        else:
                            row_record[f"{col_name}_formatiertes_abdatum"] = None
                    
                    except Exception as e:
                        logger.debug(f"  ⚠️ get_value Fehler für {col_name}: {e}")
                        # Fehlerfall: Alle 3 Ebenen leer - ORIGINAL SUFFIX!
                        row_record[col_name] = ""
                        row_record[f"{col_name}_abdatum"] = None
                        row_record[f"{col_name}_formatiertes_abdatum"] = None
                else:
                    # Kein Feld/Gruppe: Alle 3 Ebenen leer - ORIGINAL SUFFIX!
                    row_record[col_name] = ""
                    row_record[f"{col_name}_abdatum"] = None
                    row_record[f"{col_name}_formatiertes_abdatum"] = None
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der _original Spalten: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_abdatum(self, abdatum_value, temp_dt):
        """
        Formatiert ein Abdatum länderspezifisch via pdvm_DateTime
        
        Args:
            abdatum_value: Rohdatum (z.B. 2024310.12500)
            temp_dt: Pdvm_DateTime Instanz
        
        Returns:
            str: Formatiertes Datum (z.B. "05.11.2024 03:00:00")
            None: Wenn kein Abdatum vorhanden
        """
        if abdatum_value is None:
            return None
        
        # SPEZIALFALL: Default-Wert 1001.0 (01.01.0001)
        if float(abdatum_value) == 1001.0:
            return "01.01.0001 (Default)"
        
        try:
            temp_dt.PdvmDateTime = float(abdatum_value)
            formatted = temp_dt.FormTimeStamp
            return formatted
        except Exception as e:
            logger.debug(f"❌ Formatierungs-Fehler für {abdatum_value}: {e}")
            return f"{abdatum_value} (Fehler)"
    
    def _berechne_datum_zusatz(self, original_datum: float, zusatz_typ: str, temp_dt):
        """Berechnet Datum-Zusatzwerte"""
        try:
            temp_dt.PdvmDateTime = original_datum
            
            if zusatz_typ == "alter":
                # PRÄZISE TAGESEXAKTE ALTERSBERECHNUNG
                return temp_dt.calc_alter(gcs.stichtag)
            elif zusatz_typ == "jahr":
                return temp_dt.Year
            elif zusatz_typ == "monat":
                return temp_dt.Month
            elif zusatz_typ == "tag":
                return temp_dt.Day
            else:
                return ""
        except Exception as e:
            logger.debug(f"❌ Datum-Zusatz-Berechnung Fehler ({zusatz_typ}): {e}")
            return ""
    
    def _berechne_alter(self, stichtag, datum):
        stdiff = int(stichtag) - int(datum)
        strest = stdiff % 1000
        return int((stdiff - strest) / 1000)

    def _fill_show_columns(self, row_record: dict, abdatum_row: dict = None):
        """
        SCHRITT 5: _show Spalten befüllen mit 3-EBENEN-STRUKTUR
        
        Kopiert ALLE 3 Ebenen von _original zu _show:
        - {col_name}              → EBENE 1: Wert
        - {col_name}_abdatum      → EBENE 2: AB-Datum (roh)
        - {col_name}_formatiertes_abdatum  → EBENE 3: Formatiertes AB-Datum
        """
        try:
            # System uid_show
            if 'uid_original' in row_record:
                guid = row_record['uid_original']
                row_record['uid_show'] = guid[:8] + "..." if guid else ""
                
                # === 3-EBENEN für uid_show (kopiert von uid_original) ===
                row_record['uid_show_abdatum'] = row_record.get('uid_original_abdatum')
                row_record['uid_show_formatiertes_abdatum'] = row_record.get('uid_original_formatiertes_abdatum')
            
            # Alle anderen _show Spalten
            for col in self.basis_columns:
                col_name = col['name']
                
                if not col_name.endswith('_show') or col_name == 'uid_show':
                    continue
                
                # Entsprechende _original Spalte finden
                original_col_name = col_name.replace('_show', '_original')
                
                if original_col_name in row_record:
                    # === 3-EBENEN KOPIEREN (SUFFIX-PATTERN) ===
                    
                    # EBENE 1: Wert
                    row_record[col_name] = row_record[original_col_name]
                    
                    # EBENE 2: AB-Datum (roh)
                    row_record[f"{col_name}_abdatum"] = row_record.get(f"{original_col_name}_abdatum")
                    
                    # EBENE 3: Formatiertes AB-Datum
                    row_record[f"{col_name}_formatiertes_abdatum"] = row_record.get(f"{original_col_name}_formatiertes_abdatum")
                    
                    logger.debug(f"✅ {col_name} kopiert von {original_col_name} (3 Ebenen)")
                    
                    # Bei normalen Feldern: Historische Dictionaries zu lesbaren Werten (LEGACY - sollte nicht mehr vorkommen)
                    original_wert = row_record[col_name]
                    col_type = col.get('type', '')
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
        Verwendet die ZENTRALE PROJEKTION - dieselbe wie der Dialog
        """
        try:
            if not self.column_control:
                return {'headers': [], 'rows': []}

            # LINEARER PROJECTION MANAGER: Einfache Tabellen-Projektion
            if self.view_guid:
                projection_manager = get_projection_manager(self.view_guid, gcs)
                table_projection = projection_manager.get_table_projection()
                
                if table_projection and self.basis_columns:
                    # Basis-Columns nach Projektion filtern und sortieren
                    basis_dict = {col['name']: col for col in self.basis_columns}
                    columns = []
                    for col_name in table_projection:
                        if col_name in basis_dict:
                            columns.append(basis_dict[col_name])
                    
                    display_columns = [col['name'] for col in columns]
                    display_headers = [col.get('spaltenueberschrift', col['name']) for col in columns]
                else:
                    logger.warning(f"⚠️ Keine Table-Projektion verfügbar für View {self.view_guid}")
                    return {'headers': [], 'rows': []}
            else:
                logger.warning("⚠️ Keine View-GUID verfügbar für Projektion")
                return {'headers': [], 'rows': []}

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
                display_row = [row_data.get(col, "") for col in display_columns]
                display_data.append(display_row)

            # Entferne leere Zeilen aus Controls
            for guid in guids_to_remove:
                if guid in self.column_control.row_guids:
                    self.column_control.row_guids.remove(guid)
                for col_data in self.column_control.column_data.values():
                    if guid in col_data:
                        del col_data[guid]

            # NEUE ARCHITEKTUR: Rückgabe als Dict für Widget-Kompatibilität
            # ✅ WICHTIG: Abdatum-Matrix für Tooltips mitliefern (3. Dimension)
            result_data = {
                'headers': display_headers,  # Schöne Namen verwenden
                'rows': display_data
            }
            
            # Abdatum-Matrix hinzufügen, falls vorhanden
            try:
                abdatum_matrix = self.get_abdatum_matrix(show_only=True)
                if abdatum_matrix:
                    result_data['abdatum_matrix'] = abdatum_matrix
                    logger.info(f"✅ Abdatum-Matrix für Tooltips hinzugefügt: {len(abdatum_matrix)} Zeilen")
                else:
                    logger.info("ℹ️ Keine Abdatum-Matrix verfügbar")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Laden der Abdatum-Matrix: {e}")
                result_data['abdatum_matrix'] = None
            
            return result_data
            
        except Exception as e:
            logger.error(f"❌ Fehler in get_table_data_for_display: {e}")
            import traceback
            traceback.print_exc()
            return {'headers': [], 'rows': []}

    def save_column_settings(self, updated_columns):
        """
        NEUE ARCHITEKTUR: Speichert Column Settings vom Dialog.
        Wird vom Widget aufgerufen wenn der ColumnSettingsDialog Änderungen hat.
        DatenManager bleibt persistent und behält alle Einstellungen!
        """
        try:
            logger.info(f"💾 Speichere Column Settings in persistentem DatenManager")
            
            # Aktualisiere die basis_columns mit den neuen Einstellungen
            if updated_columns and hasattr(self, 'basis_columns'):
                self.basis_columns = updated_columns
                logger.info(f"✅ {len(updated_columns)} Column Controls in persistentem DatenManager aktualisiert")
            
            # Speichere mit der bestehenden save_column_configuration Methode
            self.save_column_configuration(working_columns=updated_columns)
            
            logger.info(f"✅ Column Settings erfolgreich in persistentem DatenManager gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Column Settings im persistenten DatenManager: {e}")
            traceback.print_exc()

    def save_column_configuration(self, working_columns=None, mode=None):
        """
        Speichert Spalten-Konfiguration in der Systemsteuerung
        
        Args:
            working_columns: Geänderte Spalten-Konfiguration (Dialog-Format)
            mode: Aktueller Modus (wird ignoriert - linear)
            
        Returns:
            bool: True wenn erfolgreich gespeichert
        """
        try:
            logger.info(f"💾 save_column_configuration aufgerufen")
            
            # Falls working_columns übergeben wurde, diese in basis_columns übernehmen
            if working_columns:
                logger.info(f"💾 Übernehme {len(working_columns)} geänderte Spalten")
                
                # Dialog gibt bereits das richtige Format zurück: show, expertOrder, displayOrder
                # Aber sicherheitshalber prüfen wir das Format
                for working_col in working_columns:
                    col_name = working_col.get('name')
                    if not col_name:
                        continue
                    
                    # Entsprechende Basis-Spalte finden und aktualisieren
                    for basis_col in self.basis_columns:
                        if basis_col['name'] == col_name:
                            # Direkte Übernahme aus Dialog (bereits im richtigen Format)
                            basis_col['show'] = working_col.get('show', basis_col.get('show', False))
                            basis_col['expertOrder'] = working_col.get('expertOrder', basis_col.get('expertOrder', 999))
                            basis_col['displayOrder'] = working_col.get('displayOrder', basis_col.get('displayOrder', 999))
                            
                            # Fallback für alte Dialog-Formate (falls vorhanden)
                            if 'visible' in working_col:
                                basis_col['show'] = working_col['visible']
                            if 'order' in working_col:
                                basis_col['displayOrder'] = working_col['order']
                            if 'expert_order' in working_col:
                                basis_col['expertOrder'] = working_col['expert_order']
                            break
            
            # Persistiere alle Spalten-Attribute in der Systemsteuerung
            persist_map = {col['name']: {
                'show': col['show'],
                'expertOrder': col['expertOrder'], 
                'displayOrder': col['displayOrder']
            } for col in self.basis_columns}
            
            gcs.set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
            gcs.save_values()
            
            logger.info(f"✅ ColumnControl-Attribute erfolgreich in Systemsteuerung gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Spalten-Konfiguration: {e}")
            return False

#        except Exception as e:
#            logger.error(f"❌ Fehler bei get_table_data_for_display: {e}")
#            return [], []
    
