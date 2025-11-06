"""
PdvmViewDialog - SAUBERE LINEARE ARCHITEKTUR

Architektur-Prinzipien:
1. GCS über Property, nicht in __init__
2. Keine user_guid - alles über GCS
3. PdvmCentralDatenbank mit korrekten Parametern oder Fehler
4. ViewDaten komplett übernehmen, nicht einzeln kopieren
5. Kein Fallback für Dummy - Fehler wenn nicht in ViewDaten
6. Keine Duplikate - eine Methode pro Funktion
7. Linear: ViewDaten → Original Controls → Show Controls → Dummy → GCS speichern
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                            QMenu, QAction, QMessageBox, QToolButton, QWidget,
                            QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox,
                            QGroupBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

# GLOBALE IMPORTS: Konsistente GCS-Verwendung
from global_gcs import gcs
from pdvm_central_systemsteuerung import get_gcs

import logging
import time
import json
import traceback
import re

logger = logging.getLogger(__name__)

# LINEARES FILTER-SYSTEM IMPORT
try:
    from linear_filter_execution_manager import get_linear_filter_manager
    LINEAR_FILTER_AVAILABLE = True
    logger.info("✅ Lineares Filter-System verfügbar")
except ImportError as e:
    LINEAR_FILTER_AVAILABLE = False
    logger.warning(f"⚠️ Lineares Filter-System nicht verfügbar: {e}")

logger = logging.getLogger(__name__)

def get_gcs_linear():
    """LINEARE GCS-Hilfsfunktion - konsistente Verwendung"""
    try:
        # Versuche zuerst globale GCS
        if gcs and gcs.is_initialized:
            return gcs
        # Fallback auf get_gcs Funktion
        return get_gcs()
    except Exception as e:
        logger.warning(f"⚠️ GCS nicht verfügbar: {e}")
        return None

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_spalten_parameter_dialog import PdvmSpaltenParameterDialog
from pdvm_spalten_konfig_dialog import PdvmSpaltenKonfigDialog
from pdvm_datetime import Pdvm_DateTime


class PdvmViewDialog:
    """
    SAUBERER Autonomer View-Dialog mit integriertem Datenmanagement
    
    LINEARE ARCHITEKTUR:
    1. Validation der call_daten
    2. ViewDaten laden mit korrekter PdvmCentralDatenbank
    3. Controls linear generieren: ViewDaten → _original → _show → dummy
    4. Controls in GCS speichern
    5. Daten laden und Matrix erstellen
    6. UI-Display erstellen
    """
    
    def __init__(self, call_daten, parent=None, view_manager=None):
        """
        Initialisierung des autonomen View-Dialogs
        
        Args:
            call_daten: Enthält view_guid, title, first_call, reset
            parent: Parent-Widget
            view_manager: Optional View-Manager für synchronisierte Projektion
        """
        self.call_daten = call_daten
        self.parent = parent
        self.view_manager = view_manager  # Optional: View-Manager für Synchronisation
        
        # Fallback: Versuche View-Manager aus Parent zu bekommen
        if self.view_manager is None and hasattr(parent, 'view_manager'):
            self.view_manager = parent.view_manager
            logger.info("✅ View-Manager aus Parent übernommen")
            
        # Wenn View-Manager verfügbar ist, aktualisiere Filter-Panel
        if hasattr(self, 'display') and self.display and hasattr(self.display, 'filter_panel') and self.display.filter_panel:
            self.display.filter_panel.refresh_column_search_fields()
            logger.info("✅ Filter-Panel nach View-Manager Zuweisung aktualisiert")
        
        # 🔍 1. TITEL-VALIDATION: Prüfung auf erforderliche Daten
        self.view_guid = call_daten.get("view_guid")
        self.title = call_daten.get("title")
        self.first_call = call_daten.get("first_call", False)
        self.reset = call_daten.get("reset", False)  # Reset-Flag
        
        # Fehlerbehandlung für fehlende erforderliche Daten
        error_messages = []
        if not self.view_guid:
            error_messages.append("❌ Keine view_guid in call_daten gefunden")
        if not self.title:
            error_messages.append("❌ Kein Titel in call_daten gefunden")
            
        if error_messages:
            error_text = "\n".join(error_messages)
            logger.error(f"Validation Error: {error_text}")
            QMessageBox.critical(None, "Fehlende Daten", 
                               f"Die Ausgabe kann nicht erfolgen:\n\n{error_text}")
            raise ValueError(error_text)
        
        logger.info(f"🔹 PdvmViewDialog initialisiert - View: {self.view_guid}, First Call: {self.first_call}")
        
        # Daten-Container
        self.view_config = None
        self.controls_config = None
        self.all_data_records = []
        self.display_matrix = []
        
        # UI-Container
        self.display = None
        
        # Initialisierung starten
        self._initialize_dialog()
    
    
    def _initialize_dialog(self):
        """LINEARE Initialisierung"""
        logger.info("🔹 Starte LINEARE Dialog-Initialisierung...")

        # 1. ViewDaten laden
        self._load_viewdata()

        # 2. Controls linear generieren und speichern
        self._generate_and_save_controls()

        # 3. PROJEKTIONEN INITIALISIEREN
        self._initialize_projections()

        # 4. Daten laden
        self._load_data()

        # 5. Matrix erstellen
        self._build_matrix()

        # 6. UI erstellen
        self._create_ui()

        logger.info("✅ LINEARE Dialog-Initialisierung abgeschlossen")

    def _initialize_projections(self):
        """Projektionen aus Controls ableiten und initialisieren"""
        try:
            logger.info("🔧 Initialisiere Projektionen...")

            # Basis-Columns aus Controls ableiten
            basis_columns = []
            for control_key, control_config in self.controls_config.items():
                if control_config.get('control_type') in ['original', 'show']:
                    basis_col = {
                        'name': control_key,
                        'expertOrder': control_config.get('expert_order', 999),
                        'displayOrder': control_config.get('display_order', 999),
                        'show': control_config.get('show', False),
                        'spaltenueberschrift': control_config.get('name', control_key)
                    }
                    basis_columns.append(basis_col)

            # ✅ PROJEKTIONEN LIVE: Nicht mehr nötig zu speichern - werden live aus Controls berechnet
            logger.info(f"✅ Projektions-System initialisiert für View {self.view_guid} (Live-Berechnung)")

        except Exception as e:
            logger.error(f"❌ Fehler bei Projektions-Initialisierung: {e}")
            raise
    
    def _load_viewdata(self):
        """1. ViewDaten laden mit korrekter PdvmCentralDatenbank"""
        logger.info("🔧 Lade ViewDaten...")
        
        # KORREKTE PdvmCentralDatenbank-Initialisierung oder FEHLER
        try:
            view_db = PdvmCentralDatenbank(
                table_name="viewdaten", 
                guid=self.view_guid
            )
        except Exception as e:
            error_msg = f"❌ PdvmCentralDatenbank-Initialisierung fehlgeschlagen: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            # ROOT-Daten laden
            root_data = view_db.get_static_value(gruppe='ROOT', feld='VIEW_TABLE')
            if not root_data:
                raise ValueError(f"ROOT.VIEW_TABLE nicht gefunden für view_guid: {self.view_guid}")
            
            # METADATEN laden
            metadaten = view_db.get_static_value(gruppe='METADATEN', feld=root_data.upper())
            if not metadaten:
                raise ValueError(f"METADATEN.{root_data.upper()} nicht gefunden für view_guid: {self.view_guid}")
            
            if 'controls' not in metadaten:
                raise ValueError(f"METADATEN.{root_data.upper()}.controls nicht gefunden")
            
            if 'standard_control' not in metadaten or 'dummy' not in metadaten['standard_control']:
                raise ValueError(f"METADATEN.{root_data.upper()}.standard_control.dummy nicht gefunden - KEIN FALLBACK!")
            
            # View-Config zusammenstellen
            self.view_config = {
                'ROOT': {'view_table': root_data},
                'controls': metadaten['controls'],
                'standard_control': metadaten['standard_control']
            }
            
            logger.info(f"✅ ViewDaten geladen: Tabelle '{root_data}', {len(self.view_config['controls'])} Controls, Dummy vorhanden")
            
        except Exception as e:
            error_msg = f"ViewDaten-Ladung fehlgeschlagen für view_guid '{self.view_guid}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _generate_and_save_controls(self):
        """2. Controls linear generieren nach KORREKTEM Ablauf - NUR ViewDaten-Inhalte verwenden"""
        logger.info("🔧 Generiere Controls - NUR aus ViewDaten-Inhalten...")
        
        # SCHRITT 1: ViewDaten Controls sind die Basis - komplett übernehmen und _original umbenennen
        all_controls = {}
        
        for control_key, control_data in self.view_config['controls'].items():
            original_key = f"{control_key}_original"
            
            # KOMPLETT aus ViewDaten übernehmen - was auch immer drin steht
            all_controls[original_key] = control_data.copy()
            all_controls[original_key]['control_type'] = 'original'
            all_controls[original_key]['show'] = False
            
            # Datum-Expansion hinzufügen
            if control_data.get('type') == 'date':
                for suffix in ['_alter', '_jahr', '_monat', '_tag']:
                    expanded_key = f"{control_key}{suffix}_original"
                    all_controls[expanded_key] = control_data.copy()
                    all_controls[expanded_key]['feld'] = f"{control_key}{suffix}"
                    all_controls[expanded_key]['name'] = f"{control_data.get('name', control_key)} ({suffix[1:].title()})"
                    all_controls[expanded_key]['control_type'] = 'original'
                    all_controls[expanded_key]['type'] = f"date{suffix}"  # KORREKT: date_alter, date_jahr, etc.
                    all_controls[expanded_key]['show'] = False
        
        logger.info(f"✅ SCHRITT 1: Original Controls erstellt: {len([k for k in all_controls if k.endswith('_original')])} Controls")
        
        # SCHRITT 2: Aus Original Controls die Show Controls bilden
        original_controls = {k: v for k, v in all_controls.items() if k.endswith('_original')}
        for original_key, original_control in original_controls.items():
            show_key = original_key.replace('_original', '_show')
            all_controls[show_key] = original_control.copy()
            all_controls[show_key]['control_type'] = 'show'
            all_controls[show_key]['show'] = True
            all_controls[show_key]['expert_mode'] = False  # Standard-Spalten sind nie ExpertMode
        
        logger.info(f"✅ SCHRITT 2: Show Controls erstellt: {len([k for k in all_controls if k.endswith('_show')])} Controls")
        
        # SCHRITT 3: Dummy aus ViewDaten kopieren
        dummy_data = self.view_config['standard_control']['dummy']
        all_controls['dummy'] = dummy_data.copy()
        all_controls['dummy']['control_type'] = 'dummy'
        
        logger.info(f"✅ SCHRITT 3: Dummy Control erstellt")
        
        # SCHRITT 4: Benutzer-spezifische WERTE aus GCS laden (ÜBERSPRINGEN bei Reset!)
        if not self.reset:
            try:
                existing_gcs_controls = gcs.db.get_static_value(gruppe=self.view_guid, feld='controls')
                if existing_gcs_controls:
                    logger.info(f"📋 SCHRITT 4: Lade bestehende GCS Controls für Benutzer-Werte")
                    
                    # ERWEITERUNG: Stelle sicher, dass alle erforderlichen Controls vorhanden sind
                    # Füge fehlende Controls hinzu (z.B. uid_original, date-Zusatzfelder)
                    for control_key, control_config in all_controls.items():
                        if control_key not in existing_gcs_controls:
                            existing_gcs_controls[control_key] = control_config.copy()
                            logger.info(f"➕ Fehlendes Control hinzugefügt: {control_key}")
                    
                    # Aktualisiere all_controls mit den erweiterten GCS Controls
                    all_controls = existing_gcs_controls.copy()
                    logger.info(f"📊 Controls erweitert: {len(all_controls)} total")
                    
                    for control_key, control_config in all_controls.items():
                        if control_key in existing_gcs_controls:
                            gcs_control = existing_gcs_controls[control_key]
                            
                            # NUR explizit erlaubte Benutzer-Parameter überschreiben (Whitelist)
                            allowed_user_params = ['expert_mode', 'show', 'expert_order', 'display_order']
                            
                            for prop_key in allowed_user_params:
                                if prop_key in gcs_control and prop_key in control_config:
                                    control_config[prop_key] = gcs_control[prop_key]
                                    logger.debug(f"🔄 '{control_key}.{prop_key}' mit Benutzer-Wert überschrieben")
                            
                            # Alle anderen Parameter bleiben unverändert (Basis-Konfiguration)
                    
                    logger.info(f"✅ SCHRITT 4: Benutzer-spezifische WERTE aus GCS übernommen")
                else:
                    logger.info(f"✅ SCHRITT 4: Keine bestehenden GCS Controls (erste Ausführung)")
                    
            except Exception as e:
                logger.info(f"✅ SCHRITT 4: Keine bestehenden GCS Controls gefunden: {e}")
        else:
            logger.info(f"🔄 SCHRITT 4: ÜBERSPRUNGEN - Reset-Modus aktiviert")
        
        # SCHRITT 5: Controls in GCS speichern - ViewDaten-Änderungen werden immer beachtet
        gcs.db.set_value(
            gruppe=self.view_guid, 
            feld='controls', 
            wert=all_controls
        )
        gcs.db.save_all_values()
        
        self.controls_config = all_controls
        logger.info(f"✅ SCHRITT 5: Controls in GCS gespeichert: {len(all_controls)} total")
        logger.info(f"🎉 KORREKT: ViewDaten bilden die Basis, Benutzer-Werte werden übernommen!")
        
        # SCHRITT 6: Basis-Spalten aus Controls ableiten (wie View-Manager)
        self.basis_columns = self._get_columns_from_controls()
        logger.info(f"✅ SCHRITT 6: {len(self.basis_columns)} Basis-Spalten abgeleitet")
    
    def _load_data(self):
        """3. Daten laden"""
        logger.info("🔧 Lade Daten...")
        
        try:
            table_name = self.view_config['ROOT']['view_table']
            data_db = PdvmCentralDatenbank(table_name=table_name)
            
            self.raw_records = data_db.get_all_records()
            
            # Performance-Instanzen erstellen
            self.optimized_instances = []
            for record in self.raw_records:
                instance = PdvmCentralDatenbank.create_with_data(
                    guid=record["uid"],
                    daten=record["daten"],
                    table_name=table_name
                )
                self.optimized_instances.append(instance)
            
            logger.info(f"✅ Daten geladen: {len(self.optimized_instances)} Instanzen")
            
        except Exception as e:
            logger.error(f"❌ Datenladung fehlgeschlagen: {e}")
            self.raw_records = []
            self.optimized_instances = []
    
    def _build_matrix(self):
        """VEREINFACHTE LINEARE Matrix-Erstellung - Stufe 1: Datenaufbau"""
        logger.info("🔧 Erstelle Matrix - LINEARE VEREINFACHUNG...")

        self.display_matrix = []

        for instance in self.optimized_instances:
            row_data = {}

            # STUFE 1: ORIGINAL-FELDER befüllen - LINEAR und einfach
            logger.info(f"📊 Befülle Original-Felder für Instanz: {instance.guid}")

            # SPEZIALFALL: uid_original - GUID des Datensatzes selbst
            if 'uid_original' in self.controls_config:
                row_data['uid_original'] = instance.guid
                row_data['uid_original_abdatum'] = None  # uid hat kein Abdatum
                row_data['uid_original_formatiertes_abdatum'] = None
                logger.info(f"  🔑 uid_original: {instance.guid}")
            else:
                logger.warning("  ⚠️ uid_original nicht in controls_config gefunden")
                row_data['uid_original'] = instance.guid
                row_data['uid_original_abdatum'] = None  # uid hat kein Abdatum
                row_data['uid_original_formatiertes_abdatum'] = None
                logger.info(f"  🔑 uid_original: {instance.guid}")

            # Sortiere Controls so dass Basis-Felder vor Zusatzfeldern verarbeitet werden
            def sort_key(control_key):
                control_config = self.controls_config.get(control_key, {})
                control_type = control_config.get('type', '')
                # Basis-Felder zuerst (keine date_*-Typen), dann Zusatzfelder
                if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                    return 1  # Zusatzfelder später
                else:
                    return 0  # Basis-Felder zuerst
            
            # Erstelle sortierte Liste der Original-Controls (ohne uid_original, da bereits behandelt)
            original_controls = [(k, v) for k, v in self.controls_config.items() 
                               if v.get('control_type') == 'original' and k != 'uid_original']
            sorted_controls = sorted(original_controls, key=lambda x: sort_key(x[0]))

            for control_key, control_config in sorted_controls:
                # uid_original wurde bereits oben behandelt und ist nicht in dieser Liste
                
                # SPEZIALFALL: Date-Zusatzfelder werden im Original berechnet
                    control_type = control_config.get('type', '')
                    if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                        # Basis-Datumsfeld finden (entferne alle Suffixe)
                        base_field = control_key.replace('_original', '').replace('_alter', '').replace('_jahr', '').replace('_monat', '').replace('_tag', '')
                        base_original = f"{base_field}_original"
                        
                        logger.info(f"    🔍 Basis-Feld für {control_key}: {base_original}")
                        
                        # WICHTIG: Verwende den WERT aus dem Basis-Feld für Berechnung, NICHT das Abdatum!
                        base_wert = row_data.get(base_original)
                        logger.info(f"    📊 Basis-Wert: {base_wert} (Typ: {type(base_wert)})")
                        if base_wert is not None:
                            try:
                                # Verwende den Wert aus dem Basis-Feld für Berechnung
                                if isinstance(base_wert, (int, float)):
                                    numeric_value = float(base_wert)
                                elif isinstance(base_wert, str) and base_wert.replace('.', '').isdigit():
                                    numeric_value = float(base_wert)
                                else:
                                    numeric_value = None
                                
                                if numeric_value is not None and numeric_value != 1001.0:  # Nicht den Default-Wert verwenden
                                    # Verwende temp_dt_inst für Berechnung
                                    # GCS direkt verwenden - keine Zwischenspeicherung nötig
                                    dt = gcs.temp_dt_inst
                                    logger.info(f"    🔧 temp_dt_inst erhalten: {dt is not None}")
                                    if dt:
                                        dt.PdvmDateTime = numeric_value
                                        logger.info(f"    📅 PdvmDateTime gesetzt: {numeric_value} → dt.PdvmDateTime = {dt.PdvmDateTime}")
                                        logger.info(f"    📅 FormTimeStamp verfügbar: {hasattr(dt, 'FormTimeStamp')}")
                                        
                                        if control_type == 'date_alter':
                                            # Alter berechnen mit der neuen calc_alter Methode
                                            try:
                                                # Alter berechnen (verwendet automatisch aktuelles Datum als Stichtag)
                                                calculated_value = str(dt.calc_alter(gcs.stichtag))
                                                logger.info(f"    📅 Alter berechnet: {numeric_value} → {calculated_value} Jahre")
                                            except Exception as calc_error:
                                                calculated_value = ""
                                                logger.warning(f"    ⚠️ Fehler bei Alter-Berechnung: {calc_error}")
                                                logger.warning(f"    🔍 DEBUG: dt.PdvmDateTime = {getattr(dt, 'PdvmDateTime', 'N/A')}")
                                                logger.warning(f"    🔍 DEBUG: dt.pdvmdatetime = {getattr(dt, 'pdvmdatetime', 'N/A')}")
                                        elif control_type == 'date_jahr':
                                            calculated_value = str(dt.Year)
                                            logger.info(f"    📅 Jahr: dt.Year = {dt.Year}")
                                        elif control_type == 'date_monat':
                                            calculated_value = str(dt.Month)
                                            logger.info(f"    📅 Monat: dt.Month = {dt.Month}")
                                        elif control_type == 'date_tag':
                                            calculated_value = str(dt.Day)
                                            logger.info(f"    📅 Tag: dt.Day = {dt.Day}")

                                        row_data[control_key] = calculated_value
                                        logger.info(f"    📅 {control_type}: {numeric_value} → {calculated_value}")
                                    else:
                                        row_data[control_key] = ""
                                        logger.info(f"    📅 {control_type}: kein temp_dt_inst verfügbar")
                                else:
                                    row_data[control_key] = ""
                                    logger.info(f"    📅 {control_type}: kein gültiger numerischer Wert oder Default-Wert ({numeric_value})")
                            except Exception as e:
                                row_data[control_key] = ""
                                logger.warning(f"    ⚠️ Fehler bei {control_type} Berechnung: {e}")
                        else:
                            row_data[control_key] = ""
                            logger.info(f"    📅 {control_type}: kein Basis-Wert verfügbar")
                        
                        # Date-Zusatzfelder haben kein eigenes Abdatum
                        row_data[f"{control_key}_abdatum"] = None
                        row_data[f"{control_key}_formatiertes_abdatum"] = None
                        logger.info(f"  📅 {control_key}: {row_data[control_key]} (berechnet im Original)")
                        continue
                        
                    feld = control_config.get('feld')
                    gruppe = control_config.get('gruppe', 'SYSTEM')
                    control_type = control_config.get('type', '')

                    if feld:
                        try:
                            logger.info(f"  🔍 Original-Control: {control_key}, Feld: {feld}, Gruppe: {gruppe}")

                            # WERT und ABDATUM aus Datenbank holen
                            result = instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
                            logger.info(f"    📋 get_value({gruppe}, {feld}) = {result}")
                            
                            # DEBUG: Detaillierte Analyse des Results
                            logger.info(f"    🔍 DEBUG get_value Result: type={type(result)}, value='{result}'")
                            if isinstance(result, tuple):
                                logger.info(f"    🔍 DEBUG Tuple-Inhalt: len={len(result)}, [0]={result[0]} (type={type(result[0])}), [1]={result[1]} (type={type(result[1])})")

                            # Wert und Abdatum extrahieren
                            if isinstance(result, tuple) and len(result) >= 2:
                                wert, abdatum = result[0], result[1]
                            else:
                                wert, abdatum = result, None

                            logger.info(f"    💾 Wert: {wert}, Abdatum: {abdatum}")

                            # EBENE 1: WERT speichern
                            row_data[control_key] = wert

                            # EBENE 2: ABDATUM speichern (roh)
                            row_data[f"{control_key}_abdatum"] = abdatum

                            # EBENE 3: FORMATIERTES ABDATUM speichern (bereits formatiert)
                            if abdatum:
                                formatiertes_abdatum = self._format_abdatum(abdatum)
                                row_data[f"{control_key}_formatiertes_abdatum"] = formatiertes_abdatum
                                logger.info(f"    🎨 Formatiertes Abdatum: {formatiertes_abdatum}")
                                # DEBUG: Prüfe was tatsächlich gespeichert wird
                                logger.info(f"    🔍 DEBUG Matrix-Speicherung: key='{control_key}_formatiertes_abdatum', value='{formatiertes_abdatum}', type={type(formatiertes_abdatum)}")
                            else:
                                row_data[f"{control_key}_formatiertes_abdatum"] = None

                        except Exception as e:
                            logger.debug(f"❌ Fehler bei {control_key}: {e}")
                            row_data[control_key] = None
                            row_data[f"{control_key}_abdatum"] = None
                            row_data[f"{control_key}_formatiertes_abdatum"] = None
                    else:
                        row_data[control_key] = None
                        row_data[f"{control_key}_abdatum"] = None
                        row_data[f"{control_key}_formatiertes_abdatum"] = None

            # STUFE 2: SHOW-FELDER aus ORIGINAL-FELDERN bestücken - LINEAR
            logger.info("📋 Befülle Show-Felder aus Original-Feldern")

            for control_key, control_config in self.controls_config.items():
                if control_config.get('control_type') == 'show':
                    # Original-Feld finden
                    original_key = control_key.replace('_show', '_original')

                    logger.info(f"  🔄 Show-Control: {control_key} ← {original_key}")

                    # SPEZIALFALL: uid_show - ersten 8 Stellen + "..."
                    if control_key == 'uid_show':
                        original_guid = row_data.get('uid_original')
                        if original_guid and isinstance(original_guid, str) and len(original_guid) >= 8:
                            show_value = f"{original_guid[:8]}..."
                            row_data[control_key] = show_value
                            logger.info(f"    🔑 uid_show: {original_guid} → {show_value}")
                        else:
                            row_data[control_key] = ""
                            logger.info(f"    🔑 uid_show: kein gültiger Original-Wert")
                        
                        # uid_show hat kein Abdatum
                        row_data[f"{control_key}_abdatum"] = None
                        row_data[f"{control_key}_formatiertes_abdatum"] = None
                        continue

                    # SPEZIALFALL: Date-Zusatzfelder (_alter, _jahr, _monat, _tag) - Werte aus Original kopieren
                    control_type = control_config.get('type', '')
                    if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                        # Wert aus dem bereits berechneten Original-Feld kopieren
                        original_calculated_value = row_data.get(original_key)
                        if original_calculated_value is not None:
                            row_data[control_key] = original_calculated_value
                            logger.info(f"    📅 {control_type}: {original_calculated_value} (aus Original kopiert)")
                        else:
                            row_data[control_key] = ""
                            logger.info(f"    📅 {control_type}: kein Original-Wert verfügbar")
                        
                        # Date-Zusatzfelder haben kein eigenes Abdatum
                        row_data[f"{control_key}_abdatum"] = None
                        row_data[f"{control_key}_formatiertes_abdatum"] = None
                        continue

                    # SPEZIALFALL: Einfache Date-Felder - Wert aus Original in lesbares Datum umwandeln
                    if control_type == 'date':
                        original_wert = row_data.get(original_key)
                        if original_wert is not None and original_wert != 1001.0:
                            try:
                                # GCS direkt verwenden - keine Zwischenspeicherung nötig
                                dt = gcs.temp_dt_inst
                                if dt:
                                    dt.PdvmDateTime = float(original_wert)
                                    show_value = dt.Date  # Einfaches Datum formatieren
                                    row_data[control_key] = show_value
                                    logger.info(f"    📅 Date konvertiert: {original_wert} → {show_value}")
                                else:
                                    row_data[control_key] = str(original_wert)
                                    logger.info(f"    📅 Date (Fallback): {original_wert} (keine temp Instanz)")
                            except Exception as e:
                                row_data[control_key] = str(original_wert)
                                logger.warning(f"    ⚠️ Fehler bei Date-Konvertierung {original_wert}: {e}")
                        else:
                            row_data[control_key] = ""
                            logger.info(f"    📅 Date: leer oder Default-Wert ({original_wert})")
                        
                        # Abdatum und formatiertes Abdatum aus Original kopieren
                        original_abdatum = row_data.get(f"{original_key}_abdatum")
                        row_data[f"{control_key}_abdatum"] = original_abdatum
                        original_formatiertes = row_data.get(f"{original_key}_formatiertes_abdatum")
                        row_data[f"{control_key}_formatiertes_abdatum"] = original_formatiertes
                        continue

                    # NORMALFALL: WERT aus Original kopieren
                    original_wert = row_data.get(original_key)
                    if original_wert is None:
                        row_data[control_key] = ""
                        logger.info(f"    📝 None → leer")
                    else:
                        # SPEZIALFALL: Dropdown-Felder übersetzen
                        control_type = control_config.get('type', '')
                        if control_type == 'dropdown':
                            # Dropdown-Konfiguration auslesen
                            dropdown_config = control_config.get('dropdown', {})
                            dropdown_guid = dropdown_config.get('key', '')  # GUID des Dropdowns
                            dropdown_gruppe = dropdown_config.get('value', '')  # Gruppe (z.B. 'anrede')
                            
                            if dropdown_guid:
                                # GCS für Übersetzung verwenden
                                # GCS direkt verwenden
                                if gcs:
                                    try:
                                        # Verwende die GUID und Gruppe für die Übersetzung
                                        translated_value = gcs.translate_dropdown_value(dropdown_guid, str(original_wert), dropdown_gruppe)
                                        row_data[control_key] = translated_value
                                        logger.info(f"    📋 Dropdown '{dropdown_gruppe}' (GUID: {dropdown_guid}): {original_wert} → {translated_value}")
                                    except Exception as e:
                                        row_data[control_key] = str(original_wert)
                                        logger.warning(f"    ⚠️ Dropdown-Übersetzung fehlgeschlagen '{dropdown_gruppe}' (GUID: {dropdown_guid}): {e}")
                                else:
                                    row_data[control_key] = str(original_wert)
                                    logger.warning(f"    ⚠️ GCS nicht verfügbar für Dropdown-Übersetzung")
                            else:
                                row_data[control_key] = str(original_wert)
                                logger.info(f"    📋 Dropdown ohne GUID: {original_wert}")
                        else:
                            # Normaler Wert kopieren
                            row_data[control_key] = original_wert
                            logger.info(f"    📝 Kopiert: {original_wert}")

                    # ABDATUM kopieren (Ebene 2)
                    original_abdatum = row_data.get(f"{original_key}_abdatum")
                    row_data[f"{control_key}_abdatum"] = original_abdatum

                    # FORMATIERTES ABDATUM kopieren (Ebene 3)
                    original_formatiertes = row_data.get(f"{original_key}_formatiertes_abdatum")
                    row_data[f"{control_key}_formatiertes_abdatum"] = original_formatiertes

                    logger.info(f"    📅 Abdatum: {original_abdatum}")
                    logger.info(f"    🎨 Formatiertes: {original_formatiertes}")

            # DUMMY-CONTROL
            if 'dummy' in self.controls_config:
                row_data['dummy'] = ''

            # FILTER: Zeile nur hinzufügen wenn nicht alle Original-Felder leer sind
            if not self._all_original_fields_empty(row_data):
                # LINEARES FILTER-SYSTEM: Jede Zeile bekommt display=True (wird später für Filter genutzt)
                row_data['display'] = True
                self.display_matrix.append(row_data)
                logger.info(f"✅ Zeile hinzugefügt - {len(row_data)} Felder")
            else:
                logger.debug(f"⚠️ Zeile gefiltert (alle Original-Felder leer): {instance.guid}")

        logger.info(f"✅ Matrix erstellt: {len(self.display_matrix)} Zeilen (aus {len(self.optimized_instances)} Instanzen)")
        logger.info("🎯 LINEARE Matrix-Erstellung abgeschlossen - robust und einfach!")
    
    def _format_abdatum(self, abdatum_value):
        """Formatiert einen Abdatum-Wert in lesbares Format - PERFORMANCE OPTIMIERT"""
        if abdatum_value is None:
            return None
        
        # SPEZIALFALL: Default-Wert 1001.0 (01.01.0001) als lesbaren Text darstellen
        if float(abdatum_value) == 1001.0:
            return "01.01.0001 (Default)"
        
        try:
            # GCS direkt verwenden - keine Zwischenspeicherung nötig
            dt = gcs.temp_dt_inst
            if dt is None:
                # Fallback wenn temporäre Instanz nicht verfügbar (sollte nicht passieren)
                return f"{abdatum_value} (nicht formatiert)"
            
            dt.PdvmDateTime = float(abdatum_value)
            formatted = dt.FormTimeStamp
            logger.info(f"🔍 DEBUG Abdatum formatiert: {abdatum_value} → {formatted}")
            
            return formatted
        except Exception as e:
            logger.debug(f"Fehler bei Abdatum-Formatierung {abdatum_value}: {e}")
            return f"{abdatum_value} (Fehler)"
    
    def _all_original_fields_empty(self, row_data):
        """Prüft ob alle Original-Felder einer Zeile leer/None sind - VEREINFACHT"""
        # Sammle alle Original-Felder (control_type == 'original')
        original_fields = [key for key, config in self.controls_config.items()
                          if config.get('control_type') == 'original']

        if not original_fields:
            # Keine Original-Felder gefunden - Zeile behalten
            return False

        # Prüfe ob alle Original-Felder leer sind (nur Ebene 1: Wert)
        for field_key in original_fields:
            # SPEZIALFÄLLE: Diese Felder haben immer einen Wert und zählen nicht als "leer"
            if field_key == 'uid_original':
                continue  # uid_original hat immer die GUID
            
            # Date-Zusatzfelder haben immer einen berechneten Wert
            control_config = self.controls_config.get(field_key, {})
            control_type = control_config.get('type', '')
            if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                continue  # Diese werden immer berechnet
            
            value = row_data.get(field_key)
            # Feld ist nicht leer wenn es einen Wert hat (nicht None, nicht leerer String, nicht 0 bei Zahlen)
            if value is not None and value != '' and value != 0:
                return False

        # Alle relevanten Original-Felder sind leer
        return True
    
    def _create_ui(self):
        """5. UI erstellen"""
        logger.info("🔧 Erstelle UI...")
        
        self.display = PdvmViewDisplay(self)
        
        logger.info("✅ UI erstellt")
        
        # Nach UI-Erstellung: Persistente Filter laden und anwenden
        self._load_and_apply_persistent_filters()
    
    def _load_and_apply_persistent_filters(self):
        """Lade persistente Suchparameter und wende sie an"""
        try:
            if not gcs:
                return
            
            # GCS Key für persistente Speicherung der Suchparameter
            gcs_filters_key = f"search_parameters_{self.view_guid}"
            saved_filters, _ = gcs.db.get_value(self.view_guid, gcs_filters_key)
            
            if saved_filters:
                logger.info(f"🔄 Lade {len(saved_filters)} persistente Suchparameter")
                self.display.apply_column_filters(saved_filters)
                logger.info("✅ Persistente Suchparameter automatisch angewendet")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden persistenter Suchparameter: {e}")
    
    def apply_filter_string(self, filter_string):
        """🎯 ZENTRALE FILTER-METHODE - NEUE LINEARE FILTER-EXECUTION
        
        Args:
            filter_string (str): Filterstring im Format "feld1:wert1||feld2:wert2||EXTENDED:feld3:bedingungen"
        """
        try:
            logger.info("🎯 === LINEARE FILTER-EXECUTION GESTARTET ===")
            logger.info(f"📂 View-GUID: {self.view_guid}")
            logger.info(f"🔍 Filter-String: '{filter_string}'")
            
            # SCHRITT 1: LinearFilterExecutionManager holen
            from linear_filter_execution_manager import get_linear_filter_manager
            manager = get_linear_filter_manager(self.view_guid)
            
            # SCHRITT 2: Leerer Filter - alle Filter löschen
            if not filter_string or filter_string.strip() == "":
                logger.info("🧹 Leerer Filter - lösche alle Filter linear")
                success = manager.clear_all_filters()
                if success:
                    if hasattr(self, 'display') and self.display and hasattr(self.display, '_show_all_rows'):
                        self.display._show_all_rows()
                    if hasattr(self, 'display') and self.display:
                        self.display.refresh_table()
                return
            
            # SCHRITT 3: Lineare Filter-Type-Erkennung und -Ausführung
            success = False
            
            if 'EXTENDED:' in filter_string:
                # EXTENDED FILTER - über LinearFilterExecutionManager
                logger.info("🔧 EXTENDED Filter erkannt - verwende lineare Execution")
                filter_config = {
                    'filter_string': filter_string,
                    'field_name': self._extract_field_from_extended_string(filter_string),
                    'conditions': self._parse_extended_conditions_from_string(filter_string)
                }
                success = manager.execute_filter_linear('extended', filter_config)
                
            elif ':' in filter_string:
                # STRUKTURIERTER/PARAMETRISCHER FILTER - über LinearFilterExecutionManager  
                logger.info("🎛️ Strukturierter Filter erkannt - verwende lineare Execution")
                filter_config = self._parse_to_parametric_config(filter_string)
                success = manager.execute_filter_linear('parametric', filter_config)
                
            else:
                # GESAMTFILTER/GLOBALE SUCHE - über LinearFilterExecutionManager
                logger.info(f"🌐 Gesamtfilter erkannt - verwende lineare Execution")
                filter_config = {'filter_text': filter_string}
                success = manager.execute_filter_linear('gesamtfilter', filter_config)
            
            # SCHRITT 4: Ergebnis-Behandlung
            if success:
                logger.info("✅ Lineare Filter-Execution erfolgreich")
                if hasattr(self, 'display') and self.display:
                    self.display.refresh_table()
            else:
                logger.error("❌ Lineare Filter-Execution fehlgeschlagen")
                # Fallback: Alle Zeilen anzeigen
                if hasattr(self, 'display') and self.display and hasattr(self.display, '_show_all_rows'):
                    self.display._show_all_rows()
                if hasattr(self, 'display') and self.display:
                    self.display.refresh_table()
                    
        except Exception as e:
            logger.error(f"❌ Fehler bei linearer Filter-Execution: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback: Alle Zeilen anzeigen
            if hasattr(self, 'display') and self.display and hasattr(self.display, '_show_all_rows'):
                self.display._show_all_rows()
            if hasattr(self, 'display') and self.display:
                self.display.refresh_table()
            
            # SCHRITT 3: Display-Update
            if hasattr(self, 'display') and self.display:
                self.display.refresh_table()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim stufenweisen Filtern: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_extended_filters_direct(self, filter_string):
        """Direkte Anwendung der Extended Filter Engine"""
        try:
            logger.info("🚀 Starte direkte Extended Filter Engine Anwendung")
            
            # Import Extended Filter Engine
            from extended_filter_engine import extended_filter_engine
            
            # Direkt die Extended Filter Engine auf die Tabelle anwenden
            extended_filter_engine.apply_extended_filters_to_table(self, {})
            
            logger.info("✅ Extended Filter Engine direkt angewendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei direkter Extended Filter Anwendung: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_structured_filters(self, filter_conditions):
        """Strukturierte Filter stufenweise anwenden"""
        initial_count = len([row for row in self.display_matrix if row['display']])
        
        for condition_idx, condition in enumerate(filter_conditions):
            column_name = condition['column']
            operator = condition['operator']
            value = condition['value']
            
            logger.info(f"📍 Stufe {condition_idx + 1}: Spalte '{column_name}' mit '{operator}:{value}'")
            
            # Nur Zeilen mit display=True prüfen
            active_rows = [row for row in self.display_matrix if row['display']]
            if not active_rows:
                logger.info(f"⚠️ Keine aktiven Zeilen mehr - Filter-Abbruch bei Stufe {condition_idx + 1}")
                break
            
            # EXTENDED Filter haben spezielle Behandlung
            if column_name == 'EXTENDED':
                matched_rows = self._apply_extended_condition(active_rows, operator, value)
                # Alle Zeilen auf display=False setzen, dann nur matched_rows auf True
                for row in self.display_matrix:
                    row['display'] = False
                for row in matched_rows:
                    row['display'] = True
            else:
                # Normale strukturierte Filter
                for row in active_rows:
                    uid = row.get('uid_show', 'unknown')
                    row_value = row.get(column_name, '')
                    
                    # Filter-Logik anwenden
                    matches = self._apply_single_condition(row_value, operator, value)
                    
                    if not matches:
                        row['display'] = False
                        logger.debug(f"    🚫 UID {uid}: '{row_value}' filtert raus")
                    else:
                        logger.debug(f"    ✅ UID {uid}: '{row_value}' bleibt")
            
            remaining_count = len([row for row in self.display_matrix if row['display']])
            logger.info(f"    📊 Stufe {condition_idx + 1} Ergebnis: {remaining_count} von {len(active_rows)} Zeilen verbleiben")
            
            # Frühzeitiger Abbruch wenn keine Zeilen mehr da sind
            if remaining_count == 0:
                logger.info("⚠️ Keine Zeilen mehr gefunden - Filter-Abbruch")
                break
        
        final_count = len([row for row in self.display_matrix if row['display']])
        logger.info(f"✅ Strukturierte Filterung abgeschlossen: {final_count} von {initial_count} Zeilen sichtbar")
    
    def _apply_global_search(self, search_text):
        """Globale Suche in allen sichtbaren Spalten"""
        # Hole die sichtbaren Spalten direkt vom Display-Widget
        visible_columns = []
        if hasattr(self, 'display') and self.display:
            try:
                visible_columns = self.display._get_visible_columns_from_gcs()
                logger.info(f"🔍 Globale Suche in {len(visible_columns)} sichtbaren Spalten")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Abrufen sichtbarer Spalten: {e}")
        
        if not visible_columns:
            # Fallback: Alle show-Spalten
            if self.display_matrix:
                visible_columns = [key for key in self.display_matrix[0].keys() 
                                 if key.endswith('_show') and key != 'display']
                logger.info(f"🔍 Fallback: Verwende {len(visible_columns)} Show-Spalten für globale Suche")
            else:
                logger.warning("⚠️ Keine Spalten für globale Suche verfügbar")
                return
        
        search_lower = search_text.lower()
        matched_count = 0
        
        for row in self.display_matrix:
            uid = row.get('uid_show', 'unknown')
            matches = False
            
            # Durchsuche alle sichtbaren Spalten
            for column_name in visible_columns:
                if column_name == 'display':  # display-Feld überspringen
                    continue
                    
                row_value = row.get(column_name, '')
                if row_value is not None and search_lower in str(row_value).lower():
                    matches = True
                    logger.debug(f"    ✅ UID {uid}: Gefunden in '{column_name}' → '{row_value}'")
                    break
            
            row['display'] = matches
            if matches:
                matched_count += 1
            else:
                logger.debug(f"    🚫 UID {uid}: Kein Match in sichtbaren Spalten")
        
        logger.info(f"✅ Globale Suche abgeschlossen: {matched_count} von {len(self.display_matrix)} Zeilen sichtbar")
    
    def _apply_extended_condition(self, active_rows, operator, value):
        """EXTENDED Filter anwenden - Komplexe Bedingungen aus SearchParameterDialog"""
        # Parse EXTENDED Format: "vorname_show:NOT enthält 'lau'"
        try:
            logger.info(f"🔧 EXTENDED Parser: operator='{operator}', value='{value}'")
            
            # value enthält den vollständigen Condition-String
            condition_text = value.strip()  # "NOT enthält 'lau'"
            
            # Parse die Bedingung mit Regex
            import re
            
            # Check für Negation
            is_negated = condition_text.startswith('NOT ')
            if is_negated:
                condition_text = condition_text[4:].strip()  # Entferne "NOT "
            
            # Parse "enthält 'wert'"
            if 'enthält' in condition_text:
                match = re.search(r"enthält\s+'([^']*)'", condition_text)
                if match:
                    search_value = match.group(1)
                    column_name = operator.lower()  # Der Spaltenname
                    
                    logger.info(f"🔧 EXTENDED Parsed: column='{column_name}', value='{search_value}', negated={is_negated}")
                    
                    matched_rows = []
                    for row in active_rows:
                        if not row.get('display', True):  # Nur aktive Zeilen
                            continue
                            
                        row_value = row.get(column_name, '')
                        contains_match = search_value.lower() in str(row_value).lower()
                        
                        # Negation anwenden
                        if is_negated:
                            matches = not contains_match
                        else:
                            matches = contains_match
                        
                        if matches:
                            matched_rows.append(row)
                            
                    logger.info(f"🔧 EXTENDED Result: {len(matched_rows)} von {len(active_rows)} Zeilen")
                    return matched_rows
                    
            logger.warning(f"⚠️ EXTENDED Format nicht erkannt: '{condition_text}'")
            return active_rows
                    
        except Exception as e:
            logger.warning(f"⚠️ EXTENDED Parser Fehler: {e}")
            return active_rows
    
    def _parse_filter_string(self, filter_string):
        """Filter-String in einzelne Bedingungen zerlegen
        Args:
            filter_string (str): z.B. "vorname_show:Lau|familienname_show:NOT:Müller"
        Returns:
            list: Liste von Filter-Bedingungen [{'column': 'name', 'operator': 'CONTAINS', 'value': 'text'}]
        """
        conditions = []
        
        if not filter_string or not filter_string.strip():
            return conditions
        
        try:
            # Trennung nach | für mehrere Bedingungen
            parts = filter_string.split('|')
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Parse einzelne Bedingung: "spalte:operator:wert" oder "spalte:wert" oder "EXTENDED:spalte:bedingung"
                if ':' in part:
                    components = part.split(':', 2)  # Maximal 3 Teile
                    
                    if len(components) == 2:
                        # Format: "spalte:wert" -> Standard-Contains
                        column, value = components
                        conditions.append({
                            'column': column.strip(),
                            'operator': 'CONTAINS',
                            'value': value.strip()
                        })
                    elif len(components) == 3:
                        # Format: "spalte:operator:wert" oder "EXTENDED:spalte:bedingung"
                        column, operator, value = components
                        
                        if column.strip().upper() == 'EXTENDED':
                            # EXTENDED Format: "EXTENDED:vorname_show:NOT enthält 'lau'"
                            conditions.append({
                                'column': 'EXTENDED',
                                'operator': operator.strip(),  # vorname_show
                                'value': value.strip()         # NOT enthält 'lau'
                            })
                        else:
                            # Standard Format: "spalte:operator:wert"
                            conditions.append({
                                'column': column.strip(),
                                'operator': operator.strip().upper(),
                                'value': value.strip()
                            })
                    elif len(components) > 3 and components[0].strip().upper() == 'EXTENDED':
                        # EXTENDED Format mit mehreren Doppelpunkten: "EXTENDED:spalte:bedingung:mit:doppelpunkt"
                        column = 'EXTENDED'
                        operator = components[1].strip()
                        value = ':'.join(components[2:]).strip()
                        conditions.append({
                            'column': column,
                            'operator': operator,
                            'value': value
                        })
                        
            logger.info(f"📋 Filter geparst: {len(conditions)} Bedingungen erkannt")
            for i, cond in enumerate(conditions):
                logger.info(f"    {i+1}. {cond['column']} {cond['operator']} '{cond['value']}'")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen des Filter-Strings '{filter_string}': {e}")
        
        return conditions
    
    def _apply_single_condition(self, row_value, operator, filter_value):
        """Einzelne Filter-Bedingung auf einen Zellenwert anwenden
        Args:
            row_value: Wert aus der Matrix-Zeile
            operator (str): 'CONTAINS', 'NOT', 'EQUALS', etc.
            filter_value (str): Suchwert
        Returns:
            bool: True wenn die Bedingung erfüllt ist
        """
        if row_value is None:
            row_value = ''
        
        row_str = str(row_value).lower()
        filter_str = str(filter_value).lower()
        
        try:
            if operator == 'CONTAINS':
                return filter_str in row_str
            elif operator == 'NOT':
                return filter_str not in row_str
            elif operator == 'EQUALS':
                return row_str == filter_str
            elif operator == 'STARTS':
                return row_str.startswith(filter_str)
            elif operator == 'ENDS':
                return row_str.endswith(filter_str)
            else:
                # Fallback: CONTAINS
                logger.warning(f"⚠️ Unbekannter Operator '{operator}', verwende CONTAINS")
                return filter_str in row_str
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Bedingungsprüfung: {e}")
            return False
    
    def clear_all_filters(self):
        """Alle Filter löschen - EINFACH UND DIREKT"""
        try:
            logger.info("🗑️ === ALLE FILTER LÖSCHEN - START ===")
            
            # SCHRITT 1: Persistenz löschen (KRITISCH für komplexe Filter!)
            try:
                if gcs and hasattr(self, 'view_guid'):
                    gcs_filters_key = f"search_parameters_{self.view_guid}"
                    gcs.db.set_value(self.view_guid, gcs_filters_key, None)  # Persistente Filter löschen
                    logger.info("✅ Persistente Suchparameter gelöscht")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Löschen der Persistenz: {e}")
            
            # SCHRITT 2: DIREKTE Tabellen-Sichtbarkeit zurücksetzen (das ist das ECHTE System!)
            hidden_count = 0
            table = None
            
            # Tabelle finden (wie Extended Filter Engine)
            if hasattr(self, 'display') and hasattr(self.display, 'table'):
                table = self.display.table
            elif hasattr(self, 'table'):
                table = self.table
            
            if table and hasattr(table, 'rowCount'):
                total_rows = table.rowCount()
                for row_index in range(total_rows):
                    if table.isRowHidden(row_index):
                        table.setRowHidden(row_index, False)
                        hidden_count += 1
                
                logger.info(f"✅ TABELLEN-Reset: {total_rows} Zeilen total, {hidden_count} waren versteckt und wurden sichtbar gemacht")
                
                # Gesamtsuche leeren
                if hasattr(self, 'display') and hasattr(self.display, 'search_input'):
                    self.display.search_input.clear()
                    logger.info("✅ Gesamtsuche-Feld geleert")
                
                # VERIFIKATION der echten Tabellen-Sichtbarkeit
                visible_rows = sum(1 for i in range(total_rows) if not table.isRowHidden(i))
                logger.info(f"🔍 VERIFIKATION: {visible_rows} von {total_rows} Zeilen sind in der TABELLE sichtbar")
                
                if visible_rows == total_rows:
                    logger.info("✅ ERFOLGREICH: Alle Zeilen sind in der Tabelle sichtbar!")
                else:
                    logger.error(f"❌ TABELLEN-FEHLER: Nur {visible_rows} von {total_rows} Zeilen sind sichtbar!")
                    
            else:
                logger.warning("⚠️ Keine Tabelle gefunden!")
                logger.info(f"🔍 DEBUG: display={hasattr(self, 'display')}, table={hasattr(self, 'table')}")
                if hasattr(self, 'display'):
                    logger.info(f"🔍 DEBUG: display.table={hasattr(self.display, 'table')}")
            
            logger.info("🗑️ === ALLE FILTER LÖSCHEN - ENDE ===")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen aller Filter: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    
    def get_display_widget(self):
        """Widget für Integration zurückgeben"""
        return self.display
    
    def _get_columns_from_controls(self):
        """Basis-Spalten aus controls_config ableiten (wie View-Manager)"""
        try:
            # PRIORITÄT 1: Verwende view_manager.basis_columns wenn verfügbar
            if hasattr(self, 'view_manager') and self.view_manager and hasattr(self.view_manager, 'basis_columns'):
                logger.info(f"✅ Verwende {len(self.view_manager.basis_columns)} Spalten aus view_manager")
                return self.view_manager.basis_columns
            
            # PRIORITÄT 2: Eigene Ableitung aus controls_config (Fallback)
            columns = []
            for control_key, control_config in self.controls_config.items():
                # WICHTIG: Alle Felder korrekt mappen und sicherstellen dass sie existieren
                simple_col = {
                    'name': control_key,
                    'label': control_config.get('name', control_key),
                    'type': control_config.get('type', 'string'),
                    'show': control_config.get('show', True),
                    'expertOrder': control_config.get('expert_order', control_config.get('order', 999)),  
                    'displayOrder': control_config.get('display_order', control_config.get('order', 999)),  
                    'expert': control_config.get('expert_mode', False),  
                    'field_config': control_config.get('field_config', {}),
                    'spaltenueberschrift': control_config.get('name', control_key),
                    'gruppe': control_config.get('gruppe'),
                    'feld': control_config.get('feld')
                }
                
                # Sicherheitscheck: Alle Order-Felder müssen valide Zahlen sein
                if not isinstance(simple_col['expertOrder'], (int, float)):
                    simple_col['expertOrder'] = 999
                if not isinstance(simple_col['displayOrder'], (int, float)):
                    simple_col['displayOrder'] = simple_col['expertOrder']
                    
                columns.append(simple_col)
                
            logger.info(f"✅ {len(columns)} Basis-Spalten aus controls_config abgeleitet")
            
            # Debug-Output für erste 3 Spalten
            for col in columns[:3]:
                logger.debug(f"  {col['name']}: expertOrder={col['expertOrder']}, displayOrder={col['displayOrder']}, show={col['show']}")
                
            return columns
        except Exception as e:
            logger.error(f"❌ Fehler beim Basis-Spalten-Aufbau: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def reload(self):
        """Reload bei Stichtag-Änderung"""
        logger.info("🔄 Reload...")
        self._build_matrix()
        if self.display:
            self.display.refresh_table()


class PdvmViewDisplay(QWidget):
    """
    SAUBERES UI-Display für PdvmViewDialog
    """
    
    def __init__(self, view_dialog):
        super().__init__(view_dialog.parent)
        self.view_dialog = view_dialog
        self.header_label = None
        
        self._setup_ui()
        self.refresh_table()
    
    def _setup_ui(self):
        """UI-Setup"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Titel mit ExpertMode-spezifischen Ergänzungen
        title_text = self._get_title_text()
        self.header_label = QLabel(title_text)
        header_font = QFont("Segoe UI", 12, QFont.Bold)
        self.header_label.setFont(header_font)
        header_layout.addWidget(self.header_label)
        
        header_layout.addStretch()
        
        # Settings-Button mit Dropdown-Menü
        self.settings_button = QToolButton()
        self.settings_button.setText("⚙️")
        self.settings_button.setToolTip("Einstellungen")
        self.settings_button.setPopupMode(QToolButton.InstantPopup)
        
        # Menü erstellen
        self._create_settings_menu()
        
        header_layout.addWidget(self.settings_button)
        
        layout.addLayout(header_layout)
        
        # Suchbereich - DEUTLICH SICHTBAR
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Box)
        search_frame.setLineWidth(1)
        search_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border: 1px solid #ccc; }")
        
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 8, 10, 8)
        
        search_label = QLabel("🔍 Gesamtsuche:")
        search_label.setMinimumWidth(100)
        search_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche in allen angezeigten Spalten...")
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setVisible(True)  # Explizit sichtbar machen
        self.search_input.setMinimumHeight(25)  # Mindesthöhe setzen
        search_layout.addWidget(self.search_input)
        
        # Negativ-Suche Toggle Button
        self.negative_search_button = QPushButton("➕")
        self.negative_search_button.setFixedSize(30, 25)
        self.negative_search_button.setToolTip("Normale Suche (einschließen)\nKlicken für Negativ-Suche (ausschließen)")
        self.negative_search_button.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                border: none; 
                border-radius: 3px; 
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #45a049; 
            }
        """)
        self.negative_search_button.clicked.connect(self._toggle_negative_search)
        self.is_negative_search = False  # Status der Negativ-Suche
        search_layout.addWidget(self.negative_search_button)
        
        # Filter löschen Button
        self.clear_filters_button = QPushButton("🗑️")
        self.clear_filters_button.setFixedSize(30, 25)
        self.clear_filters_button.setToolTip("Alle Filter löschen\n(Gesamtsuche und Spaltenfilter)")
        self.clear_filters_button.setStyleSheet("""
            QPushButton { 
                background-color: #ff9800; 
                color: white; 
                border: none; 
                border-radius: 3px; 
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { 
                background-color: #f57c00; 
            }
        """)
        self.clear_filters_button.clicked.connect(self.view_dialog.clear_all_filters)
        search_layout.addWidget(self.clear_filters_button)
        
        # Suchstatus
        self.search_status = QLabel()
        self.search_status.setMinimumWidth(150)
        self.search_status.setFont(QFont("Segoe UI", 8))
        search_layout.addWidget(self.search_status)
        
        layout.addWidget(search_frame)  # Frame statt Layout hinzufügen
        
        # DEBUG: Suchfeld-Sichtbarkeit loggen
        logger.info(f"🔍 DEBUG: Suchfeld erstellt - Sichtbar: {self.search_input.isVisible()}, Höhe: {self.search_input.height()}")
        logger.info(f"🔍 DEBUG: Suchframe erstellt - Sichtbar: {search_frame.isVisible()}, Höhe: {search_frame.height()}")
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Header-Schrift konfigurieren
        header_font = QFont("Segoe UI", 10, QFont.Bold)
        self.table.horizontalHeader().setFont(header_font)
        
        layout.addWidget(self.table)
        
        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
    
    def _get_title_text(self):
        """Titel-Text mit ExpertMode-spezifischen Ergänzungen - LINEAR"""
        try:
            from pdvm_central_systemsteuerung import get_gcs

            base_title = self.view_dialog.title

            # LINEAR: GCS immer verfügbar machen
            # GCS direkt verwenden
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar für Titel-Text")
                return base_title

            # Im ExpertMode: Stichtag hinzufügen - FORMATIERT!
            if gcs.expert_mode and hasattr(gcs, 'st_inst') and gcs.st_inst:
                # VERWENDE FormTimeStamp für formatierte Anzeige!
                formatted_stichtag = getattr(gcs.st_inst, 'FormTimeStamp', str(gcs.st_inst.PdvmDateTime))
                return f"{base_title} - Stichtag: {formatted_stichtag}"

            return base_title

        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Erstellen des Titel-Texts: {e}")
            return self.view_dialog.title
    
    def refresh_table(self):
        """Tabelle aktualisieren - LINEARES FILTER-SYSTEM: Nur Zeilen mit display=True anzeigen"""
        matrix = self.view_dialog.display_matrix
        
        if not matrix:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.status_label.setText("Keine Daten")
            return
        
        # LINEARES FILTER-SYSTEM: Nur Zeilen mit display=True filtern
        visible_rows = [row for row in matrix if row.get('display', True)]
        
        # Sichtbare Spalten direkt aus GCS holen (NEUE ARCHITEKTUR)
        visible_columns = self._get_visible_columns_from_gcs()

        # Tabelle füllen mit gefilterten Zeilen
        self.table.setRowCount(len(visible_rows))
        self.table.setColumnCount(len(visible_columns))

        # Header
        headers = []
        tooltips = []
        # GCS direkt verwenden  # LINEAR: GCS einmal holen
        for col in visible_columns:
            control = self.view_dialog.controls_config.get(col, {})
            base_name = control.get('name', col)
            
            # Original-Kennzeichnung hinzufügen
            if control.get('control_type') == 'original':
                header_text = f"{base_name} (Orig.)"
            else:
                header_text = base_name
            
            # Im ExpertMode: Control-Key in zweiter Zeile hinzufügen
            if gcs and gcs.expert_mode:
                header_text += f"\n{col}"
            
            headers.append(header_text)
            
            # ToolTip für vollständigen Text erstellen
            tooltip_text = base_name
            if gcs and gcs.expert_mode:
                tooltip_text += f"\nControl-Key: {col}"
            if control.get('control_type'):
                tooltip_text += f"\nTyp: {control.get('control_type')}"
            tooltips.append(tooltip_text)
        
        self.table.setHorizontalHeaderLabels(headers)
        
        # ToolTips für Header setzen
        for i, tooltip in enumerate(tooltips):
            self.table.horizontalHeaderItem(i).setToolTip(tooltip)
        
        # Daten - LINEARES FILTER: visible_rows verwenden statt matrix
        for row_idx, row_data in enumerate(visible_rows):
            for col_idx, col_name in enumerate(visible_columns):
                value = row_data.get(col_name, '')
                
                # ToolTip für erweiterte Informationen erstellen
                control = self.view_dialog.controls_config.get(col_name, {})
                control_type = control.get('control_type', '')
                
                # Abdatum aus der gleichen Ebene wie der Wert holen (bereits formatiert)
                abdatum_value = None
                # DIREKT aus der Matrix: formatiertes Abdatum verwenden
                abdatum_value = row_data.get(f"{col_name}_formatiertes_abdatum")
                
                # FALLBACK: Wenn nicht formatiert, dann direkt formatieren
                if abdatum_value is None or (isinstance(abdatum_value, str) and abdatum_value.replace('.', '').isdigit()):
                    # Versuche das rohe Abdatum zu holen und zu formatieren
                    raw_abdatum = row_data.get(f"{col_name}_abdatum")
                    if raw_abdatum is not None:
                        try:
                            formatted_abdatum = self.view_dialog._format_abdatum(raw_abdatum)
                            abdatum_value = formatted_abdatum
                            logger.info(f"🔧 FALLBACK-Formatierung: {raw_abdatum} → {formatted_abdatum}")
                        except Exception as e:
                            logger.warning(f"⚠️ FALLBACK-Formatierung fehlgeschlagen: {e}")
                            abdatum_value = f"{raw_abdatum} (Formatierungsfehler)"
                
                # DEBUG: Prüfe was aus der Matrix gelesen wird
#                logger.info(f"    🔍 DEBUG Tooltip-Lesen: col_name='{col_name}', key='{col_name}_formatiertes_abdatum', value='{abdatum_value}', type={type(abdatum_value)}")
#                if abdatum_value:
#                    logger.info(f"    🔍 DEBUG Tooltip-Details: Länge={len(str(abdatum_value))}, Inhalt='{str(abdatum_value)[:50]}...'")
                
                item = QTableWidgetItem(str(value) if value is not None else "")
                
                # Erweiterte ToolTip erstellen - LINEAR aus Matrix-Daten
                tooltip_parts = []
                
                # Aktueller Wert (Ebene 1)
                if value is not None and str(value).strip():
                    tooltip_parts.append(f"Wert: {value}")
                else:
                    tooltip_parts.append("Wert: (leer)")
                
                # Abdatum aus Ebene 3 (bereits formatiert)
                if abdatum_value:
                    tooltip_parts.append(f"Abdatum: {abdatum_value}")
                else:
                    tooltip_parts.append("Abdatum: (nicht verfügbar)")
                
                # Zusätzliche Informationen im ExpertMode
                if gcs and gcs.expert_mode:
                    tooltip_parts.append(f"Control-Key: {col_name}")
                    if control_type:
                        tooltip_parts.append(f"Typ: {control_type}")
                    if control.get('feld'):
                        tooltip_parts.append(f"Feld: {control.get('feld')}")
                    if control.get('gruppe'):
                        tooltip_parts.append(f"Gruppe: {control.get('gruppe')}")
                
                # ToolTip setzen
                if tooltip_parts:
                    item.setToolTip("\n".join(tooltip_parts))
                
                self.table.setItem(row_idx, col_idx, item)
        
        # Status mit Modus-Anzeige - GCS direkt verwenden (keine Fallbacks nötig)
        mode_text = "Experten Modus" if gcs.expert_mode else "Standard Modus"
        # Status-Text mit Filter-Information
        total_rows = len(matrix)
        visible_count = len(visible_rows)
        
        if visible_count == total_rows:
            status_text = f"{total_rows} Datensätze, {len(visible_columns)} Spalten"
        else:
            status_text = f"{visible_count} von {total_rows} Datensätzen gefiltert, {len(visible_columns)} Spalten"

        # Layout für Status-Zeile mit rechts ausgerichtetem Modus
        self.status_label.setText(f"{status_text} - {mode_text}")
        self.status_label.setStyleSheet("QLabel { color: #666666; }")
    
    def _get_visible_columns_from_gcs(self):
        """Sichtbare Spalten direkt aus GCS-Projektion laden (NEUE EINFACHE ARCHITEKTUR)"""
        try:
            # View-GUID für Projektion
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                logger.error("❌ Keine View-GUID verfügbar für Tabelle")
                return []

            # GCS direkt verwenden - berücksichtigt automatisch Standard/Expert Mode
            if not gcs:
                logger.error("❌ GCS nicht verfügbar")
                return []
                
            # STATISCHE PROJEKTION aus GCS - je nach Expert Mode
            if gcs.expert_mode:
                projection = gcs.get_projection_table(view_guid, 'table_expert')
            else:
                projection = gcs.get_projection_table(view_guid, 'table_standard')
            if projection:
                mode_info = "Expert" if gcs.expert_mode else "Standard"
                logger.debug(f"✅ Tabellen-Projektion ({mode_info}) live berechnet: {len(projection)} Spalten")
                return projection
            else:
                logger.warning(f"⚠️ Keine Tabellen-Projektion verfügbar für View {view_guid}")
                return []

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Tabellen-Projektion aus GCS: {e}")
            return []
    
    def _on_search_changed(self):
        """Event-Handler für Suchfeld-Änderungen - LINEARES FILTER-SYSTEM"""
        search_text = self.search_input.text().strip()
        
        # Zentrale Filter-Methode verwenden
        if hasattr(self, 'view_dialog') and self.view_dialog:
            self.view_dialog.apply_filter_string(search_text)
            logger.info(f"🔍 Einfache Suche angewendet: '{search_text}'")
    
    def _show_all_rows(self):
        """Zeige alle Tabellenzeilen"""
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
    
    def _perform_search(self, search_text):
        """Führe Suche in allen angezeigten Spalten durch - unterstützt Normal- und Negativ-Suche"""
        if not search_text:
            self._show_all_rows()
            return
        
        search_text_lower = search_text.lower()
        visible_count = 0
        total_count = self.table.rowCount()
        
        # Durchsuche alle Zeilen
        for row in range(total_count):
            contains_text = False
            
            # Durchsuche alle Spalten in dieser Zeile
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    cell_text = item.text().lower()
                    if search_text_lower in cell_text:
                        contains_text = True
                        break
            
            # Zeile basierend auf Suchmodus anzeigen/verstecken
            if self.is_negative_search:
                # Negativ-Suche: Zeile verstecken wenn Text gefunden
                show_row = not contains_text
            else:
                # Normal-Suche: Zeile anzeigen wenn Text gefunden
                show_row = contains_text
            
            self.table.setRowHidden(row, not show_row)
            if show_row:
                visible_count += 1
        
        # Suchstatus aktualisieren
        mode_text = "ausgeschlossen" if self.is_negative_search else "gefunden"
        
        if visible_count == 0:
            if self.is_negative_search:
                self.search_status.setText(f"⚠️ Alle Zeilen enthalten '{search_text}'")
            else:
                self.search_status.setText(f"⚠️ Keine Treffer")
            self.search_status.setStyleSheet("QLabel { color: #d32f2f; }")
        else:
            if self.is_negative_search:
                self.search_status.setText(f"➖ {visible_count} von {total_count} ('{search_text}' ausgeschlossen)")
            else:
                self.search_status.setText(f"✅ {visible_count} von {total_count}")
            self.search_status.setStyleSheet("QLabel { color: #388e3c; }")
    
    def clear_search(self):
        """Öffentliche Methode zum Löschen der Suche"""
        self.search_input.clear()
        self._show_all_rows()
        self.search_status.setText("")
        self.search_status.setStyleSheet("")
        
        # Button auf Normal-Suche zurücksetzen
        if self.is_negative_search:
            self.is_negative_search = False
            self.negative_search_button.setText("➕")
            self.negative_search_button.setToolTip("Normale Suche (einschließen)\nKlicken für Negativ-Suche (ausschließen)")
            self.negative_search_button.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    border: none; 
                    border-radius: 3px; 
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background-color: #45a049; 
                }
            """)
            self.search_input.setPlaceholderText("Suche in allen angezeigten Spalten...")
    
    def _toggle_negative_search(self):
        """Toggle zwischen Normal- und Negativ-Suche"""
        self.is_negative_search = not self.is_negative_search
        
        if self.is_negative_search:
            # Negativ-Suche aktiviert
            self.negative_search_button.setText("➖")
            self.negative_search_button.setToolTip("Negativ-Suche (ausschließen)\nKlicken für normale Suche (einschließen)")
            self.negative_search_button.setStyleSheet("""
                QPushButton { 
                    background-color: #f44336; 
                    color: white; 
                    border: none; 
                    border-radius: 3px; 
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background-color: #da190b; 
                }
            """)
            self.search_input.setPlaceholderText("Ausschließen aus allen angezeigten Spalten...")
        else:
            # Normal-Suche aktiviert
            self.negative_search_button.setText("➕")
            self.negative_search_button.setToolTip("Normale Suche (einschließen)\nKlicken für Negativ-Suche (ausschließen)")
            self.negative_search_button.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    border: none; 
                    border-radius: 3px; 
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { 
                    background-color: #45a049; 
                }
            """)
            self.search_input.setPlaceholderText("Suche in allen angezeigten Spalten...")
        
        # Suche neu durchführen mit neuem Modus
        current_text = self.search_input.text().strip()
        if current_text:
            self._perform_search(current_text)
    
    def _create_settings_menu(self):
        """Erstelle Settings-Dropdown-Menü - LINEAR"""
        try:
            settings_menu = QMenu(self)

            # Debug: Prüfe ob Methoden in self existieren (nicht in self.view_dialog)
            logger.info(f"🔍 Debug: self.view_dialog = {self.view_dialog}")
            logger.info(f"🔍 Debug: hasattr _spalten_verwaltung (self) = {hasattr(self, '_spalten_verwaltung')}")
            logger.info(f"🔍 Debug: hasattr _suchparameter_verwaltung (self) = {hasattr(self, '_suchparameter_verwaltung')}")

            # 1. Verwaltung der Spalten (in self, nicht in self.view_dialog!)
            action_spalten = QAction("Verwaltung der Spalten", self)
            action_spalten.triggered.connect(self._spalten_verwaltung)
            settings_menu.addAction(action_spalten)

            # 2. Suchparameter verwalten (in self, nicht in self.view_dialog!)
            action_search = QAction("Suchparameter verwalten", self)
            action_search.triggered.connect(self._suchparameter_verwaltung)
            settings_menu.addAction(action_search)

            # 2. ExpertMode (nur für Admins) - LINEAR
            # GCS direkt verwenden
            if gcs and gcs.is_admin:
                settings_menu.addSeparator()

                # ExpertMode Toggle (in self, nicht in self.view_dialog!)
                expert_text = "ExpertMode (ausschalten)" if gcs.expert_mode else "ExpertMode (einschalten)"
                action_expert = QAction(expert_text, self)
                action_expert.triggered.connect(self._toggle_expert_mode)
                settings_menu.addAction(action_expert)

            # 3. Zurücksetzen
            settings_menu.addSeparator()
            action_reset = QAction("Zurücksetzen", self)
            action_reset.triggered.connect(self._reset_view)
            settings_menu.addAction(action_reset)

            # Menü am Button setzen
            self.settings_button.setMenu(settings_menu)

            logger.info("✅ Settings-Menü erstellt")

        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Settings-Menüs: {e}")
    
    def _spalten_verwaltung(self):
        """Spalten-Verwaltung mit neuen Modal-Dialogen öffnen"""
        try:
            from column_management_dialog import show_column_management_dialog
            
            # View-GUID für Projektion
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                QMessageBox.warning(self, "Fehler", "Keine View-GUID verfügbar für Spaltenverwaltung")
                return
                
            # Controls direkt vom Dialog übergeben
            controls_config = getattr(self.view_dialog, 'controls_config', {})
            if not controls_config:
                QMessageBox.warning(self, "Fehler", "Keine Controls-Konfiguration verfügbar")
                return
                
            # Modal-Dialog öffnen mit controls_config direkt
            result = show_column_management_dialog(self, view_guid, controls_config, "table")
            
            if result:
                # Bei Änderung -> Tabelle und Filter-Panel aktualisieren
                self.refresh_table()
                
                # Filter-Panel aktualisieren falls vorhanden
                if hasattr(self, 'filter_panel') and self.filter_panel:
                    self.filter_panel.refresh_column_search_fields()
                    logger.info("✅ Filter-Panel nach Spaltenverwaltung aktualisiert")
                
                logger.info("✅ Spaltenverwaltung abgeschlossen, Tabelle und Filter-Panel aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Verwaltung: {e}")
            QMessageBox.warning(self, "Fehler", f"Spalten-Verwaltung Fehler:\n{e}")
    
    def _suchparameter_verwaltung(self):
        """Suchparameter-Verwaltung mit neuen Modal-Dialogen öffnen"""
        try:
            from search_parameter_dialog import SearchParameterDialog
            
            # View-GUID für Projektion
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                QMessageBox.warning(self, "Fehler", "Keine View-GUID verfügbar für Suchparameter")
                return
                
            # Aktuelle Filter aus Filter-Panel holen (falls vorhanden)
            current_filters = {}
            if hasattr(self, 'filter_panel') and self.filter_panel:
                current_filters = self.filter_panel.get_current_filters()
            
            # Modal-Dialog öffnen mit controls_config direkt übergeben
            dialog = SearchParameterDialog(self, view_guid, self.view_dialog.controls_config, current_filters)
            
            # PUNKT 3: Gesamtsuche-Feld leeren BEVOR Dialog geöffnet wird
            if hasattr(self, 'search_field') and self.search_field:
                logger.info("✅ Gesamtsuche verzögert geleert da Spaltenfilter aktiv")
                self.search_field.clear()  # Feld sofort leeren
            
            result = dialog.exec_()
            
            if result == QDialog.Accepted and dialog.was_accepted:
                # Dialog wurde mit OK geschlossen
                filter_string = dialog.result_filter_string
                logger.info(f"🎯 SearchParameter-Dialog: Filterstring empfangen: '{filter_string}'")
                
                # DEBUG: Überprüfen ob Filterstring leer ist
                if not filter_string or filter_string.strip() == "":
                    logger.warning("⚠️ PROBLEM: Filterstring ist leer beim ersten Mal!")
                    logger.info("🔍 DEBUG: Versuche Filter direkt vom Dialog zu holen...")
                    
                    # Versuche Filter direkt vom Dialog zu holen
                    if hasattr(dialog, 'get_filter_conditions'):
                        conditions = dialog.get_filter_conditions()
                        logger.info(f"🔍 DEBUG: Dialog-Bedingungen: {conditions}")
                    
                    # Versuche auch den Filter direkt zu rekonstruieren
                    if hasattr(dialog, 'build_filter_string'):
                        reconstructed_filter = dialog.build_filter_string()
                        logger.info(f"🔍 DEBUG: Rekonstruierter Filter: {reconstructed_filter}")
                        if reconstructed_filter:
                            filter_string = reconstructed_filter
                            logger.info("✅ Filter rekonstruiert!")
                
                # NEUE LINEARE ARCHITEKTUR: Direkt die zentrale Filter-Methode verwenden
                if filter_string and filter_string.strip():
                    self.view_dialog.apply_filter_string(filter_string)
                    logger.info("✅ Filter angewendet")
                else:
                    logger.error("❌ FEHLER: Kein gültiger Filterstring zum Anwenden!")
                
                # Referenz auf Dialog für spätere Filterstring-Abfragen speichern
                self.search_dialog = dialog
                
                logger.info("✅ Suchparameter-Verwaltung abgeschlossen")
            else:
                logger.info("ℹ️ Suchparameter-Dialog abgebrochen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Suchparameter-Verwaltung: {e}")
            QMessageBox.warning(self, "Fehler", f"Suchparameter-Verwaltung Fehler:\n{e}")
    
    def _toggle_expert_mode(self):
        """ExpertMode ein/aus schalten - LINEAR"""
        try:
            # GCS direkt verwenden
            if not gcs:
                QMessageBox.warning(self, "Fehler", "Systemsteuerung nicht verfügbar")
                return

            new_mode = not gcs.expert_mode
            gcs.expert_mode = new_mode

            # Menü neu erstellen um Text zu aktualisieren
            self._create_settings_menu()

            # Titel aktualisieren (wegen Stichtag im ExpertMode)
            self.header_label.setText(self._get_title_text())

            # Tabelle aktualisieren (wegen geänderten sichtbaren Spalten)
            self.refresh_table()

            # Filter-Panel aktualisieren (wegen geänderten projizierten Spalten)
            if hasattr(self, 'filter_panel') and self.filter_panel:
                self.filter_panel.refresh_column_search_fields()
                logger.info("✅ Filter-Panel nach Moduswechsel aktualisiert")

            mode_text = "aktiviert" if new_mode else "deaktiviert"
            logger.info(f"✅ ExpertMode {mode_text}: {new_mode}")

        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des ExpertModus: {e}")
            QMessageBox.warning(self, "Fehler", f"ExpertMode konnte nicht umgeschaltet werden:\n{e}")
    
    def _toggle_filter_panel(self):
        """Filter-Panel ein/aus blenden"""
        try:
            if not hasattr(self, 'filter_panel'):
                # Filter-Panel erstellen
                self.filter_panel = PdvmFilterPanel(self.view_dialog, self)

                # Panel in Hauptlayout integrieren
                main_layout = self.layout()

                if main_layout and isinstance(main_layout, QVBoxLayout):
                    # Layout-Struktur neu aufbauen
                    # 1. Header-Layout finden (bleibt oben)
                    header_layout = None
                    table_widget = None
                    status_label = None

                    # Widgets im aktuellen Layout identifizieren
                    for i in range(main_layout.count()):
                        item = main_layout.itemAt(i)
                        if item:
                            if item.layout():  # Header-Layout (QHBoxLayout)
                                header_layout = item.layout()
                            elif item.widget():
                                widget = item.widget()
                                if hasattr(widget, 'setAlternatingRowColors'):  # QTableWidget
                                    table_widget = widget
                                elif isinstance(widget, QLabel) and widget != self.header_label:
                                    status_label = widget

                    if table_widget:
                        # Layout komplett neu strukturieren
                        # Temporär alle Items entfernen
                        items_to_restore = []
                        while main_layout.count() > 0:
                            item = main_layout.takeAt(0)
                            if item.layout():
                                items_to_restore.append(('layout', item.layout()))
                            elif item.widget():
                                items_to_restore.append(('widget', item.widget()))

                        # Layout neu aufbauen
                        # 1. Header-Layout wieder hinzufügen
                        for item_type, item in items_to_restore:
                            if item_type == 'layout' and item == header_layout:
                                main_layout.addLayout(item)
                                break

                        # 2. Content-Bereich (Filter-Panel + Tabelle)
                        content_layout = QHBoxLayout()

                        # Filter-Panel links hinzufügen
                        self.filter_panel.setMaximumWidth(350)
                        self.filter_panel.setMinimumWidth(300)
                        content_layout.addWidget(self.filter_panel)

                        # Tabelle rechts hinzufügen (nimmt restlichen Platz)
                        content_layout.addWidget(table_widget, 1)

                        main_layout.addLayout(content_layout)

                        # 3. Status-Label wieder hinzufügen
                        for item_type, item in items_to_restore:
                            if item_type == 'widget' and item == status_label:
                                main_layout.addWidget(item)
                                break

                        logger.info("✅ Filter-Panel in Layout integriert - Header bleibt oben")

            # Panel ein-/ausblenden
            if self.filter_panel.isVisible():
                self.filter_panel.hide()
                logger.info("ℹ️ Filter-Panel ausgeblendet")
            else:
                self.filter_panel.show()
                logger.info("ℹ️ Filter-Panel eingeblendet")

        except Exception as e:
            logger.error(f"❌ Fehler beim Filter-Panel Toggle: {e}")
            QMessageBox.warning(self, "Fehler", f"Filter-Panel Fehler:\n{e}")
    
    def _reset_view(self):
        """View zurücksetzen - komplett neu initialisieren"""
        try:
            # Sicherheitsabfrage
            reply = QMessageBox.question(self, "Zurücksetzen bestätigen", 
                                       "Möchten Sie die View-Einstellungen wirklich zurücksetzen?\n\n"
                                       "Alle benutzerdefinierten Spalten-Einstellungen gehen verloren.",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply != QMessageBox.Yes:
                logger.info("ℹ️ View-Reset abgebrochen")
                return
            
            logger.info(f"🔄 Starte View-Reset für {self.view_dialog.view_guid}")
            
            # call_daten für Reset vorbereiten - mit reset=True (eleganter Ansatz!)
            reset_call_daten = self.view_dialog.call_daten.copy()
            reset_call_daten['reset'] = True  # Reset-Flag setzen
            # first_call kann False bleiben - reset überspringt Schritt 4
            
            # Neue PdvmViewDialog Instanz erstellen (überspringt Schritt 4: Synchronisation)
            from pdvm_view_dialog import PdvmViewDialog
            new_dialog = PdvmViewDialog(reset_call_daten, self.view_dialog.parent)
            
            # Aktuelles view_dialog mit Standard-Controls aktualisieren
            self.view_dialog.controls_config = new_dialog.controls_config.copy()
            self.view_dialog.display_matrix = new_dialog.display_matrix
            
            # Original-Matrix für Filter zurücksetzen (wichtig für korrekte Filterung)
            if hasattr(self.view_dialog, 'original_matrix'):
                self.view_dialog.original_matrix = self.view_dialog.display_matrix.copy()
            
            # Filter-Panel zurücksetzen falls vorhanden
            if hasattr(self, 'filter_panel') and self.filter_panel:
                self.filter_panel._reset_search_filters()
                logger.info("✅ Filter-Panel beim View-Reset zurückgesetzt")
            
            # Titel aktualisieren (falls ExpertMode aktiv)
            self.header_label.setText(self._get_title_text())
            
            # Tabelle komplett neu aufbauen
            self.refresh_table()
            
            logger.info("✅ View erfolgreich zurückgesetzt - Standard-Controls persistent gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim View-Reset: {e}")
            QMessageBox.critical(self, "Fehler", f"View konnte nicht zurückgesetzt werden:\n{e}")
    
    def _clear_all_filters(self):
        """PUNKT 4: Alle Filter löschen - alle Zeilen auf display=True und Gesamtsuche leeren"""
        try:
            logger.info("🗑️ Alle Filter werden zurückgesetzt...")
            
            # 1. Alle Matrix-Zeilen auf display=True setzen
            if hasattr(self.view_dialog, 'display_matrix') and self.view_dialog.display_matrix:
                for row in self.view_dialog.display_matrix:
                    row['display'] = True
                logger.info(f"✅ {len(self.view_dialog.display_matrix)} Zeilen auf sichtbar gesetzt")
            
            # 2. Gesamtsuche-Feld leeren (falls vorhanden)
            if hasattr(self, 'search_field') and self.search_field:
                self.search_field.clear()
                logger.info("✅ Gesamtsuche-Feld geleert")
            
            # 3. Normales Suchfeld leeren
            if hasattr(self, 'search_input') and self.search_input:
                self.search_input.clear()
                logger.info("✅ Suchfeld geleert")
            
            # 4. Tabelle sofort aktualisieren
            self.refresh_table()
            
            # 5. Status-Update
            visible_count = len(self.view_dialog.display_matrix) if hasattr(self.view_dialog, 'display_matrix') else 0
            logger.info(f"✅ Alle Filter zurückgesetzt - {visible_count} Datensätze sichtbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen aller Filter: {e}")
    
    def apply_column_filters(self, filters):
        """
        DEAKTIVIERT: Alte Spaltenfilter-Methode - jetzt einheitlicher Filterstring
        """
        logger.info("⚠️ apply_column_filters DEAKTIVIERT - verwende einheitlichen Filterstring")
        return


class PdvmFilterPanel(QWidget):
    """
    Filter-Panel für View-Dialog mit umfassender Suchfunktionalität

    Features:
    - Suchmodi: Groß-/Kleinschreibung, ganzes Wort, Wortteile
    - Globales Suchfeld für alle searchable Spalten
    - Spalten-spezifische Suchfelder
    - Stellvertreterzeichen-Unterstützung
    - Positive/negative Suche
    - Persistente Filter-Einstellungen
    """

    def __init__(self, view_dialog, parent=None):
        super().__init__(parent)
        self.view_dialog = view_dialog
        self.filter_active = False

        # Filter-Einstellungen laden
        self._load_filter_settings()

        # UI erstellen
        self._setup_ui()

        logger.info("✅ Filter-Panel initialisiert")

    def _setup_ui(self):
        """Erstellt die Filter-UI"""
        # Hauptlayout für das Panel
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_label = QLabel("🔍 Filter & Suche")
        header_font = QFont("Segoe UI", 11, QFont.Bold)
        header_label.setFont(header_font)
        main_layout.addWidget(header_label)
        
        # Scroll-Bereich für den Filter-Inhalt
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumWidth(280)
        scroll_area.setMaximumWidth(340)
        
        # Container-Widget für den scrollbaren Inhalt
        scroll_widget = QWidget()
        content_layout = QVBoxLayout(scroll_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # Suchmodi-Gruppe
        search_modes_group = QGroupBox("Suchmodi")
        search_modes_layout = QVBoxLayout(search_modes_group)
        
        # Groß-/Kleinschreibung
        self.case_sensitive_radio = QRadioButton("Groß-/Kleinschreibung beachten")
        self.case_insensitive_radio = QRadioButton("Groß-/Kleinschreibung ignorieren")
        self.case_insensitive_radio.setChecked(True)  # Standard
        
        case_group = QButtonGroup(self)
        case_group.addButton(self.case_sensitive_radio)
        case_group.addButton(self.case_insensitive_radio)
        
        search_modes_layout.addWidget(self.case_sensitive_radio)
        search_modes_layout.addWidget(self.case_insensitive_radio)
        
        # Wort-Modi
        self.whole_word_radio = QRadioButton("Ganzes Wort")
        self.word_parts_radio = QRadioButton("Wortteile")
        self.word_parts_radio.setChecked(True)  # Standard
        
        word_group = QButtonGroup(self)
        word_group.addButton(self.whole_word_radio)
        word_group.addButton(self.word_parts_radio)
        
        search_modes_layout.addWidget(self.whole_word_radio)
        search_modes_layout.addWidget(self.word_parts_radio)
        
        content_layout.addWidget(search_modes_group)
        
        # Globales Suchfeld
        global_search_group = QGroupBox("Globale Suche")
        global_search_layout = QVBoxLayout(global_search_group)
        
        self.global_search_edit = QLineEdit()
        self.global_search_edit.setPlaceholderText("Suche in allen Spalten...")
        self.global_search_edit.textChanged.connect(self._on_global_search_changed)
        
        # Positive/Negative Toggle
        global_controls_layout = QHBoxLayout()
        self.global_negative_checkbox = QCheckBox("Negativ")
        self.global_negative_checkbox.setToolTip("Negative Suche: Zeilen ausschließen die den Suchtext enthalten")
        
        global_controls_layout.addWidget(self.global_negative_checkbox)
        global_controls_layout.addStretch()
        
        global_search_layout.addWidget(self.global_search_edit)
        global_search_layout.addLayout(global_controls_layout)
        
        content_layout.addWidget(global_search_group)
        
        # Spalten-spezifische Suchfelder
        self._create_column_search_fields(content_layout)
        
        # Original-Matrix für Filterung initialisieren
        if hasattr(self.view_dialog, 'display_matrix') and self.view_dialog.display_matrix:
            self.view_dialog.original_matrix = self.view_dialog.display_matrix.copy()
            logger.info("💾 Original-Matrix für Filterung initialisiert")
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("✅ Anwenden")
        self.apply_button.clicked.connect(self._apply_filters)
        
        self.cancel_button = QPushButton("❌ Abbrechen")
        self.cancel_button.clicked.connect(self._cancel_filters)
        
        self.reset_button = QPushButton("🔄 Zurücksetzen")
        self.reset_button.clicked.connect(self._reset_filters)
        
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.reset_button)
        
        content_layout.addLayout(buttons_layout)
        
        # Stretch am Ende für besseres Layout
        content_layout.addStretch()
        
        # Scroll-Bereich konfigurieren
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # SUCHFELDER NACH ERSTELLUNG AKTUALISIEREN (wichtig für korrekte Anzeige)
        self.refresh_column_search_fields()
        logger.info("✅ Suchfelder nach UI-Erstellung aktualisiert")
    
    def refresh_column_search_fields(self):
        """Aktualisiert die Suchfelder für Spalten - wird aufgerufen wenn sich Spalten ändern"""
        try:
            logger.info("🔄 Aktualisiere Suchfelder für Spalten...")
            
            # SCHRITT 1: Basis-Columns des View-Dialogs aktualisieren
            if hasattr(self.view_dialog, '_get_columns_from_controls'):
                old_basis_columns = getattr(self.view_dialog, 'basis_columns', [])
                self.view_dialog.basis_columns = self.view_dialog._get_columns_from_controls()
                
                # Prüfe ob sich die Basis-Columns geändert haben
                if len(old_basis_columns) != len(self.view_dialog.basis_columns):
                    logger.info(f"✅ Basis-Columns des View-Dialogs aktualisiert: {len(old_basis_columns)} → {len(self.view_dialog.basis_columns)} Spalten")
                elif old_basis_columns != self.view_dialog.basis_columns:
                    logger.info(f"✅ Basis-Columns des View-Dialogs geändert")
            
            # SCHRITT 2: Original-Matrix aktualisieren (für korrekte Filterung nach Spalten-Änderungen)
            if hasattr(self.view_dialog, 'display_matrix') and self.view_dialog.display_matrix:
                self.view_dialog.original_matrix = self.view_dialog.display_matrix.copy()
                logger.info("✅ Original-Matrix für Filterung aktualisiert")
            
            # Finde den Spalten-Suchbereich im Layout
            scroll_widget = None
            content_layout = None
            column_search_group = None
            
            # Durchsuche das Layout nach dem Spalten-Suchbereich
            if hasattr(self, 'layout') and self.layout():
                main_layout = self.layout()
                if isinstance(main_layout, QVBoxLayout):
                    # Finde den Scroll-Bereich
                    for i in range(main_layout.count()):
                        item = main_layout.itemAt(i)
                        if item and item.widget() and isinstance(item.widget(), QScrollArea):
                            scroll_widget = item.widget()
                            break
            
            if scroll_widget and scroll_widget.widget():
                content_widget = scroll_widget.widget()
                if hasattr(content_widget, 'layout') and content_widget.layout():
                    content_layout = content_widget.layout()
                    
                    # Finde den Spalten-Suchbereich
                    for i in range(content_layout.count()):
                        item = content_layout.itemAt(i)
                        if item and item.layout():
                            layout = item.layout()
                            # Prüfe ob es der Spalten-Suchbereich ist
                            for j in range(layout.count()):
                                sub_item = layout.itemAt(j)
                                if sub_item and sub_item.widget():
                                    widget = sub_item.widget()
                                    if isinstance(widget, QGroupBox) and "Spalten-spezifische Suche" in widget.title():
                                        column_search_group = widget
                                        break
                            if column_search_group:
                                break
            
            if column_search_group and hasattr(column_search_group, 'layout'):
                column_layout = column_search_group.layout()
                
                # Entferne alle alten Suchfelder
                while column_layout.count() > 0:
                    item = column_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                    elif item.layout():
                        # Rekursiv Layouts entfernen
                        sub_layout = item.layout()
                        while sub_layout.count() > 0:
                            sub_item = sub_layout.takeAt(0)
                            if sub_item.widget():
                                sub_item.widget().deleteLater()
                
                # Leere das Suchfelder-Dictionary
                self.column_search_fields.clear()
                
                # Erstelle neue Suchfelder
                self._create_column_search_fields(column_layout.parent())
                
                logger.info("✅ Suchfelder für Spalten aktualisiert")
                
                # Erzwinge Layout-Update
                self.update()
                if scroll_widget:
                    scroll_widget.update()
                    
            else:
                logger.warning("⚠️ Konnte Spalten-Suchbereich nicht finden für Aktualisierung")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Suchfelder: {e}")

    def _create_column_search_fields(self, parent_layout):
        """Erstellt Suchfelder für jede searchable Spalte - 1:1 wie in der Tabelle projiziert"""
        column_search_group = QGroupBox("Spalten-spezifische Suche")
        column_search_layout = QVBoxLayout(column_search_group)

        self.column_search_fields = {}

        # Spalten 1:1 aus der aktuellen Tabellen-Projektion ermitteln
        table_columns = self._get_table_projection_columns()

        # Alle Spalten aus der Tabellen-Projektion verwenden
        all_columns = []
        for field_name in table_columns:
            field_config = self.view_dialog.controls_config.get(field_name, {})
            display_name = field_config.get('name', field_name)
            # Eine Spalte ist suchbar, wenn sie das searchable Attribut hat
            # Ganz linear: searchable = true → suchbar, egal ob _show oder _original
            is_searchable = field_config.get('searchable', False)
            all_columns.append((field_name, display_name, is_searchable))

        if not all_columns:
            no_search_label = QLabel("Keine Spalten verfügbar")
            no_search_label.setStyleSheet("color: #666; font-style: italic;")
            column_search_layout.addWidget(no_search_label)
        else:
            for field_name, display_name, is_searchable in all_columns:
                # Container für jedes Suchfeld
                field_layout = QHBoxLayout()

                # Label
                label = QLabel(f"{display_name}:")
                label.setMinimumWidth(100)
                if not is_searchable:
                    label.setStyleSheet("color: #999;")  # Ausgrauen für nicht-suchebare Spalten
                field_layout.addWidget(label)

                # Suchfeld
                search_edit = QLineEdit()
                search_edit.setPlaceholderText(f"Suche in {display_name}...")
                if not is_searchable:
                    search_edit.setEnabled(False)  # Deaktivieren für nicht-suchebare Spalten
                    search_edit.setStyleSheet("color: #999; background-color: #f5f5f5;")  # Ausgrauen
                else:
                    search_edit.textChanged.connect(lambda text, fn=field_name: self._on_column_search_changed(fn, text))
                field_layout.addWidget(search_edit)

                # Negative Checkbox
                negative_checkbox = QCheckBox("Neg.")
                negative_checkbox.setToolTip("Negative Suche für diese Spalte")
                if not is_searchable:
                    negative_checkbox.setEnabled(False)  # Deaktivieren für nicht-suchebare Spalten
                field_layout.addWidget(negative_checkbox)

                column_search_layout.addLayout(field_layout)
                self.column_search_fields[field_name] = {
                    'edit': search_edit,
                    'negative': negative_checkbox
                }

        parent_layout.addWidget(column_search_group)

    def _get_table_projection_columns(self):
        """SUCH-PANEL-PROJEKTION DIREKT AUS GCS (NEUE EINFACHE ARCHITEKTUR)"""
        try:
            # View-GUID für Projektion
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                logger.error("❌ Keine View-GUID verfügbar für Such-Panel")
                return []

            # GCS direkt verwenden für Such-Panel
            if not gcs:
                logger.error("❌ GCS nicht verfügbar")
                return []
                
            # DIREKTE PROJEKTION aus GCS für Such-Panel - Live-Berechnung aus Controls
            # STATISCHE PROJEKTION für Search je nach Expert Mode
            if gcs.expert_mode:
                projection = gcs.get_projection_table(view_guid, 'search_expert')
            else:
                projection = gcs.get_projection_table(view_guid, 'search_standard')
            if projection:
                mode_info = "Expert" if gcs.expert_mode else "Standard"
                logger.debug(f"✅ Such-Projektion ({mode_info}) live berechnet: {len(projection)} Spalten")
                return projection
            else:
                logger.warning(f"⚠️ Keine Such-Projektion verfügbar für View {view_guid}")
                return []

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Such-Projektion aus GCS: {e}")
            return []

    def _load_filter_settings(self):
        """Lädt persistente Filter-Einstellungen"""
        try:
            # GCS direkt verwenden
            if gcs:
                # Filter-Einstellungen aus GCS laden
                filter_settings = gcs.db.get_static_value(self.view_dialog.view_guid, 'searchparameter')
                if filter_settings:
                    self.filter_settings = filter_settings
                    logger.info("✅ Filter-Einstellungen geladen")
                else:
                    self.filter_settings = self._get_default_settings()
                    logger.info("ℹ️ Standard-Filter-Einstellungen verwendet")
            else:
                self.filter_settings = self._get_default_settings()
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Filter-Einstellungen: {e}")
            self.filter_settings = self._get_default_settings()

    def _get_default_settings(self):
        """Gibt Standard-Filter-Einstellungen zurück"""
        return {
            'case_sensitive': False,
            'whole_word': False,
            'global_search': '',
            'global_negative': False,
            'column_searches': {}
        }

    def _save_filter_settings(self):
        """Speichert Filter-Einstellungen persistent"""
        try:
            # GCS direkt verwenden
            if gcs:
                # Aktuelle Einstellungen sammeln
                settings = {
                    'case_sensitive': self.case_sensitive_radio.isChecked(),
                    'whole_word': self.whole_word_radio.isChecked(),
                    'global_search': self.global_search_edit.text(),
                    'global_negative': self.global_negative_checkbox.isChecked(),
                    'column_searches': {}
                }

                # Spalten-spezifische Suchen
                for field_name, field_data in self.column_search_fields.items():
                    settings['column_searches'][field_name] = {
                        'text': field_data['edit'].text(),
                        'negative': field_data['negative'].isChecked()
                    }

                # In GCS speichern
                gcs.db.set_value(self.view_dialog.view_guid, 'searchparameter', settings)
                gcs.db.save_all_values()

                logger.info("💾 Filter-Einstellungen gespeichert")
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Filter-Einstellungen: {e}")

    def _on_global_search_changed(self, text):
        """Handler für globale Suchfeld-Änderungen - LINEARES FILTER-SYSTEM"""
        if hasattr(self, 'view_dialog') and self.view_dialog:
            self.view_dialog.apply_filter_string(text)
            logger.info(f"🔍 Globale Suche angewendet: '{text}'")

    def _on_column_search_changed(self, field_name, text):
        """Handler für Spalten-spezifische Suchfeld-Änderungen"""
        # Automatische Filter-Anwendung (optional)
        pass

    def _apply_filters(self):
        """Filter anwenden"""
        try:
            # Filter-Einstellungen sammeln
            filter_config = {
                'case_sensitive': self.case_sensitive_radio.isChecked(),
                'whole_word': self.whole_word_radio.isChecked(),
                'global_search': self.global_search_edit.text().strip(),
                'global_negative': self.global_negative_checkbox.isChecked(),
                'column_filters': {}
            }

            # Spalten-spezifische Filter
            for field_name, field_data in self.column_search_fields.items():
                search_text = field_data['edit'].text().strip()
                if search_text:
                    filter_config['column_filters'][field_name] = {
                        'text': search_text,
                        'negative': field_data['negative'].isChecked()
                    }

            # Filter anwenden (hier würde die eigentliche Filter-Logik implementiert)
            self._apply_search_filters(filter_config)

            # Einstellungen speichern
            self._save_filter_settings()

            # Filter als aktiv markieren
            self.filter_active = True

            logger.info("✅ Filter angewendet")

        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Filter: {e}")
            QMessageBox.warning(self, "Filter-Fehler", f"Filter konnten nicht angewendet werden:\n{e}")

    def _cancel_filters(self):
        """Filter abbrechen - Panel ausblenden"""
        # Panel ausblenden
        self.hide()
        logger.info("ℹ️ Filter-Panel ausgeblendet")

    def _reset_filters(self):
        """Filter zurücksetzen"""
        try:
            # Sicherheitsabfrage
            reply = QMessageBox.question(self, "Filter zurücksetzen",
                                       "Möchten Sie alle Filter zurücksetzen?",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)

            if reply != QMessageBox.Yes:
                return

            # Alle Felder zurücksetzen
            self.case_insensitive_radio.setChecked(True)
            self.word_parts_radio.setChecked(True)
            self.global_search_edit.clear()
            self.global_negative_checkbox.setChecked(False)

            for field_data in self.column_search_fields.values():
                field_data['edit'].clear()
                field_data['negative'].setChecked(False)

            # Filter zurücksetzen (hier würde die eigentliche Reset-Logik implementiert)
            self._reset_search_filters()

            # Einstellungen speichern
            self._save_filter_settings()

            # Filter als inaktiv markieren
            self.filter_active = False

            logger.info("🔄 Filter zurückgesetzt")

        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Filter: {e}")

    def _apply_search_filters(self, filter_config):
        """Wendet die Suchfilter auf die Daten an"""
        # Hier würde die eigentliche Filter-Logik implementiert werden
        # Für jetzt: Einfache Implementierung mit Wildcard-Support

        # Original-Matrix initialisieren/sichern, falls noch nicht geschehen
        if not hasattr(self.view_dialog, 'original_matrix') or not self.view_dialog.original_matrix:
            self.view_dialog.original_matrix = self.view_dialog.display_matrix.copy()
            logger.info("💾 Original-Matrix für Filterung gesichert")

        original_matrix = self.view_dialog.original_matrix
    def _apply_search_filters(self, filter_config):
        """
        NEUE LINEARE FILTERUNG: Einheitlicher Filterstring-Ansatz
        """
        try:
            # Hole Filterstring vom SearchParameterDialog
            filter_string = ""
            if hasattr(self.search_dialog, 'result_filter_string'):
                filter_string = self.search_dialog.result_filter_string
            
            logger.info(f"🎯 Anwenden einheitlicher Filterstring: '{filter_string}'")
            
            # Wende Filterstring an
            self.apply_filter_string(filter_string)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei einheitlicher Filterung: {e}")
            # Fallback: Alle Zeilen anzeigen
            if hasattr(self, 'view_dialog') and self.view_dialog and hasattr(self.view_dialog, 'display') and self.view_dialog.display and hasattr(self.view_dialog.display, '_show_all_rows'):
                self.view_dialog.display._show_all_rows()

    def apply_filter_string(self, filter_string):
        """
        ZENTRALE FILTERMETHODE: Wendet einen einheitlichen Filterstring auf die Tabelle an
        
        Args:
            filter_string (str): Filterstring im Format "feld1:wert1||feld2:wert2||EXTENDED:feld3:bedingungen"
        """
        try:
            if not filter_string or filter_string.strip() == "":
                # Kein Filter - alle Zeilen anzeigen
                logger.info("🔓 Kein Filter - alle Zeilen anzeigen")
                if hasattr(self, 'view_dialog') and self.view_dialog and hasattr(self.view_dialog, 'display') and self.view_dialog.display and hasattr(self.view_dialog.display, '_show_all_rows'):
                    self.view_dialog.display._show_all_rows()
                return
            
            logger.info(f"🔍 Anwenden Filterstring: {filter_string}")
            
            # Parse Filterstring
            filter_parts = filter_string.split("||")
            visible_count = 0
            total_count = self.table.rowCount()
            
            # Durch alle Tabellenzeilen iterieren
            for row_index in range(total_count):
                row_matches = self._row_matches_filter_string(row_index, filter_parts)
                
                # Zeile anzeigen/verstecken
                self.table.setRowHidden(row_index, not row_matches)
                if row_matches:
                    visible_count += 1
            
            # Status-Update
            if hasattr(self, 'search_status'):
                if visible_count == 0:
                    self.search_status.setText(f"⚠️ Keine Treffer für Filter")
                    self.search_status.setStyleSheet("QLabel { color: #d32f2f; }")
                else:
                    self.search_status.setText(f"🔍 {visible_count} von {total_count} Zeilen (gefiltert)")
                    self.search_status.setStyleSheet("QLabel { color: #388e3c; }")
            
            logger.info(f"✅ Filter angewendet: {visible_count} von {total_count} Zeilen sichtbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des Filterstrings: {e}")
            self._show_all_rows()

    def _row_matches_filter_string(self, row_index, filter_parts):
        """
        Prüft ob eine Tabellenzeile dem Filterstring entspricht
        
        Args:
            row_index (int): Index der Tabellenzeile
            filter_parts (list): Liste der Filter-Teile
            
        Returns:
            bool: True wenn Zeile den Filtern entspricht
        """
        try:
            # Alle Filter müssen erfüllt sein (AND-Verknüpfung)
            for filter_part in filter_parts:
                if not self._row_matches_single_filter(row_index, filter_part):
                    return False
            
            return True  # Alle Filter erfüllt
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Prüfen der Zeile {row_index}: {e}")
            return False

    def _row_matches_single_filter(self, row_index, filter_part):
        """
        Prüft ob eine Zeile einem einzelnen Filter entspricht
        
        Args:
            row_index (int): Index der Tabellenzeile
            filter_part (str): Einzelner Filter im Format "feld:wert" oder "EXTENDED:feld:bedingungen"
            
        Returns:
            bool: True wenn Zeile dem Filter entspricht
        """
        try:
            if ":" not in filter_part:
                return True  # Ungültiger Filter - ignorieren
            
            if filter_part.startswith("EXTENDED:"):
                # Erweiterte Filter
                return self._row_matches_extended_filter(row_index, filter_part)
            else:
                # Einfache Filter
                return self._row_matches_simple_filter(row_index, filter_part)
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Prüfen einzelner Filter: {e}")
            return False

    def _row_matches_simple_filter(self, row_index, filter_part):
        """Prüft einfachen Filter: 'feldname:wert'"""
        try:
            field_name, search_value = filter_part.split(":", 1)
            
            # Finde passende Spalte
            column_index = self._get_column_index_for_field(field_name)
            if column_index is None:
                logger.warning(f"⚠️ Spalte für Feld '{field_name}' nicht gefunden")
                return True  # Unbekannte Felder ignorieren
            
            # Zellwert holen
            item = self.table.item(row_index, column_index)
            cell_value = item.text() if item else ""
            
            # Einfache Contains-Suche (case-insensitive)
            return search_value.lower() in cell_value.lower()
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei einfachem Filter: {e}")
            return False

    def _row_matches_extended_filter(self, row_index, filter_part):
        """Prüft erweiterten Filter: 'EXTENDED:feldname:bedingungen'"""
        try:
            # Für jetzt: Erweiterte Filter über bestehende Engine
            from extended_filter_engine import extended_filter_engine
            
            # Zeilen-Daten extrahieren
            from extended_filter_engine import extended_filter_engine
            row_data = extended_filter_engine._extract_row_data_from_table(self.table, row_index)
            if row_data is None:
                return False
            
            # Erweiterte Bedingungen prüfen
            return extended_filter_engine._row_matches_extended_conditions(row_data, {})
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei erweitertem Filter: {e}")
            return False

    def _apply_normal_search_filters(self, filter_config):
        """
        Normale Filterlogik für Suchfelder (ohne Extended Filter)
        """
        try:
            logger.info("🔍 Anwenden normale Such-Filter...")
            
            # Sammle alle aktiven normalen Suchfilter
            active_filters = {}
            for field_key, widget_data in self.search_dialog.filter_widgets.items():
                widget = widget_data.get('widget')
                if widget and widget.text().strip():
                    active_filters[field_key] = {
                        'text': widget.text().strip(),
                        'negative': False  # Normale Suche ist nicht negativ
                    }
            
            if not active_filters:
                self._show_all_rows()
                return
            
            logger.info(f"🔍 Aktive normale Filter: {list(active_filters.keys())}")
            
            # Alle Zeilen durchgehen und filtern
            visible_count = 0
            total_rows = self.table.rowCount()
            
            for row_index in range(total_rows):
                # Zeile ist sichtbar wenn alle Filter zutreffen
                row_matches = True
                
                for field_key, filter_data in active_filters.items():
                    # Zellwert aus Tabelle extrahieren
                    column_index = self._get_column_index_for_field(field_key)
                    if column_index is None:
                        continue
                        
                    item = self.table.item(row_index, column_index)
                    cell_value = item.text() if item else ""
                    
                    search_text = filter_data['text']
                    
                    # Einfache Contains-Suche (case-insensitive)
                    if not search_text.lower() in cell_value.lower():
                        row_matches = False
                        break
                
                # Zeile anzeigen/verstecken
                self.table.setRowHidden(row_index, not row_matches)
                if row_matches:
                    visible_count += 1
            
            logger.info(f"✅ Normale Filterung: {visible_count}/{total_rows} Zeilen sichtbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei normaler Filterung: {e}")
            self._show_all_rows()
    
    def _get_column_index_for_field(self, field_key):
        """Findet Column-Index für Feld-Schlüssel"""
        try:
            # Vereinfachte Logik: Feld-Namen matchen
            for col in range(self.table.columnCount()):
                header = self.table.horizontalHeaderItem(col)
                if header and header.text().lower().replace(" ", "_") == field_key:
                    return col
            return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Finden Column-Index für '{field_key}': {e}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei linearem Filter-System: {e} - alle Zeilen anzeigen")
            self._show_all_rows()

    def _check_global_search(self, row, filter_config):
        """Prüft globale Suche für eine Zeile"""
        search_text = filter_config['global_search']
        case_sensitive = filter_config['case_sensitive']
        whole_word = filter_config['whole_word']

        # Alle searchable Spalten durchsuchen
        for field_name in self.column_search_fields.keys():
            if field_name in row:
                cell_value = str(row[field_name])
                if self._matches_search(cell_value, search_text, case_sensitive, whole_word):
                    return True

        return False

    def _check_column_search(self, row, field_name, column_filter, filter_config):
        """Prüft Spalten-spezifische Suche"""
        if field_name not in row:
            return not column_filter['negative']  # Wenn Feld nicht vorhanden, bei negativer Suche True

        cell_value = str(row[field_name])
        search_text = column_filter['text']
        negative = column_filter['negative']
        case_sensitive = filter_config['case_sensitive']
        whole_word = filter_config['whole_word']

        matches = self._matches_search(cell_value, search_text, case_sensitive, whole_word)

        return matches if not negative else not matches

    def _matches_search(self, text, search_pattern, case_sensitive, whole_word):
        """Prüft ob Text dem Suchmuster entspricht"""
        if not text or not search_pattern:
            return False

        # Groß-/Kleinschreibung
        if not case_sensitive:
            text = text.lower()
            search_pattern = search_pattern.lower()

        # Wildcard-Support
        search_pattern = self._convert_wildcards(search_pattern)

        import re

        if whole_word:
            # Ganzes Wort
            pattern = r'\b' + re.escape(search_pattern) + r'\b'
        else:
            # Wortteile
            pattern = search_pattern

        try:
            return bool(re.search(pattern, text, re.IGNORECASE if not case_sensitive else 0))
        except re.error:
            # Fallback bei Regex-Fehlern
            return search_pattern in text

    def _convert_wildcards(self, pattern):
        """Konvertiert Wildcard-Symbole zu Regex"""
        # % → .*
        # ? → .
        # Escape special regex chars
        pattern = re.escape(pattern)
        pattern = pattern.replace(r'\%', '.*')  # % für beliebig viele Zeichen
        pattern = pattern.replace(r'\?', '.')   # ? für ein Zeichen
        return pattern
    
    def _extract_field_from_extended_string(self, filter_string):
        """Extrahiert Feldname aus EXTENDED Filter-String"""
        try:
            # Beispiel: "EXTENDED:familienname_show:conditions"
            if 'EXTENDED:' in filter_string:
                parts = filter_string.split(':')
                if len(parts) >= 2:
                    return parts[1]
        except:
            pass
        return 'unknown_field'
    
    def _parse_extended_conditions_from_string(self, filter_string):
        """Parst Extended Filter Conditions aus String"""
        try:
            # Placeholder - erweiterte Bedingungen aus String extrahieren
            # TODO: Implementierung basierend auf tatsächlichem Extended Filter Format
            return []
        except:
            return []
    
    def _parse_to_parametric_config(self, filter_string):
        """Konvertiert Filter-String zu parametrischem Filter-Config"""
        try:
            # Beispiel: "familienname_show:Lau" oder "vorname_show:NOT:Max"
            if ':' in filter_string:
                parts = filter_string.split(':')
                if len(parts) >= 2:
                    field_name = parts[0]
                    
                    if len(parts) >= 3 and parts[1] == 'NOT':
                        # Negation
                        return {
                            'field_name': field_name,
                            'search_value': parts[2],
                            'operator': 'NOT_enthält'
                        }
                    else:
                        # Normal
                        return {
                            'field_name': field_name,
                            'search_value': parts[1],
                            'operator': 'enthält'
                        }
            
            # Fallback für einfachen Text
            return {
                'field_name': 'global',
                'search_value': filter_string,
                'operator': 'enthält'
            }
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen parametrischer Filter-Config: {e}")
            return {
                'field_name': 'global',
                'search_value': filter_string,
                'operator': 'enthält'
            }

    def _reset_search_filters(self):
        """Setzt alle Suchfilter zurück"""
        # Original-Matrix wiederherstellen
        if hasattr(self.view_dialog, 'original_matrix'):
            self.view_dialog.display_matrix = self.view_dialog.original_matrix.copy()
        else:
            # Fallback: Matrix neu erstellen
            self.view_dialog._create_display_matrix()

        # UI-Elemente zurücksetzen
        self.case_insensitive_radio.setChecked(True)
        self.word_parts_radio.setChecked(True)
        self.global_search_edit.clear()
        self.global_negative_checkbox.setChecked(False)
        
        # Spalten-spezifische Suchfelder zurücksetzen
        for field_data in self.column_search_fields.values():
            field_data['edit'].clear()
            field_data['negative'].setChecked(False)

        # Tabelle aktualisieren
        if hasattr(self.view_dialog, 'refresh_table'):
            self.view_dialog.refresh_table()

        # Filter als inaktiv markieren
        self.filter_active = False

        logger.info("🔄 Suchfilter zurückgesetzt")