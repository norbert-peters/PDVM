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

# V3 Filter-System
from schnellsuche_manager import SchnellsucheManager

import logging
import time
import json
import traceback
import re

logger = logging.getLogger(__name__)

# NEUES UNIFIED LINEAR FILTER SYSTEM
from pdvm_linear_filter_integration import create_pdvm_linear_filter

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
from PyQt5.QtWidgets import QWidget


class PdvmViewDialog(QWidget):
    """
    SAUBERER Autonomer View-Dialog mit integriertem Datenmanagement - EINE KLASSE!
    
    LINEARE ARCHITEKTUR:
    1. Validation der call_daten
    2. ViewDaten laden mit korrekter PdvmCentralDatenbank
    3. Controls linear generieren: ViewDaten → _original → _show → dummy
    4. Controls in GCS speichern
    5. Daten laden und Matrix erstellen
    6. UI direkt erstellen (KEINE separate Display-Klasse!)
    """
    
    def __init__(self, call_daten, parent=None, view_manager=None):
        """
        Initialisierung des autonomen View-Dialogs als QWidget
        
        Args:
            call_daten: Enthält view_guid, title, first_call, reset
            parent: Parent-Widget
            view_manager: Optional View-Manager für synchronisierte Projektion
        """
        # WICHTIG: Zuerst QWidget initialisieren!
        super().__init__(parent)
        
        self.call_daten = call_daten
        self.parent = parent
        self.view_manager = view_manager  # Optional: View-Manager für Synchronisation
        
        # Fallback: Versuche View-Manager aus Parent zu bekommen
        if self.view_manager is None and hasattr(parent, 'view_manager'):
            self.view_manager = parent.view_manager
            logger.info("✅ View-Manager aus Parent übernommen")
        
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
        self.display_matrix = []  # Legacy - wird durch MatrixManager ersetzt
        
        # UI-Container
        self.display = None
        
        # 🚀 NEUES 4-SCHICHTEN MATRIX-SYSTEM
        self.matrix_integration = None  # Wird nach GCS-Verfügbarkeit initialisiert
        
        # NEUES LINEARES FILTER-SYSTEM
        self.linear_filter = None  # Wird nach display-Erstellung initialisiert
        
        # SORTIERUNGS-MANAGER
        self.sorting_manager = None  # Wird nach display-Erstellung initialisiert
        
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
        # Alte DB (Kompatibilität)
        gcs.db.set_value(
            gruppe=self.view_guid, 
            feld='controls', 
            wert=all_controls
        )
        gcs.db.save_all_values()
        
        # SCHRITT 5b: Controls auch in Systemsteuerung-DB speichern (für Projektions-Tabellen)
        import json
        for control_key, control_config in all_controls.items():
            try:
                control_json = json.dumps(control_config, ensure_ascii=False)
                gcs._db.set_value(self.view_guid, control_key, control_json)
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Speichern von {control_key} in Systemsteuerung-DB: {e}")
        
        logger.info(f"✅ SCHRITT 5: Controls in beide DBs gespeichert: {len(all_controls)} total")
        
        self.controls_config = all_controls
        logger.info(f"🎉 KORREKT: ViewDaten bilden die Basis, Benutzer-Werte werden übernommen!")
        
        # SCHRITT 5c: Projektions-Tabellen in GCS aufbauen (für Sortierung benötigt)
        try:
            logger.info("🔄 Baue Projektions-Tabellen für Sortierung auf...")
            gcs.rebuild_projection_tables(self.view_guid)
            logger.info("✅ Projektions-Tabellen erfolgreich aufgebaut")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aufbau der Projektions-Tabellen: {e}")
        
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
        
        # 🚀 PDVM MATRIX-MANAGER - DIREKTE INTEGRATION
        self._initialize_clean_matrix_manager()
        
        # Matrix-Manager mit Daten versorgen
        if hasattr(self, 'display_matrix') and self.display_matrix:
            # Alle Spalten sammeln
            all_columns = set()
            for row in self.display_matrix:
                all_columns.update(row.keys())
            
            # Matrix-Manager initialisieren
            self._initialize_matrix_with_data(self.display_matrix, all_columns)
    
    def _initialize_clean_matrix_manager(self):
        """
        🎯 ULTRA-LINEARER Matrix-Manager (DIREKT - KEINE INTEGRATION!)
        """
        try:
            logger.info("🏗️ Initialisiere PdvmMatrixManager (DIREKT)...")
            
            from pdvm_matrix_manager import get_matrix_manager
            
            # Direkter Matrix-Manager - KEINE komplexe Integration!
            self.matrix_manager = get_matrix_manager(self.view_guid)
            
            if not self.matrix_manager:
                raise RuntimeError("PdvmMatrixManager konnte nicht erstellt werden!")
            
            logger.info("✅ PdvmMatrixManager DIREKT initialisiert")
            
        except Exception as e:
            error_msg = f"❌ KRITISCHER FEHLER: Matrix-Manager nicht verfügbar!\n{e}"
            logger.error(error_msg)
            raise RuntimeError("Matrix-Manager ist ERFORDERLICH!")
    
    def _initialize_matrix_with_data(self, data, columns):
        """
        Matrix-Manager mit Daten versorgen (BASIS-Matrix setzen)
        
        Args:
            data: Matrix-Daten
            columns: Spalten-Set
        """
        if not hasattr(self, 'matrix_manager') or not self.matrix_manager:
            logger.error("❌ Matrix-Manager nicht verfügbar!")
            return
        
        try:
            # BASIS-MATRIX im Matrix-Manager setzen
            self.matrix_manager.set_basis_matrix(data, columns)
            
            # Initial: Filter anwenden (auch wenn leer)
            self.matrix_manager.apply_filter(None)
            
            # Initial: Sortierung anwenden (auch wenn leer)
            self.matrix_manager.apply_sort(None)
            
            logger.info("✅ Matrix-Manager mit Daten versorgt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Matrix-Daten setzen: {e}")
            raise
    
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
        """5. UI erstellen - DIREKT ohne separate Display-Klasse"""
        logger.info("🔧 Erstelle UI...")
        
        # UI direkt in PdvmViewDialog erstellen
        self._setup_ui_direct()
        
        logger.info("✅ UI erstellt")
        
        # Nach UI-Erstellung: Persistente Filter laden und anwenden
        self._load_and_apply_persistent_filters()
    
    def _load_and_apply_persistent_filters(self):
        """V3: Lade persistente Filter mit SchnellsucheManager"""
        try:
            if not hasattr(self, 'search_input'):
                return
            
            # V3: SchnellsucheManager verwenden (braucht matrix_manager)
            if not hasattr(self, 'matrix_manager') or not self.matrix_manager:
                logger.info("ℹ️ Matrix Manager nicht verfügbar")
                return
            
            # Manager erstellen
            schnellsuche_manager = SchnellsucheManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager
            )
            
            # UI-Daten laden (NUR wenn s_source == 'schnell')
            search_text = schnellsuche_manager.load_schnellsuche_ui()
            
            if search_text:
                self.search_input.setText(search_text)
                logger.info(f"🔄 V3: Schnellsuche in UI wiederhergestellt: '{search_text}'")
            else:
                self.search_input.clear()
                logger.info(f"ℹ️ V3: Schnellsuche-Feld leer (anderer Filter aktiv)")
            
            # HINWEIS: Einfach/Komplex-Filter werden in ihren Dialogen geladen
            # Pipeline lädt s_string AUTONOM beim rebuild_pipeline()
            logger.info("✅ V3: Persistente Filter-UI aktualisiert")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden persistenter Filter-UI: {e}")
    
    def apply_filter_string(self, filter_string: str):
        """🎯 NEUE UNIFIED LINEAR FILTER-METHODE - ersetzt alles alte
        
        Args:
            filter_string (str): Filterstring für alle drei Filterarten
        """
        try:
            logger.info("🎯 === PDVM VIEW DIALOG - UNIFIED LINEAR FILTER ===")
            logger.info(f"📂 View-GUID: {self.view_guid}")
            logger.info(f"🔍 Filter-String: '{filter_string}'")
            
            # Filter-Integration sicherstellen
            if not self.linear_filter and hasattr(self, 'display') and self.display and hasattr(self.display, 'table'):
                # VEREINFACHT: Keine Column-Mappings mehr - Control-Key Patch übernimmt das
                self.linear_filter = create_pdvm_linear_filter(self.table, self.view_guid)
                logger.info("✅ Linear Filter Integration mit Control-Key Patch erstellt")
            
            if not self.linear_filter:
                logger.error("❌ Kein Linear Filter verfügbar")
                return
            
            # EINHEITLICHE LINEARE FILTER-ANWENDUNG
            success = self.linear_filter.apply_filter_unified(filter_string)
            
            if success:
                logger.info("✅ Unified Linear Filter-Anwendung erfolgreich")
                # UI refresh direkt
                self.refresh_table_direct()
            else:
                logger.error("❌ Unified Linear Filter-Anwendung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler in neuer unified linear Filter-Methode: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # SCHRITT 3: Display-Update direkt
            self.refresh_table_direct()
                
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
                visible_columns = self._get_visible_columns_from_gcs()
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
                table = self.table
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
                    self.search_input.clear()
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
        """Widget für Integration zurückgeben - SELF da UI direkt hier ist"""
        logger.info("🔹 get_display_widget() - UI ist direkt in PdvmViewDialog integriert")
        return self
    
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
        self.refresh_table_direct()

    # === DIREKTE UI-FUNKTIONEN - KEINE SEPARATE DISPLAY-KLASSE! ===
    
    def _setup_ui_direct(self):
        """Direkte UI-Erstellung in PdvmViewDialog ohne separate Display-Klasse"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit, 
                                       QTableWidget, QPushButton, QToolBar, QAction, QComboBox, QCheckBox)
            from PyQt5.QtGui import QFont, QIcon
            from PyQt5.QtCore import QSize
            
            logger.info("🔧 Starte UI-Setup...")
            
            # CRITICAL: Prüfe, ob bereits ein Layout existiert
            if self.layout() is not None:
                logger.warning("⚠️ Widget hat bereits ein Layout - überspringe Setup")
                return
            
            # Layout für den Dialog - ERST erstellen, DANN setzen
            layout = QVBoxLayout()
            layout.setSpacing(5)
            layout.setContentsMargins(10, 10, 10, 10)
            logger.info(f"🔧 Layout erstellt: {layout}")
            
            # Header-Bereich mit Titel und Einstellungen-Zahnrad
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            # Header-Label - SICHERE Erstellung
            gcs = get_gcs()
            base_title = getattr(self, 'title', f"View: {self.view_guid}")
            if gcs and gcs.expert_mode and hasattr(gcs, 'st_inst') and gcs.st_inst:
                formatted_stichtag = getattr(gcs.st_inst, 'FormTimeStamp', str(gcs.st_inst.PdvmDateTime))
                title_text = f"{base_title} - Stichtag: {formatted_stichtag}"
            else:
                title_text = base_title
                
            self.header_label = QLabel(title_text)
            if self.header_label is None:
                logger.error("❌ Header-Label konnte nicht erstellt werden!")
                return
                
            header_font = QFont("Segoe UI", 12, QFont.Bold)
            self.header_label.setFont(header_font)
            self.header_label.setStyleSheet("""
                QLabel {
                    color: #1a365d;
                    padding: 10px;
                    background-color: #e2e8f0;
                    border-radius: 6px;
                    border: 1px solid #cbd5e0;
                }
            """)
            header_layout.addWidget(self.header_label)
            
            # Einstellungs-Zahnrad rechts
            self.settings_btn = QPushButton("⚙️")
            self.settings_btn.setToolTip("Einstellungen")
            self.settings_btn.setFixedSize(35, 35)
            self.settings_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    background-color: #3498db;
                    border: none;
                    border-radius: 17px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """)
            self.settings_btn.clicked.connect(self._show_settings_menu)
            header_layout.addWidget(self.settings_btn)
            
            # Header-Widget zum Layout hinzufügen
            layout.addWidget(header_widget)
            logger.info(f"✅ Header mit Einstellungs-Zahnrad hinzugefügt")
            
            # === GESAMTSUCHE-FELD ===
            self._create_global_search_field(layout)
            
            # Tabelle DIREKT in PdvmViewDialog - SICHERE Erstellung
            self.table = QTableWidget()
            if self.table is None:
                logger.error("❌ Tabelle konnte nicht erstellt werden!")
                return
                
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            
            # Header-Schrift konfigurieren
            header_font = QFont("Segoe UI", 10, QFont.Bold)
            self.table.horizontalHeader().setFont(header_font)
            
            # KRITISCH: Tabelle explizit sichtbar machen
            self.table.setVisible(True)
            self.table.show()
            logger.info(f"🔧 Tabelle Sichtbarkeit: {self.table.isVisible()}")
            
            # Mindestgröße setzen damit Tabelle sichtbar wird
            self.table.setMinimumSize(400, 200)
            
            # SICHERE Widget-Hinzufügung
            if self.table is not None and layout is not None:
                layout.addWidget(self.table)
                logger.info(f"✅ Tabelle hinzugefügt: {self.table}")
            else:
                logger.error(f"❌ Kann Tabelle nicht hinzufügen: Widget={self.table}, Layout={layout}")
                return
            
            # DIREKTE Header-Click Verbindung in derselben Klasse
            self._setup_header_click_direct()
            
            # Status-Label - SICHERE Erstellung
            self.status_label = QLabel("Bereit")
            if self.status_label is None:
                logger.error("❌ Status-Label konnte nicht erstellt werden!")
                return
                
            self.status_label.setMinimumHeight(20)
            
            # SICHERE Widget-Hinzufügung
            if self.status_label is not None and layout is not None:
                layout.addWidget(self.status_label)
                logger.info(f"✅ Status-Label hinzugefügt: {self.status_label}")
            else:
                logger.error(f"❌ Kann Status-Label nicht hinzufügen: Widget={self.status_label}, Layout={layout}")
                return
            
            # CRITICAL: Layout zum Widget setzen - GANZ AM ENDE!
            try:
                if layout is not None:
                    self.setLayout(layout)
                    logger.info(f"✅ Layout zum Widget gesetzt: {layout}")
                    
                    # SOFORTIGE SICHTBARKEITS-PRÜFUNG
                    logger.info(f"🔍 Widget selbst sichtbar: {self.isVisible()}")
                    logger.info(f"🔍 Tabelle sichtbar: {self.table.isVisible() if hasattr(self, 'table') else 'N/A'}")
                    logger.info(f"🔍 Header-Label sichtbar: {self.header_label.isVisible() if hasattr(self, 'header_label') else 'N/A'}")
                    logger.info(f"🔍 Status-Label sichtbar: {self.status_label.isVisible() if hasattr(self, 'status_label') else 'N/A'}")
                    
                    # Widget explizit sichtbar machen
                    self.setVisible(True)
                    self.show()
                    logger.info(f"🔧 Widget nach show(): {self.isVisible()}")
                    
                else:
                    logger.error("❌ Layout ist None - kann nicht gesetzt werden!")
                    return
            except Exception as e:
                logger.error(f"❌ Fehler beim Layout setzen: {e}")
                return
            
            # Nach UI-Setup: Tabelle füllen
            logger.info("🔧 Starte Tabellen-Befüllung...")
            self.refresh_table_direct()
            
            logger.info("✅ UI-Setup abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei direkter UI-Erstellung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _create_global_search_field(self, layout):
        """Erstelle das Gesamtsuche-Feld"""
        try:
            # Such-Widget Container
            search_widget = QWidget()
            search_layout = QHBoxLayout(search_widget)
            search_layout.setContentsMargins(5, 5, 5, 5)
            
            # Such-Label
            search_label = QLabel("🔍 Gesamtsuche:")
            search_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px;
                }
            """)
            search_layout.addWidget(search_label)
            
            # Such-Input
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Suchbegriff eingeben...")
            self.search_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    font-size: 14px;
                    background-color: white;
                }
                QLineEdit:focus {
                    border-color: #2980b9;
                    background-color: #f8f9fa;
                }
            """)
            # V3: KEIN textChanged Event - nur bei ENTER oder Button-Klick!
            self.search_input.returnPressed.connect(self._perform_global_search)
            search_layout.addWidget(self.search_input)
            
            # Such-Button  
            search_btn = QPushButton("Suchen")
            search_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """)
            search_btn.clicked.connect(self._perform_global_search)
            search_layout.addWidget(search_btn)
            
            # Reset-Button
            reset_btn = QPushButton("Zurücksetzen")
            reset_btn.setStyleSheet("""
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
            """)
            reset_btn.clicked.connect(self._reset_search)
            search_layout.addWidget(reset_btn)
            
            layout.addWidget(search_widget)
            logger.info("✅ Gesamtsuche-Feld erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Gesamtsuche-Felds: {e}")
    
    def _show_settings_menu(self):
        """Zeige Einstellungsmenü beim Klick auf Zahnrad"""
        try:
            from PyQt5.QtWidgets import QMenu, QAction
            
            # Menü erstellen
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 20px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #3498db;
                    color: white;
                }
            """)
            
            # Menü-Aktionen
            column_action = QAction("📋 Spalten verwalten", self)
            column_action.triggered.connect(self._show_column_management)
            menu.addAction(column_action)
            
            search_action = QAction("🔎 Erweiterte Suche", self)
            search_action.triggered.connect(self._show_advanced_search)
            menu.addAction(search_action)
            
            menu.addSeparator()
            
            # Sortierung & Gruppierung
            sorting_action = QAction("📊 Sortierung & Gruppierung", self)
            sorting_action.triggered.connect(self._show_sorting_dialog)
            menu.addAction(sorting_action)
            
            # Alle Spalten sortierbar machen
            enable_sort_action = QAction("🔧 Alle Spalten sortierbar machen", self)
            enable_sort_action.triggered.connect(self._enable_all_columns_sortable)
            menu.addAction(enable_sort_action)
            
            menu.addSeparator()
            
            # Expert Mode nur für Admin-Benutzer anzeigen
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs:
                user_mode = gcs.mode  # 'user' oder 'admin'
                if user_mode == 'admin':
                    expert_action = QAction("🔧 Expert Mode", self)
                    expert_action.setCheckable(True)
                    expert_action.setChecked(gcs.expert_mode)
                    expert_action.triggered.connect(self._toggle_expert_mode)
                    menu.addAction(expert_action)
                    logger.debug(f"✅ Expert Mode Menüpunkt für Admin angezeigt (mode={user_mode})")
                else:
                    logger.debug(f"ℹ️ Expert Mode Menüpunkt ausgeblendet für mode={user_mode}")
            
            menu.addSeparator()
            
            refresh_action = QAction("🔄 Daten aktualisieren", self)
            refresh_action.triggered.connect(self._refresh_data)
            menu.addAction(refresh_action)
            
            export_action = QAction("📤 Daten exportieren", self)
            export_action.triggered.connect(self._export_data)
            menu.addAction(export_action)
            
            # Menü unter dem Button anzeigen
            button_pos = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft())
            menu.exec_(button_pos)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen des Einstellungsmenüs: {e}")
    
    def _on_search_text_changed(self, text):
        """Reagiere auf Änderungen im Suchfeld (Live-Suche)"""
        try:
            if len(text.strip()) >= 3:  # Live-Suche ab 3 Zeichen
                self._perform_global_search()
            elif len(text.strip()) == 0:  # Reset bei leerem Feld
                self._reset_search()
        except Exception as e:
            logger.error(f"❌ Fehler bei Live-Suche: {e}")
    
    def _reset_search(self):
        """
        V3: Suche zurücksetzen über ZENTRALEN FilterResetManager
        Verwendet: self.matrix_manager (NICHT self.controller!)
        """
        try:
            # 1. Suchfeld leeren
            if not hasattr(self, 'search_input'):
                error_msg = "FEHLER: Suchfeld nicht initialisiert!\n\nSuche-Reset kann nicht ausgeführt werden."
                logger.error(f"❌ {error_msg}")
                QMessageBox.critical(self, "Suche-Reset Fehler", error_msg)
                return
                
            self.search_input.clear()
            
            # 2. Matrix Manager prüfen
            if not hasattr(self, 'matrix_manager') or not self.matrix_manager:
                error_msg = "FEHLER: Matrix Manager nicht verfügbar!\n\nFilter-Reset kann nicht ausgeführt werden."
                logger.error(f"❌ {error_msg}")
                QMessageBox.critical(self, "Filter-Reset Fehler", error_msg)
                return
            
            # 3. V3: ZENTRALER FilterResetManager für ALLE Filter-Typen
            from filter_reset_manager import get_filter_reset_manager
            
            reset_manager = get_filter_reset_manager(self.view_guid, self.matrix_manager)
            
            # 4. ALLE Filter löschen (schnell + einfach + komplex)
            success = reset_manager.reset_all_filters()
            
            if success:
                logger.info("✅ V3 ALLE Filter zurückgesetzt - Suchfeld geleert, DB bereinigt")
            else:
                error_msg = "WARNUNG: Filter-Reset konnte nicht vollständig ausgeführt werden.\n\nBitte Log-Datei prüfen."
                logger.warning(f"⚠️ {error_msg}")
                QMessageBox.warning(self, "Filter-Reset Warnung", error_msg)
            
            # 5. Tabelle aktualisieren
            self.refresh_table_direct()
            
        except Exception as e:
            error_msg = f"KRITISCHER FEHLER beim Suche-Reset:\n\n{str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            QMessageBox.critical(self, "Suche-Reset Fehler", error_msg)
    
    def _create_toolbar(self, layout):
        """Erstelle Toolbar mit allen wichtigen Funktionen"""
        try:
            from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QFrame, QComboBox, QCheckBox
            
            # Toolbar-Frame
            toolbar_frame = QFrame()
            toolbar_frame.setFrameStyle(QFrame.StyledPanel)
            toolbar_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
            
            toolbar_layout = QHBoxLayout()
            toolbar_layout.setSpacing(10)
            toolbar_layout.setContentsMargins(5, 5, 5, 5)
            
            # === SUCH-BUTTONS ===
            self.btn_search = QPushButton("🔍 Suchen")
            self.btn_search.setToolTip("Globale Suche aktivieren")
            self.btn_search.clicked.connect(self._toggle_search)
            toolbar_layout.addWidget(self.btn_search)
            
            self.btn_advanced_search = QPushButton("🔎 Erweitert")
            self.btn_advanced_search.setToolTip("Erweiterte Suchparameter")
            self.btn_advanced_search.clicked.connect(self._show_advanced_search)
            toolbar_layout.addWidget(self.btn_advanced_search)
            
            # Trennlinie
            separator1 = QFrame()
            separator1.setFrameShape(QFrame.VLine)
            separator1.setFrameShadow(QFrame.Sunken)
            toolbar_layout.addWidget(separator1)
            
            # === ANSICHT-CONTROLS ===
            self.btn_settings = QPushButton("⚙️ Einstellungen")
            self.btn_settings.setToolTip("Spalten und Ansicht konfigurieren")
            self.btn_settings.clicked.connect(self._show_settings)
            toolbar_layout.addWidget(self.btn_settings)
            
            self.btn_columns = QPushButton("📋 Spalten")
            self.btn_columns.setToolTip("Spalten verwalten")
            self.btn_columns.clicked.connect(self._show_column_management)
            toolbar_layout.addWidget(self.btn_columns)
            
            # Expert Mode Toggle
            self.checkbox_expert = QCheckBox("Expert Mode")
            self.checkbox_expert.setToolTip("Erweiterte Funktionen anzeigen")
            self.checkbox_expert.stateChanged.connect(self._toggle_expert_mode)
            toolbar_layout.addWidget(self.checkbox_expert)
            
            # Trennlinie
            separator2 = QFrame()
            separator2.setFrameShape(QFrame.VLine)
            separator2.setFrameShadow(QFrame.Sunken)
            toolbar_layout.addWidget(separator2)
            
            # === DATEN-CONTROLS ===
            self.btn_refresh = QPushButton("🔄 Aktualisieren")
            self.btn_refresh.setToolTip("Daten neu laden")
            self.btn_refresh.clicked.connect(self._refresh_data)
            toolbar_layout.addWidget(self.btn_refresh)
            
            self.btn_export = QPushButton("📤 Export")
            self.btn_export.setToolTip("Daten exportieren")
            self.btn_export.clicked.connect(self._export_data)
            toolbar_layout.addWidget(self.btn_export)
            
            # Stretchable space
            toolbar_layout.addStretch()
            
            # === INFO-BEREICH ===
            self.lbl_row_count = QLabel("0 Zeilen")
            self.lbl_row_count.setStyleSheet("font-weight: bold; color: #495057;")
            toolbar_layout.addWidget(self.lbl_row_count)
            
            toolbar_frame.setLayout(toolbar_layout)
            layout.addWidget(toolbar_frame)
            
            logger.info("✅ Toolbar mit allen Funktionen erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Toolbar: {e}")
    
    def _create_search_section(self, layout):
        """Erstelle erweiterten Suchbereich"""
        try:
            from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QFrame
            
            # Such-Frame (initial versteckt)
            self.search_frame = QFrame()
            self.search_frame.setFrameStyle(QFrame.StyledPanel)
            self.search_frame.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            self.search_frame.setVisible(False)  # Initial versteckt
            
            search_layout = QHBoxLayout()
            search_layout.setSpacing(10)
            search_layout.setContentsMargins(5, 5, 5, 5)
            
            # Global Search Input
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Globale Suche - Suchbegriff eingeben...")
            self.search_input.returnPressed.connect(self._perform_global_search)
            # V3: KEIN textChanged Event mehr - nur bei ENTER oder Lupe-Klick!
            search_layout.addWidget(self.search_input)
            
            # Such-Buttons
            self.btn_search_execute = QPushButton("Suchen")
            self.btn_search_execute.clicked.connect(self._perform_global_search)
            search_layout.addWidget(self.btn_search_execute)
            
            self.btn_search_clear = QPushButton("Löschen")
            self.btn_search_clear.clicked.connect(self._clear_search)
            search_layout.addWidget(self.btn_search_clear)
            
            self.search_frame.setLayout(search_layout)
            layout.addWidget(self.search_frame)
            
            logger.info("✅ Such-Bereich erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Such-Bereichs: {e}")
    
    def _toggle_search(self):
        """Toggle Suchbereich Sichtbarkeit"""
        try:
            if hasattr(self, 'search_frame'):
                is_visible = self.search_frame.isVisible()
                self.search_frame.setVisible(not is_visible)
                
                if not is_visible:
                    # Fokus auf Suchfeld setzen
                    if hasattr(self, 'search_input'):
                        self.search_input.setFocus()
                    self.btn_search.setText("🔍 Ausblenden")
                else:
                    self.btn_search.setText("🔍 Suchen")
                    
                logger.info(f"🔍 Suchbereich {'ein' if not is_visible else 'aus'}geblendet")
        except Exception as e:
            logger.error(f"❌ Fehler beim Toggle der Suche: {e}")
    
    def _show_advanced_search(self):
        """Zeige erweiterte Suchparameter"""
        try:
            logger.info("🔎 Öffne erweiterten Filter-Dialog...")
            
            # Import des erweiterten Filter-Dialogs
            from pdvm_extended_filter_dialog import show_pdvm_extended_filter_dialog
            
            # WICHTIG: Filter arbeitet auf ALLEN Spalten der BASIS_MATRIX!
            # Aber Dialog zeigt nur SICHTBARE Spalten für bessere UX
            all_columns = []
            visible_columns = []
            
            try:
                # 1. Hole ALLE Spalten aus MatrixManager (für Filter)
                if hasattr(self, 'matrix_manager') and self.matrix_manager:
                    all_columns = self.matrix_manager.columns.copy()
                    logger.info(f"📊 ALLE Spalten aus MatrixManager: {len(all_columns)} Spalten")
                
                # 2. Hole SICHTBARE Spalten aus GCS (für Dialog-Anzeige)
                gcs_columns = self._get_visible_columns_from_gcs()
                logger.info(f"�️ SICHTBARE Spalten aus GCS: {len(gcs_columns)} Spalten")
                
                for col_name in gcs_columns:
                    # Generiere Display-Name: 'familienname_show' → 'Familienname'
                    display_name = col_name.replace('_show', '').replace('_original', '').replace('_', ' ').title()
                    visible_columns.append((col_name, display_name))
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Holen der Spalten: {e}")
                # Fallback: Verwende aktuell angezeigte Spalten
                if hasattr(self, 'table') and self.table.columnCount() > 0:
                    for col_idx in range(self.table.columnCount()):
                        header = self.table.horizontalHeaderItem(col_idx)
                        if header:
                            col_name = header.text().lower().replace(' ', '_') + '_show'
                            visible_columns.append((col_name, header.text()))
            
            if not visible_columns:
                logger.warning("⚠️ Keine sichtbaren Spalten gefunden")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Keine Spalten", "Keine sichtbaren Spalten für Filter gefunden!")
                return
            
            logger.info(f"📋 Filter-Dialog öffnet mit {len(visible_columns)} sichtbaren Spalten")
            logger.info(f"🎯 Filter wird auf {len(all_columns)} ALLE Spalten angewendet")
            
            # Dialog anzeigen - zeigt nur sichtbare Spalten, filtert aber auf ALLEN
            result = show_pdvm_extended_filter_dialog(self, self.view_guid, visible_columns)
            
            if result:
                logger.info("✅ Erweiterter Filter angewendet")
                self.refresh_table_direct()
            
        except Exception as e:
            logger.error(f"❌ Fehler bei erweiterten Suchparametern: {e}")
    
    def _show_sorting_dialog(self):
        """📊 Zeige Sortierung & Gruppierung Dialog"""
        try:
            from advanced_sort_dialog import AdvancedSortDialog
            from PyQt5.QtWidgets import QDialog
            
            logger.info("📊 Öffne Sortierung & Gruppierung Dialog...")
            
            # Controls-Config holen
            controls_config = getattr(self, 'controls_config', {})
            if not controls_config:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Fehler", "Keine Controls-Konfiguration verfügbar")
                return
            
            # Dialog öffnen
            dialog = AdvancedSortDialog(self.view_guid, controls_config, self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Sortier-Konfiguration holen
                sort_config = dialog.get_sort_config()
                sum_columns = dialog.get_sum_columns()
                
                logger.info(f"📊 Sortier-Konfiguration: {sort_config}")
                logger.info(f"Σ Summierungs-Spalten: {sum_columns}")
                
                # Sortierung anwenden
                self._apply_sorting_config(sort_config, sum_columns)
                
                logger.info("✅ Sortierung angewendet")
            else:
                logger.info("ℹ️ Sortierungs-Dialog abgebrochen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Sortierung & Gruppierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Fehler", f"Sortierungs-Dialog Fehler:\n{e}")
    
    def _apply_sorting_config(self, sort_config: list, sum_columns: list):
        """Wendet Sortierungs-Konfiguration an"""
        try:
            from sort_manager import get_sort_manager
            from pdvm_matrix_manager import get_matrix_manager
            
            # Matrix-Manager holen
            matrix_manager = get_matrix_manager(self.view_guid)
            if not matrix_manager:
                logger.error("❌ Matrix-Manager nicht verfügbar")
                return
            
            # Sort-Manager holen
            sort_manager = get_sort_manager(self.view_guid)
            sort_manager.set_controls_config(self.controls_config)
            
            # Filter-Matrix holen (Input für Sortierung)
            filter_matrix = matrix_manager.get_filter_data()
            
            if not filter_matrix:
                logger.warning("⚠️ Keine Filter-Matrix verfügbar")
                return
            
            # Erweiterte Sortierung durchführen
            sorted_matrix = sort_manager.advanced_sort(filter_matrix, sort_config, sum_columns)
            
            # Sort-Matrix in Matrix-Manager setzen
            matrix_manager.set_sort_data(sorted_matrix)
            
            # Tabelle aktualisieren
            self.refresh_table_direct()
            
            logger.info(f"✅ Sortierung angewandt: {len(sorted_matrix)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _enable_all_columns_sortable(self):
        """🔧 Setzt alle Spalten als sortierbar"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from PyQt5.QtWidgets import QMessageBox
            import json
            
            logger.info("🔧 Aktiviere Sortierung für alle Spalten...")
            
            # GCS holen
            gcs = get_gcs()
            if not gcs:
                QMessageBox.warning(self, "Fehler", "GCS nicht verfügbar")
                return
            
            # Benutzer bestätigen lassen
            reply = QMessageBox.question(
                self,
                "Alle Spalten sortierbar machen?",
                "Möchten Sie alle Spalten dieser View als sortierbar markieren?\n\n"
                "Dies setzt für alle Controls:\n"
                "• sortable = true\n"
                "• sortDirection = 'asc' (oder 'desc' für Datum/Alter)\n"
                "• sortByOriginal = true (nur für Datumsfelder)\n\n"
                "Die Änderungen werden sofort gespeichert.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                logger.info("ℹ️ Benutzer hat Aktion abgebrochen")
                return
            
            # Projektions-Tabelle holen ODER aus controls_config ableiten
            projection_table = gcs.get_projection_table(self.view_guid, "table")
            
            # FALLBACK: Wenn keine Projektions-Tabelle existiert, verwende controls_config
            if not projection_table:
                logger.warning("⚠️ Keine Projektions-Tabelle gefunden - verwende controls_config als Fallback")
                
                if hasattr(self, 'controls_config') and self.controls_config:
                    # Verwende alle Keys aus controls_config
                    projection_table = list(self.controls_config.keys())
                    logger.info(f"✅ Fallback: {len(projection_table)} Controls aus controls_config geladen")
                else:
                    QMessageBox.warning(self, "Fehler", "Keine Projektions-Tabelle und keine Controls-Config gefunden")
                    return
            
            logger.info(f"🚀 Aktiviere Sortierung für {len(projection_table)} Controls...")
            
            updated_count = 0
            error_count = 0
            
            # Durchlaufe alle Controls
            for control_key in projection_table:
                try:
                    # Hole Control-JSON
                    control_data = gcs._db.get_value(self.view_guid, control_key)
                    
                    if not control_data or len(control_data) != 2:
                        continue
                    
                    control_json, _ = control_data
                    
                    if not control_json:
                        continue
                    
                    # Parse JSON
                    control = json.loads(control_json)
                    
                    # Stelle sicher, dass ui-Dict existiert
                    if 'ui' not in control:
                        control['ui'] = {}
                    
                    # Bestimme Default-Werte
                    if 'datum' in control_key.lower() or 'alter' in control_key.lower():
                        default_direction = 'desc'
                    else:
                        default_direction = 'asc'
                    
                    default_by_original = (
                        'geburtsdatum_show' in control_key and 
                        control_key.endswith('_show')
                    )
                    
                    # Aktualisiere Sortier-Einstellungen
                    control['ui']['sortable'] = True
                    control['ui']['sortDirection'] = control['ui'].get('sortDirection', default_direction)
                    control['ui']['sortByOriginal'] = control['ui'].get('sortByOriginal', default_by_original)
                    
                    # Speichere zurück
                    updated_json = json.dumps(control, ensure_ascii=False)
                    gcs._db.set_value(self.view_guid, control_key, updated_json)
                    
                    updated_count += 1
                    logger.info(f"✅ {control_key}: sortable=true")
                    
                except Exception as e:
                    logger.error(f"❌ Fehler bei {control_key}: {e}")
                    error_count += 1
            
            # Rebuild Projektions-Tabellen
            logger.info("🔄 Rebuild Projektions-Tabellen...")
            gcs.rebuild_projection_tables(self.view_guid)
            
            # Controls-Config neu laden
            if hasattr(self, 'controls_config'):
                for control_key in projection_table:
                    control_data = gcs._db.get_value(self.view_guid, control_key)
                    if control_data and len(control_data) == 2:
                        control_json, _ = control_data
                        if control_json:
                            self.controls_config[control_key] = json.loads(control_json)
            
            # Erfolgs-Meldung
            message = f"✅ Update abgeschlossen!\n\n"
            message += f"• {updated_count} Controls aktualisiert\n"
            if error_count > 0:
                message += f"• {error_count} Fehler aufgetreten\n"
            message += f"\nAlle Spalten sind jetzt sortierbar."
            
            QMessageBox.information(self, "Sortierbar-Update", message)
            
            logger.info(f"🎉 Sortierbar-Update abgeschlossen: {updated_count} erfolgreich, {error_count} Fehler")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei _enable_all_columns_sortable: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Fehler", f"Fehler beim Sortierbar-Update:\n{e}")
    
    def _show_settings(self):
        """Zeige Einstellungen-Dialog"""
        try:
            logger.info("⚙️ Öffne Einstellungen...")
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Einstellungen", "Einstellungen-Dialog wird implementiert...")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Einstellungen: {e}")
    
    def _show_column_management(self):
        """Zeige Spalten-Verwaltung"""
        try:
            logger.info("📋 Öffne Spalten-Verwaltung...")
            
            from column_management_dialog import show_column_management_dialog
            
            # Controls-Config verwenden
            controls_config = getattr(self, 'controls_config', {})
            
            # KORREKTUR: Parameter heißt 'current_mode' nicht 'context'
            result = show_column_management_dialog(
                parent=self,
                view_guid=self.view_guid,
                controls_config=controls_config,
                current_mode="table"
            )
            
            if result:
                logger.info("✅ Spalten-Konfiguration geändert")
                # Refresh mit neuer Spalten-Konfiguration
                self.refresh_table_direct()
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Verwaltung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _toggle_expert_mode(self):
        """Toggle Expert Mode über Menü - NUR für mode='admin' - LINEARE SPALTEN-PROJEKTION"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from PyQt5.QtWidgets import QMessageBox
            gcs = get_gcs()
            
            if not gcs:
                logger.error("❌ GCS nicht verfügbar für Expert Mode Toggle")
                return
            
            # Prüfe ob Benutzer Admin ist
            user_mode = gcs.mode
            if user_mode != 'admin':
                logger.warning(f"⚠️ Expert Mode Toggle verweigert - Benutzer ist kein Admin (mode={user_mode})")
                QMessageBox.warning(
                    self,
                    "Zugriff verweigert",
                    "Expert Mode kann nur von Administratoren aktiviert werden."
                )
                return
                
            # Expert Mode umschalten
            old_mode = gcs.expert_mode
            gcs.expert_mode = not old_mode
            logger.info(f"🎓 Expert Mode: {old_mode} → {gcs.expert_mode} (Admin-Benutzer)")
            
            # Header-Label aktualisieren (zeigt/versteckt Stichtag)
            self._update_header_label()
            
            # 🎯 KRITISCH: Spalten-Projektion neu anwenden
            self.refresh_table_direct()
            
            # Status-Meldung
            status = "aktiviert" if gcs.expert_mode else "deaktiviert"
            mode_info = "Alle Spalten (inkl. Original-Felder)" if gcs.expert_mode else "Nur konfigurierte Spalten"
            QMessageBox.information(
                self,
                "Expert Mode",
                f"Expert Mode wurde {status}.\n\nAnzeige: {mode_info}"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Expert Mode Toggle: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _update_header_label(self):
        """Aktualisiere Header-Label basierend auf Expert Mode"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                return
                
            # Basis-Titel
            base_title = getattr(self, 'title', f"View: {self.view_guid}")
            
            # Expert Mode: Zeige Stichtag im Header
            if gcs.expert_mode and hasattr(gcs, 'st_inst') and gcs.st_inst:
                formatted_stichtag = getattr(gcs.st_inst, 'FormTimeStamp', str(gcs.st_inst.PdvmDateTime))
                title_text = f"{base_title} - 🎓 Expert Mode - Stichtag: {formatted_stichtag}"
            else:
                title_text = base_title
                
            if hasattr(self, 'header_label') and self.header_label:
                self.header_label.setText(title_text)
                logger.info(f"🔧 Header aktualisiert: Expert Mode = {gcs.expert_mode}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Headers: {e}")
    

    
    def _refresh_data(self):
        """Daten neu laden"""
        try:
            logger.info("🔄 Aktualisiere Daten...")
            
            # Matrix neu erstellen
            self._build_matrix()
            
            # Tabelle aktualisieren
            self.refresh_table_direct()
            
            logger.info("✅ Daten aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Daten-Refresh: {e}")
    
    def _export_data(self):
        """Daten als CSV exportieren - exportiert aktuell gefilterte/sortierte Daten"""
        try:
            logger.info("📤 CSV-Export gestartet...")
            
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            import csv
            from datetime import datetime
            
            # Hole Matrix-Manager
            if not hasattr(self, 'matrix_manager') or not self.matrix_manager:
                QMessageBox.warning(self, "Export-Fehler", "Keine Daten zum Exportieren verfügbar")
                return
            
            # Hole gefilterte/sortierte Daten aus SORT_MATRIX
            export_data = self.matrix_manager.matrix_sort
            if not export_data:
                QMessageBox.warning(self, "Export-Fehler", "Keine Daten zum Exportieren (Matrix leer)")
                return
            
            # Hole sichtbare Spalten
            visible_columns = self._get_visible_columns_from_gcs()
            if not visible_columns:
                QMessageBox.warning(self, "Export-Fehler", "Keine sichtbaren Spalten definiert")
                return
            
            # Standard-Dateiname mit Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"export_{self.view_guid[:8]}_{timestamp}.csv"
            
            # Datei-Dialog öffnen
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV-Export speichern",
                default_filename,
                "CSV Dateien (*.csv);;Alle Dateien (*.*)"
            )
            
            if not file_path:
                logger.info("ℹ️ Export vom Benutzer abgebrochen")
                return
            
            # CSV schreiben
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:  # utf-8-sig für Excel-Kompatibilität
                writer = csv.writer(csvfile, delimiter=';')  # Semikolon für deutsche Excel-Version
                
                # Header schreiben (mit schönen Namen aus controls_config)
                header_row = []
                for col in visible_columns:
                    control = self.controls_config.get(col, {})
                    header_name = control.get('name', col)
                    header_row.append(header_name)
                writer.writerow(header_row)
                
                # Datenzeilen schreiben
                for row in export_data:
                    data_row = []
                    for col in visible_columns:
                        value = row.get(col, '')
                        # Konvertiere zu String, behandle None
                        data_row.append(str(value) if value is not None else '')
                    writer.writerow(data_row)
            
            # Erfolgs-Meldung
            row_count = len(export_data)
            col_count = len(visible_columns)
            QMessageBox.information(
                self,
                "Export erfolgreich",
                f"✅ {row_count} Zeilen und {col_count} Spalten erfolgreich exportiert!\n\nDatei: {file_path}"
            )
            logger.info(f"✅ CSV-Export erfolgreich: {row_count} Zeilen → {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim CSV-Export: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Export:\n{e}")
    
    def _perform_global_search(self):
        """
        V3 SCHNELLSUCHE: Führe Schnellsuche durch mit SchnellsucheManager
        
        - NUR bei KLICK auf Lupe ausgeführt (nicht bei jedem Buchstaben!)
        - SchnellsucheManager speichert AUTONOM: Parameter + s_string + s_source
        - GCS: save_all_values() für Persistierung
        - Matrix Manager: apply_filter() mit filter_source='schnell'
        """
        from PyQt5.QtWidgets import QMessageBox
        
        try:
            if not hasattr(self, 'search_input'):
                error_msg = "FEHLER: Suchfeld nicht initialisiert!"
                logger.error(f"❌ {error_msg}")
                QMessageBox.critical(self, "Schnellsuche Fehler", error_msg)
                return
                
            search_text = self.search_input.text().strip()
            logger.info(f"🔍 V3 SCHNELLSUCHE: '{search_text}'")
            
            if not search_text:
                # Leere Suche = Filter zurücksetzen
                self._clear_search()
                return
            
            # V3: Verwende SchnellsucheManager
            from schnellsuche_manager import SchnellsucheManager
            
            # Matrix Manager DIREKT von self holen (nicht von Controller!)
            if not hasattr(self, 'matrix_manager') or not self.matrix_manager:
                error_msg = "FEHLER: Matrix Manager nicht verfügbar!\n\nDie Schnellsuche kann nicht ausgeführt werden."
                logger.error(f"❌ {error_msg}")
                QMessageBox.critical(self, "Schnellsuche Fehler", error_msg)
                return
            
            matrix_manager = self.matrix_manager
            
            # SchnellsucheManager erstellen und ausführen
            manager = SchnellsucheManager(
                view_guid=self.view_guid,
                matrix_manager=matrix_manager
            )
            
            success = manager.execute_schnellsuche(search_text)
            
            if success:
                logger.info("✅ V3 Schnellsuche erfolgreich - PERSISTENT!")
                self.refresh_table_direct()
            else:
                error_msg = f"FEHLER: Schnellsuche konnte nicht ausgeführt werden!\n\nSuchtext: '{search_text}'\n\nBitte Log-Datei prüfen."
                logger.error(f"❌ {error_msg}")
                QMessageBox.warning(self, "Schnellsuche Fehler", error_msg)
                
        except Exception as e:
            error_msg = f"KRITISCHER FEHLER bei Schnellsuche:\n\n{str(e)}\n\nBitte Log-Datei prüfen!"
            logger.error(f"❌ {error_msg}", exc_info=True)
            QMessageBox.critical(self, "Schnellsuche Fehler", error_msg)
    
    # V3: _on_search_text_changed ENTFERNT
    # Schnellsuche wird NUR bei ENTER oder Lupe-Klick ausgeführt (nicht bei jedem Buchstaben!)
    
    # V3: ALTE _clear_search ENTFERNT (nutzte LinearFilterExecutionManager)
    
    def _clear_search(self):
        """
        V3 FILTER-RESET: Lösche ALLE Filter über ZENTRALEN FilterResetManager
        
        - Löscht s_string, s_source und ALLE Filter-Parameter (schnell/einfach/komplex)
        - Ruft save_all_values() auf für Persistierung
        - Matrix Manager: apply_filter(None) für kompletten Reset
        """
        from PyQt5.QtWidgets import QMessageBox
        
        try:
            if hasattr(self, 'search_input'):
                self.search_input.clear()
            
            # Matrix Manager DIREKT von self holen (nicht von Controller!)
            if not hasattr(self, 'matrix_manager') or not self.matrix_manager:
                error_msg = "FEHLER: Matrix Manager nicht verfügbar!\n\nDer Filter kann nicht zurückgesetzt werden."
                logger.error(f"❌ {error_msg}")
                QMessageBox.critical(self, "Filter-Reset Fehler", error_msg)
                return
            
            # V3: ZENTRALER FilterResetManager für ALLE Filter-Typen
            from filter_reset_manager import get_filter_reset_manager
            
            reset_manager = get_filter_reset_manager(self.view_guid, self.matrix_manager)
            
            # ALLE Filter löschen (schnell + einfach + komplex)
            success = reset_manager.reset_all_filters()
            
            if success:
                logger.info("🧹 V3 ALLE Filter gelöscht - PERSISTENT!")
            else:
                error_msg = "WARNUNG: Filter-Reset konnte nicht vollständig ausgeführt werden.\n\nBitte Log-Datei prüfen."
                logger.warning(f"⚠️ {error_msg}")
                QMessageBox.warning(self, "Filter-Reset Warnung", error_msg)
            
            self.refresh_table_direct()
            
        except Exception as e:
            error_msg = f"KRITISCHER FEHLER beim Filter-Reset:\n\n{str(e)}\n\nBitte Log-Datei prüfen!"
            logger.error(f"❌ {error_msg}", exc_info=True)
            QMessageBox.critical(self, "Filter-Reset Fehler", error_msg)
    
    def _update_row_count_display(self, count):
        """Aktualisiere Zeilen-Anzahl Display"""
        try:
            if hasattr(self, 'lbl_row_count'):
                self.lbl_row_count.setText(f"{count} Zeilen")
        except Exception as e:
            logger.error(f"❌ Fehler beim Update der Zeilen-Anzeige: {e}")
    
    def _setup_header_click_direct(self):
        """Header-Click DIREKT in derselben Klasse"""
        try:
            if hasattr(self.table, 'horizontalHeader'):
                header = self.table.horizontalHeader()
                # DIREKT in derselben Klasse - KEIN Weiterleitung!
                header.sectionClicked.connect(self._on_header_clicked_direct)
                logger.info("✅ Header-Click DIREKT in PdvmViewDialog verbunden")
            else:
                logger.warning("⚠️ Tabelle hat keinen Header")
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Click Setup: {e}")
    
    def refresh_table_direct(self):
        """Tabelle direkt aktualisieren ohne Display-Klasse"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            from PyQt5.QtWidgets import QTableWidgetItem
            
            logger.info("🔧 Starte direkte Tabellen-Aktualisierung...")
            
            # Prüfe ob Tabelle existiert
            if not hasattr(self, 'table') or self.table is None:
                logger.error("❌ Tabelle nicht verfügbar!")
                return
            
            gcs = get_gcs()
            
            # Matrix-Manager für finale Daten verwenden
            from pdvm_matrix_manager import get_matrix_manager
            matrix_manager = get_matrix_manager(self.view_guid)
            
            if matrix_manager:
                final_data = matrix_manager.get_final_data()
                logger.info(f"📊 Matrix-Manager Daten: {len(final_data) if final_data else 0} Zeilen")
            else:
                # Fallback: Direkte Matrix verwenden
                if hasattr(self, 'display_matrix') and self.display_matrix:
                    final_data = [row for row in self.display_matrix if row.get('display', True)]
                    logger.info(f"📊 Fallback Daten: {len(final_data)} Zeilen")
                else:
                    final_data = []
                    logger.warning("⚠️ Keine Daten verfügbar!")
            
            if not final_data:
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                if hasattr(self, 'status_label') and self.status_label:
                    self.status_label.setText("Keine Daten")
                logger.info("ℹ️ Tabelle geleert - keine Daten")
                return
            
            # Sichtbare Spalten bestimmen
            visible_columns = self._get_visible_columns_from_gcs()
            
            # FALLBACK: Wenn keine sichtbaren Spalten definiert, verwende alle verfügbaren
            if not visible_columns and final_data:
                visible_columns = list(final_data[0].keys())[:10]  # Erste 10 Spalten als Fallback
                logger.warning(f"⚠️ Fallback Spalten verwendet: {len(visible_columns)} Spalten")
            
            if not visible_columns:
                logger.error("❌ Keine Spalten verfügbar!")
                return
            
            # Tabelle dimensionieren
            self.table.setRowCount(len(final_data))
            self.table.setColumnCount(len(visible_columns))
            
            # 🎯 SPALTEN-HEADER GENERIERUNG mit Expert Mode Support
            headers = []
            for col in visible_columns:
                if hasattr(self, 'controls_config') and self.controls_config:
                    control = self.controls_config.get(col, {})
                    base_name = control.get('name', col)
                    
                    # Spalten-Typ bestimmen
                    if control.get('control_type') == 'original':
                        header_text = f"{base_name} (Orig.)"
                    else:
                        header_text = base_name
                    
                    # 🎓 EXPERT MODE: Technische Namen hinzufügen
                    if gcs and gcs.expert_mode:
                        header_text += f"\n[{col}]"
                        
                        # Zusätzliche technische Info für Original-Spalten
                        if control.get('control_type') == 'original':
                            field_name = control.get('field_name', '')
                            group_name = control.get('group_name', '')
                            if field_name and group_name:
                                header_text += f"\n({group_name}.{field_name})"
                else:
                    # Fallback Header
                    header_text = col
                    if gcs and gcs.expert_mode:
                        header_text += f"\n[{col}]"
                
                headers.append(header_text)
            
            self.table.setHorizontalHeaderLabels(headers)
            logger.info(f"🔧 Header gesetzt: Expert Mode = {gcs.expert_mode if gcs else False}")
            
            # 🏷️ HEADER-TOOLTIPS: Control-Keys in Spaltenköpfen
            for col_idx, col_name in enumerate(visible_columns):
                # Tooltip mit Control-Key erstellen
                tooltip = f"Control-Key: {col_name}"
                
                # Zusätzliche technische Info im Tooltip
                if hasattr(self, 'controls_config') and self.controls_config:
                    control = self.controls_config.get(col_name, {})
                    control_type = control.get('control_type', '')
                    field_name = control.get('field_name', '')
                    group_name = control.get('group_name', '')
                    
                    if control_type:
                        tooltip += f"\nTyp: {control_type}"
                    if field_name and group_name:
                        tooltip += f"\nFeld: {group_name}.{field_name}"
                
                # Tooltip auf Header-Item setzen
                header_item = self.table.horizontalHeaderItem(col_idx)
                if header_item:
                    header_item.setToolTip(tooltip)
                    logger.debug(f"🏷️ Header-Tooltip gesetzt für Spalte {col_idx}: {col_name}")
            
            # Debug: Erste 3 Header ausgeben
            if headers:
                sample_headers = headers[:3]
                logger.info(f"📋 Beispiel-Header: {sample_headers}")
            
            # 📊 DATEN EINFÜGEN mit Abdatum-Tooltips
            for row_idx, row_data in enumerate(final_data):
                for col_idx, col_name in enumerate(visible_columns):
                    value = row_data.get(col_name, '')
                    # Sichere Item-Erstellung
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    
                    # 🏷️ ZELLEN-TOOLTIP: Abdatum aus Matrix-Ebene
                    abdatum_key = f"{col_name}_formatiertes_abdatum"
                    abdatum = row_data.get(abdatum_key, '')
                    
                    if abdatum:
                        tooltip = f"Abdatum: {abdatum}"
                        item.setToolTip(tooltip)
                        logger.debug(f"🏷️ Zellen-Tooltip gesetzt für [{row_idx},{col_idx}]: {abdatum}")
                    
                    self.table.setItem(row_idx, col_idx, item)
            
            # Header anpassen
            self.table.resizeColumnsToContents()
            
            # KRITISCH: Tabelle explizit sichtbar machen nach Datenaktualisierung
            self.table.setVisible(True)
            self.table.show()
            self.table.update()
            logger.info(f"🔧 Tabelle nach Datenaktualisierung sichtbar: {self.table.isVisible()}")
            
            # Status aktualisieren
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"Zeilen: {len(final_data)}, Spalten: {len(visible_columns)}")
            
            logger.info(f"✅ Tabelle direkt aktualisiert: {len(final_data)} Zeilen, {len(visible_columns)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei direkter Tabellen-Aktualisierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _get_visible_columns_from_gcs(self):
        """
        🎯 SPALTEN-PROJEKTION: Sichtbare Spalten aus Projektions-Tabellen holen
        
        LINEARE ARCHITEKTUR V3:
        - Verwendet fertige Projektions-Tabellen aus GCS (bereits sortiert!)
        - StandardMode: table_standard Projektion
        - ExpertMode: table_expert Projektion
        - Keine manuelle Filterung mehr - alles in Projektion vorbereitet
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar für Spalten-Projektion")
                return []
            
            if not hasattr(self, 'view_guid') or not self.view_guid:
                logger.warning("⚠️ View-GUID nicht verfügbar für Projektion")
                return []
            
            # 🎯 PROJEKTION AUS GCS HOLEN (bereits sortiert nach display_order!)
            if gcs.expert_mode:
                projection = gcs.get_projection_table(self.view_guid, 'table_expert')
                logger.info(f"🎓 ExpertMode Projektion geladen: {len(projection)} Spalten")
            else:
                projection = gcs.get_projection_table(self.view_guid, 'table_standard')
                logger.info(f"👤 StandardMode Projektion geladen: {len(projection)} Spalten")
            
            if not projection:
                logger.warning(f"⚠️ Keine Projektion gefunden - Rebuild notwendig")
                gcs.rebuild_projection_tables(self.view_guid)
                projection = gcs.get_projection_table(self.view_guid, 
                                                    'table_expert' if gcs.expert_mode else 'table_standard')
            
            logger.info(f"✅ Spalten-Projektion: {projection[:5]}..." if len(projection) > 5 else f"✅ Spalten-Projektion: {projection}")
            return projection
        
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Projektion: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _on_header_clicked_direct(self, logical_index):
        """
        🎯 EINFACHE SORTIERUNG: Header-Click mit SortManager
        
        LINEARE ARCHITEKTUR:
        - Verwendet SortManager für Sortierung
        - Beachtet sortDirection und sortByOriginal
        - Persistiert neue Richtung in GCS
        
        Args:
            logical_index: Index der geklickten Spalte
        """
        try:
            # Matrix-Manager über Factory-Funktion holen
            from pdvm_matrix_manager import get_matrix_manager
            matrix_manager = get_matrix_manager(self.view_guid)
            
            if not matrix_manager:
                logger.warning("⚠️ Matrix-Manager nicht verfügbar für Sortierung")
                return
            
            # Sichtbare Spalten holen
            visible_columns = self._get_visible_columns_from_gcs()
            
            if logical_index >= len(visible_columns):
                logger.warning(f"⚠️ Ungültiger Spalten-Index: {logical_index}")
                return
            
            # Column-Key aus Index ermitteln
            column_key = visible_columns[logical_index]
            
            logger.info(f"🔄 Header-Click auf Spalte {logical_index}: {column_key}")
            
            # Sort-Manager holen
            from sort_manager import get_sort_manager
            sort_manager = get_sort_manager(self.view_guid)
            sort_manager.set_controls_config(self.controls_config)
            
            # Filter-Matrix holen (Input für Sortierung)
            filter_matrix = matrix_manager.get_filter_data()
            
            if not filter_matrix:
                logger.warning("⚠️ Keine Filter-Matrix verfügbar")
                return
            
            # Einfache Sortierung durchführen (toggle_direction=True)
            sorted_matrix = sort_manager.simple_sort(filter_matrix, column_key, toggle_direction=True)
            
            # Sort-Matrix in Matrix-Manager setzen
            matrix_manager.set_sort_data(sorted_matrix)
            
            # Tabelle aktualisieren
            self.refresh_table_direct()
            
            logger.info(f"✅ Einfache Sortierung angewandt: {column_key}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Click Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _refresh_table_from_matrix(self, matrix_manager=None):
        """
        Tabelle aus Matrix-Manager-Daten aktualisieren
        """
        try:
            # Matrix-Manager verwenden (Parameter oder Factory)
            if not matrix_manager:
                from pdvm_matrix_manager import get_matrix_manager
                matrix_manager = get_matrix_manager(self.view_guid)
            
            if not matrix_manager:
                logger.warning("⚠️ Kein Matrix-Manager verfügbar")
                return
            
            # Finale Daten aus Matrix-Manager holen
            final_data = matrix_manager.get_final_data()
            
            if not final_data:
                logger.warning("⚠️ Keine finalen Daten vom Matrix-Manager")
                return
            
            # Tabelle leeren
            self.table.setRowCount(0)
            
            # Neue Daten einfügen
            self.table.setRowCount(len(final_data))
            
            for row_idx, row_data in enumerate(final_data):
                for col_idx in range(self.table.columnCount()):
                    header_item = self.table.horizontalHeaderItem(col_idx)
                    if header_item:
                        column_name = header_item.text()
                        value = row_data.get(column_name, '')
                        from PyQt5.QtWidgets import QTableWidgetItem
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            logger.info(f"✅ Tabelle aktualisiert: {len(final_data)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Tabellen-Aktualisierung: {e}")


class PdvmViewDisplay(QWidget):
    """
    SAUBERES UI-Display für PdvmViewDialog
    """
    
    def __init__(self, view_dialog):
        super().__init__(view_dialog.parent)
        self.view_dialog = view_dialog
        self.header_label = None
        
        # NEUES LINEARES FILTER-SYSTEM
        self.linear_filter = None  # Wird nach table-Erstellung initialisiert
        
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
        
        # Header-Click Handler für einfache Sortierung
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        
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
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # Mehrfach-Auswahl mit Strg/Shift
        
        # Header-Schrift konfigurieren
        header_font = QFont("Segoe UI", 10, QFont.Bold)
        self.table.horizontalHeader().setFont(header_font)
        
        layout.addWidget(self.table)
        
        # SORTIERUNGS-MANAGER: Header-Click an view_dialog weiterleiten  
        self._setup_header_click_forwarding()
        
        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
    def _setup_header_click_forwarding(self):
        """Header-Click von PdvmViewDisplay an PdvmViewDialog weiterleiten"""
        try:
            if hasattr(self.table, 'horizontalHeader'):
                header = self.table.horizontalHeader()
                # Weiterleitung an view_dialog's Methode
                header.sectionClicked.connect(self.view_dialog._on_header_clicked_direct)
                logger.info("✅ Header-Click von Display an Dialog weitergeleitet")
            else:
                logger.warning("⚠️ Tabelle hat keinen Header für Click-Weiterleitung")
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Click Weiterleitung: {e}")
    
    def keyPressEvent(self, event):
        """
        Strg+C Handler - Markierte Zeilen in Zwischenablage kopieren
        Format: Tab-separierte Spalten, Zeilen durch Newline getrennt
        """
        try:
            from PyQt5.QtGui import QKeySequence
            from PyQt5.QtWidgets import QApplication
            
            # Prüfe ob Strg+C gedrückt wurde
            if event.matches(QKeySequence.Copy):
                logger.info("📋 Strg+C gedrückt - Kopiere markierte Zeilen...")
                
                # Hole markierte Zeilen
                selected_ranges = self.table.selectedRanges()
                if not selected_ranges:
                    logger.info("ℹ️ Keine Zeilen markiert")
                    return
                
                # Sammle Daten aus allen markierten Bereichen
                copied_data = []
                
                # Header-Zeile hinzufügen
                headers = []
                for col in range(self.table.columnCount()):
                    header_item = self.table.horizontalHeaderItem(col)
                    if header_item:
                        # Entferne Zeilenumbrüche aus Header (für ExpertMode)
                        header_text = header_item.text().replace('\n', ' ')
                        headers.append(header_text)
                    else:
                        headers.append(f"Spalte_{col}")
                copied_data.append('\t'.join(headers))
                
                # Sammle alle markierten Zeilen (ohne Duplikate)
                selected_rows = set()
                for selected_range in selected_ranges:
                    for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                        selected_rows.add(row)
                
                # Sortiere Zeilen für konsistente Reihenfolge
                for row in sorted(selected_rows):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            row_data.append(item.text())
                        else:
                            row_data.append('')
                    copied_data.append('\t'.join(row_data))
                
                # In Zwischenablage kopieren
                clipboard_text = '\n'.join(copied_data)
                QApplication.clipboard().setText(clipboard_text)
                
                logger.info(f"✅ {len(selected_rows)} Zeilen in Zwischenablage kopiert")
                logger.info(f"📊 Daten-Vorschau (erste 200 Zeichen):\n{clipboard_text[:200]}")
                
                # Optional: Kurze Bestätigung im Status-Label anzeigen
                if hasattr(self, 'status_label') and self.status_label:
                    old_text = self.status_label.text()
                    self.status_label.setText(f"✅ {len(selected_rows)} Zeilen kopiert")
                    # Nach 2 Sekunden zurücksetzen
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(2000, lambda: self.status_label.setText(old_text))
                
                return
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Kopieren: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Standard-Event-Handling fortsetzen
        super().keyPressEvent(event)
    
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
        # GCS für ExpertMode und andere Features laden
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
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
            # WICHTIG: Control-Key IMMER im ToolTip (für Filter-Suche)
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
            # Projektionen werden aus der SORT_MATRIX des PdvmMatrixManagers angewendet
            if gcs.expert_mode:
                projection = gcs.get_projection_table(view_guid, 'table_expert')
            else:
                projection = gcs.get_projection_table(view_guid, 'table_standard')
            
            if projection:
                mode_info = "Expert" if gcs.expert_mode else "Standard"
                logger.debug(f"✅ Tabellen-Projektion ({mode_info}) für SORT_MATRIX: {len(projection)} Spalten")
                logger.debug(f"📋 Projektions-Spalten: {projection[:5]}..." if len(projection) > 5 else f"📋 Projektions-Spalten: {projection}")
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
        """Reset alle Zeilen sichtbar - wird vom linearen System automatisch aufgerufen"""
        try:
            # Filter-Integration sicherstellen
            if not self.linear_filter and hasattr(self, 'table'):
                view_guid = getattr(self.view_dialog, 'view_guid', None)
                self.linear_filter = create_pdvm_linear_filter(self.table, view_guid)
            
            if self.linear_filter:
                return self.linear_filter.clear_all_filters()
            else:
                # Fallback
                for row in range(self.table.rowCount()):
                    self.table.setRowHidden(row, False)
                logger.info(f"✅ Fallback: Alle {self.table.rowCount()} Zeilen sichtbar")
        except Exception as e:
            logger.error(f"❌ Fehler bei show_all_rows: {e}")
    
    def _perform_search(self, search_text):
        """🎯 NEUE LINEARE SUCHE - verwendet Unified Linear Filter"""
        try:
            # Filter-Integration sicherstellen
            if not self.linear_filter and hasattr(self, 'table'):
                view_guid = getattr(self.view_dialog, 'view_guid', None)
                self.linear_filter = create_pdvm_linear_filter(self.table, view_guid)
                logger.info("✅ Linear Filter Integration für Search erstellt")
            
            if not self.linear_filter:
                logger.error("❌ Kein Linear Filter für Search verfügbar")
                return
            
            # LINEARE FILTER-ANWENDUNG
            success = self.linear_filter.apply_filter_unified(search_text)
            
            if success:
                visible_count = self.linear_filter.count_visible_rows()
                total_count = self.table.rowCount()
                
                # Suchstatus aktualisieren
                mode_text = "ausgeschlossen" if getattr(self, 'is_negative_search', False) else "gefunden"
                status_msg = f"{visible_count}/{total_count} Einträge {mode_text}"
                logger.info(f"✅ Lineare Suche erfolgreich: {status_msg}")
            else:
                logger.error("❌ Lineare Suche fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei linearer Suche: {e}")
        
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
            # GCS für ExpertMode-Prüfung laden
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
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

            # 3. Sortierung & Gruppierung (NEU!)
            settings_menu.addSeparator()
            action_sorting = QAction("📊 Sortierung & Gruppierung", self)
            action_sorting.triggered.connect(self._sortierung_verwaltung)
            settings_menu.addAction(action_sorting)
            
            # 3b. Alle Spalten sortierbar machen (Einmal-Aktion)
            action_enable_sort = QAction("🔧 Alle Spalten sortierbar machen", self)
            action_enable_sort.triggered.connect(self._enable_all_sortable)
            settings_menu.addAction(action_enable_sort)

            # 4. CSV-Export
            settings_menu.addSeparator()
            action_export = QAction("📤 Daten als CSV exportieren", self)
            action_export.triggered.connect(self._export_csv)
            settings_menu.addAction(action_export)

            # 5. ExpertMode (nur für Admins) - LINEAR
            # GCS direkt verwenden
            if gcs and gcs.is_admin:
                settings_menu.addSeparator()

                # ExpertMode Toggle (in self, nicht in self.view_dialog!)
                expert_text = "ExpertMode (ausschalten)" if gcs.expert_mode else "ExpertMode (einschalten)"
                action_expert = QAction(expert_text, self)
                action_expert.triggered.connect(self._toggle_expert_mode)
                settings_menu.addAction(action_expert)

            # 6. Zurücksetzen
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
            
            # Matrix Manager für V3 Filter-Manager holen (DIREKT von view_dialog!)
            matrix_manager = None
            if hasattr(self.view_dialog, 'matrix_manager') and self.view_dialog.matrix_manager:
                matrix_manager = self.view_dialog.matrix_manager
                logger.info(f"✅ Matrix Manager für SearchParameterDialog geholt")
            else:
                error_msg = "FEHLER: Matrix Manager nicht verfügbar!\n\nDer Suchparameter-Dialog kann nicht geöffnet werden."
                logger.error(f"❌ {error_msg}")
                QMessageBox.critical(self, "Suchparameter Fehler", error_msg)
                return
            
            # Modal-Dialog öffnen mit controls_config direkt übergeben (V3: MIT matrix_manager!)
            dialog = SearchParameterDialog(self, view_guid, self.view_dialog.controls_config, current_filters, matrix_manager)
            
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
    
    def _sortierung_verwaltung(self):
        """🎓 Erweiterte Sortierung mit Gruppierung und Summierung"""
        try:
            from advanced_sort_dialog import AdvancedSortDialog
            
            # View-GUID für Persistierung
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                QMessageBox.warning(self, "Fehler", "Keine View-GUID verfügbar für Sortierung")
                return
            
            # Controls-Config holen
            controls_config = getattr(self.view_dialog, 'controls_config', {})
            if not controls_config:
                QMessageBox.warning(self, "Fehler", "Keine Controls-Konfiguration verfügbar")
                return
            
            # Modal-Dialog öffnen
            dialog = AdvancedSortDialog(view_guid, controls_config, self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Sortier-Konfiguration holen
                sort_config = dialog.get_sort_config()
                sum_columns = dialog.get_sum_columns()
                
                logger.info(f"📊 Sortier-Konfiguration: {sort_config}")
                logger.info(f"Σ Summierungs-Spalten: {sum_columns}")
                
                # Erweiterte Sortierung anwenden
                self._apply_advanced_sort(sort_config, sum_columns)
                
                logger.info("✅ Erweiterte Sortierung angewendet")
            else:
                logger.info("ℹ️ Sortierungs-Dialog abgebrochen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Sortierungs-Verwaltung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.warning(self, "Fehler", f"Sortierungs-Verwaltung Fehler:\n{e}")
    
    def _apply_advanced_sort(self, sort_config: list, sum_columns: list):
        """
        Wendet erweiterte Sortierung auf View an
        
        Args:
            sort_config: Sortier-Konfiguration
            sum_columns: Spalten für Summierung
        """
        try:
            from sort_manager import get_sort_manager
            from pdvm_matrix_manager import get_matrix_manager
            
            # View-GUID holen
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                logger.error("❌ Keine View-GUID verfügbar")
                return
            
            # Matrix-Manager holen
            matrix_manager = get_matrix_manager(view_guid)
            if not matrix_manager:
                logger.error("❌ Matrix-Manager nicht verfügbar")
                return
            
            # Sort-Manager holen
            sort_manager = get_sort_manager(view_guid)
            sort_manager.set_controls_config(self.view_dialog.controls_config)
            
            # Filter-Matrix holen (Input für Sortierung)
            filter_matrix = matrix_manager.get_filter_data()
            
            if not filter_matrix:
                logger.warning("⚠️ Keine Filter-Matrix verfügbar")
                return
            
            # Erweiterte Sortierung durchführen
            sorted_matrix = sort_manager.advanced_sort(filter_matrix, sort_config, sum_columns)
            
            # Sort-Matrix in Matrix-Manager setzen
            matrix_manager.set_sort_data(sorted_matrix)
            
            # Tabelle aktualisieren
            self.refresh_table()
            
            logger.info(f"✅ Erweiterte Sortierung angewandt: {len(sorted_matrix)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der erweiterten Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _enable_all_sortable(self):
        """
        🔧 Setzt alle Spalten als sortierbar
        
        Einmal-Aktion die alle Controls in der Projektion als sortierbar markiert.
        Setzt auch sinnvolle Default-Werte für sortDirection und sortByOriginal.
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            import json
            
            # View-GUID holen
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                QMessageBox.warning(self, "Fehler", "Keine View-GUID verfügbar")
                return
            
            # GCS holen
            gcs = get_gcs()
            if not gcs:
                QMessageBox.warning(self, "Fehler", "GCS nicht verfügbar")
                return
            
            # Benutzer bestätigen lassen
            reply = QMessageBox.question(
                self,
                "Alle Spalten sortierbar machen?",
                "Möchten Sie alle Spalten dieser View als sortierbar markieren?\n\n"
                "Dies setzt für alle Controls:\n"
                "• sortable = true\n"
                "• sortDirection = 'asc' (oder 'desc' für Datum/Alter)\n"
                "• sortByOriginal = true (nur für Datumsfelder)\n\n"
                "Die Änderungen werden sofort gespeichert.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                logger.info("ℹ️ Benutzer hat Aktion abgebrochen")
                return
            
            # Projektions-Tabelle holen (alle sichtbaren Controls)
            projection_table = gcs.get_projection_table(view_guid, "table")
            
            if not projection_table:
                QMessageBox.warning(self, "Fehler", "Keine Projektions-Tabelle gefunden")
                return
            
            logger.info(f"🚀 Starte Sortierbar-Update für {len(projection_table)} Controls...")
            
            updated_count = 0
            error_count = 0
            
            # Durchlaufe alle Controls in der Projektion
            for control_key in projection_table:
                try:
                    # Hole Control-JSON aus Systemsteuerung-DB
                    control_data = gcs._db.get_value(view_guid, control_key)
                    
                    if not control_data or len(control_data) != 2:
                        logger.warning(f"⚠️ Keine Control-Daten gefunden für: {control_key}")
                        continue
                    
                    control_json, _ = control_data
                    
                    if not control_json:
                        logger.warning(f"⚠️ Control-JSON ist leer für: {control_key}")
                        continue
                    
                    # Parse JSON
                    control = json.loads(control_json)
                    
                    # Stelle sicher, dass ui-Dict existiert
                    if 'ui' not in control:
                        control['ui'] = {}
                    
                    # Bestimme sinnvolle Defaults basierend auf Control-Typ
                    control_type = control.get('type', 'string')
                    
                    # Default-Richtung
                    if 'datum' in control_key.lower() or 'alter' in control_key.lower():
                        default_direction = 'desc'  # Neueste zuerst
                    else:
                        default_direction = 'asc'  # Alphabetisch
                    
                    # sortByOriginal nur für Datumsfelder mit _show Suffix
                    default_by_original = (
                        'geburtsdatum_show' in control_key and 
                        control_key.endswith('_show')
                    )
                    
                    # Aktualisiere Sortier-Einstellungen
                    control['ui']['sortable'] = True
                    control['ui']['sortDirection'] = control['ui'].get('sortDirection', default_direction)
                    control['ui']['sortByOriginal'] = control['ui'].get('sortByOriginal', default_by_original)
                    
                    # Speichere zurück als JSON
                    updated_json = json.dumps(control, ensure_ascii=False)
                    gcs._db.set_value(view_guid, control_key, updated_json)
                    
                    updated_count += 1
                    logger.info(f"✅ {control_key}: sortable=true, direction={control['ui']['sortDirection']}")
                    
                except Exception as e:
                    logger.error(f"❌ Fehler bei {control_key}: {e}")
                    error_count += 1
            
            # Rebuild Projektions-Tabellen nach Änderungen
            logger.info("🔄 Rebuild Projektions-Tabellen...")
            gcs.rebuild_projection_tables(view_guid)
            
            # Controls-Config in View neu laden
            if hasattr(self.view_dialog, 'controls_config'):
                # Controls neu laden
                for control_key in projection_table:
                    control_data = gcs._db.get_value(view_guid, control_key)
                    if control_data and len(control_data) == 2:
                        control_json, _ = control_data
                        if control_json:
                            self.view_dialog.controls_config[control_key] = json.loads(control_json)
            
            # Erfolgs-Meldung
            message = f"✅ Update abgeschlossen!\n\n"
            message += f"• {updated_count} Controls aktualisiert\n"
            if error_count > 0:
                message += f"• {error_count} Fehler aufgetreten\n"
            message += f"\nAlle Spalten sind jetzt sortierbar."
            
            QMessageBox.information(self, "Sortierbar-Update", message)
            
            logger.info(f"🎉 Sortierbar-Update abgeschlossen: {updated_count} erfolgreich, {error_count} Fehler")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei _enable_all_sortable: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Sortierbar-Update:\n{e}")
    
    def _on_header_clicked(self, logical_index: int):
        """
        🎯 EINFACHE SORTIERUNG: Header-Click Handler für PdvmViewDisplay
        
        Args:
            logical_index: Index der geklickten Spalte
        """
        try:
            from sort_manager import get_sort_manager
            from pdvm_matrix_manager import get_matrix_manager
            
            # View-GUID holen
            view_guid = getattr(self.view_dialog, 'view_guid', None)
            if not view_guid:
                logger.error("❌ Keine View-GUID verfügbar für Sortierung")
                return
            
            # Sichtbare Spalten holen
            visible_columns = self._get_visible_columns_from_gcs()
            
            if logical_index >= len(visible_columns):
                logger.warning(f"⚠️ Ungültiger Spalten-Index: {logical_index}")
                return
            
            # Column-Key aus Index ermitteln
            column_key = visible_columns[logical_index]
            
            logger.info(f"🔄 Header-Click auf Spalte {logical_index}: {column_key}")
            
            # Matrix-Manager holen
            matrix_manager = get_matrix_manager(view_guid)
            if not matrix_manager:
                logger.error("❌ Matrix-Manager nicht verfügbar")
                return
            
            # Sort-Manager holen
            sort_manager = get_sort_manager(view_guid)
            sort_manager.set_controls_config(self.view_dialog.controls_config)
            
            # Filter-Matrix holen (Input für Sortierung)
            filter_matrix = matrix_manager.get_filter_data()
            
            if not filter_matrix:
                logger.warning("⚠️ Keine Filter-Matrix verfügbar")
                return
            
            # Einfache Sortierung durchführen (toggle_direction=True)
            sorted_matrix = sort_manager.simple_sort(filter_matrix, column_key, toggle_direction=True)
            
            # Sort-Matrix in Matrix-Manager setzen
            matrix_manager.set_sort_data(sorted_matrix)
            
            # Tabelle aktualisieren
            self.refresh_table()
            
            logger.info(f"✅ Einfache Sortierung angewandt: {column_key}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Click Sortierung: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _export_csv(self):
        """CSV-Export - Weiterleitung an view_dialog._export_data()"""
        try:
            logger.info("📤 CSV-Export aus Display-Menü gestartet...")
            
            # Leite an die Haupt-Export-Methode weiter
            if hasattr(self.view_dialog, '_export_data'):
                self.view_dialog._export_data()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Export-Fehler", "Export-Funktion nicht verfügbar")
                logger.error("❌ _export_data Methode nicht in view_dialog gefunden")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim CSV-Export (Display): {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Export:\n{e}")
    
