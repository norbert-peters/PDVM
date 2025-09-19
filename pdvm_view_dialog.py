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
    
    def __init__(self, call_daten, parent=None):
        """
        Initialisierung des autonomen View-Dialogs
        
        Args:
            call_daten: Enthält view_guid, title, first_call, reset
            parent: Parent-Widget
        """
        self.call_daten = call_daten
        self.parent = parent
        
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
            QMessageBox.critical(parent, "Fehlende Daten", 
                               f"Die Ausgabe kann nicht erfolgen:\n\n{error_text}")
            raise ValueError(error_text)
        
        logger.info(f"🔹 PdvmViewDialog initialisiert - View: {self.view_guid}, First Call: {self.first_call}")
        
        # PERFORMANCE: Verwende temporäre Pdvm_DateTime Instanz aus GCS für Abdatum-Formatierung
        gcs_temp = get_gcs_linear()
        if gcs_temp and hasattr(gcs_temp, 'temp_dt_inst'):
            self._dt_temp = gcs_temp.temp_dt_inst
            logger.info("✅ Temporäre Pdvm_DateTime Instanz aus GCS übernommen")
        else:
            # Fallback: Erstelle eigene Instanz
            country = gcs_temp.country if gcs_temp and hasattr(gcs_temp, 'country') else "DEU"
            self._dt_temp = Pdvm_DateTime(country)
            logger.info(f"⚠️ Fallback: Eigene Pdvm_DateTime Instanz erstellt für Country: {country}")
        
        # Daten-Container
        self.view_config = None
        self.controls_config = None
        self.all_data_records = []
        self.display_matrix = []
        
        # UI-Container
        self.display = None
        
        # Initialisierung starten
        self._initialize_dialog()
    
    def _get_dt_temp(self):
        """PERFORMANCE: Temporäre Pdvm_DateTime Instanz aus GCS für Abdatum-Formatierung"""
        if self._dt_temp is None:
            try:
                gcs_temp = get_gcs_linear()
                if gcs_temp and hasattr(gcs_temp, 'temp_dt_inst'):
                    self._dt_temp = gcs_temp.temp_dt_inst
                    logger.info("✅ Temporäre Pdvm_DateTime Instanz aus GCS übernommen")
                else:
                    # Fallback: Erstelle eigene Instanz
                    country = gcs_temp.country if gcs_temp and hasattr(gcs_temp, 'country') else "DEU"
                    self._dt_temp = Pdvm_DateTime(country)
                    logger.info(f"⚠️ Fallback: Eigene Pdvm_DateTime Instanz erstellt für Country: {country}")
            except Exception as e:
                logger.warning(f"⚠️ Fehler bei Erstellung temporärer Pdvm_DateTime: {e}")
                self._dt_temp = None
        return self._dt_temp
    
    def _initialize_dialog(self):
        """LINEARE Initialisierung"""
        logger.info("🔹 Starte LINEARE Dialog-Initialisierung...")
        
        # 1. ViewDaten laden
        self._load_viewdata()
        
        # 2. Controls linear generieren und speichern
        self._generate_and_save_controls()
        
        # 3. Daten laden
        self._load_data()
        
        # 4. Matrix erstellen
        self._build_matrix()
        
        # 5. UI erstellen
        self._create_ui()
        
        logger.info("✅ LINEARE Dialog-Initialisierung abgeschlossen")
    
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
                                    dt = self._get_dt_temp()
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
                                # Verwende temporäre PdvmDateTime-Instanz aus GCS
                                dt = self._get_dt_temp()
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
                                gcs_temp = get_gcs_linear()
                                if gcs_temp:
                                    try:
                                        # Verwende die GUID und Gruppe für die Übersetzung
                                        translated_value = gcs_temp.translate_dropdown_value(dropdown_guid, str(original_wert), dropdown_gruppe)
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
            # PERFORMANCE: Verwende temporäre Instanz statt jedes Mal neu zu erstellen
            dt = self._get_dt_temp()
            if dt is None:
                # Fallback wenn temporäre Instanz nicht verfügbar
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
    
    def get_display_widget(self):
        """Widget für Integration zurückgeben"""
        return self.display
    
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
            gcs = get_gcs_linear()
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
        """Tabelle aktualisieren"""
        matrix = self.view_dialog.display_matrix
        
        if not matrix:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.status_label.setText("Keine Daten")
            return
        
        # Sichtbare Spalten ermitteln
        visible_columns = self._get_visible_columns()

        # Tabelle füllen
        self.table.setRowCount(len(matrix))
        self.table.setColumnCount(len(visible_columns))

        # Header
        headers = []
        tooltips = []
        gcs = get_gcs_linear()  # LINEAR: GCS einmal holen
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
        
        # Daten
        for row_idx, row_data in enumerate(matrix):
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
        
        # Status mit Modus-Anzeige - LINEAR
        mode_text = "Experten Modus" if (gcs and gcs.expert_mode) else "Standard Modus"
        status_text = f"{len(matrix)} Datensätze, {len(visible_columns)} Spalten"

        # Layout für Status-Zeile mit rechts ausgerichtetem Modus
        self.status_label.setText(f"{status_text} - {mode_text}")
        self.status_label.setStyleSheet("QLabel { color: #666666; }")
    
    def _get_visible_columns(self):
        """Sichtbare Spalten ermitteln - NUR auf show-Eigenschaft basierend - LINEAR"""
        gcs = get_gcs_linear()

        visible = []
        for control_key, control in self.view_dialog.controls_config.items():
            if gcs and gcs.expert_mode:
                # Expert: Alle Controls anzeigen (außer dummy)
                if control_key != 'dummy':
                    visible.append(control_key)
            else:
                # Normal: Nur Controls mit show=True UND expert_mode=false
                if (control.get('show', False) and 
                    not control.get('expert_mode', False)):
                    visible.append(control_key)

        # Sortierung je nach Modus
        if gcs and gcs.expert_mode:
            # ExpertMode: Nach expert_order sortieren
            def get_expert_order(control_key):
                control = self.view_dialog.controls_config.get(control_key, {})
                return control.get('expert_order', 999)  # Default: hohe Zahl für unsortierte

            visible.sort(key=get_expert_order)
        else:
            # NormalMode: Nach display_order sortieren
            def get_display_order(control_key):
                control = self.view_dialog.controls_config.get(control_key, {})
                return control.get('display_order', 999)  # Default: hohe Zahl für unsortierte

            visible.sort(key=get_display_order)

        return visible
    
    def _create_settings_menu(self):
        """Erstelle Settings-Dropdown-Menü - LINEAR"""
        try:
            settings_menu = QMenu(self)

            # 1. Verwaltung der Spalten
            action_spalten = QAction("Verwaltung der Spalten", self)
            action_spalten.triggered.connect(self._spalten_verwaltung)
            settings_menu.addAction(action_spalten)

            # 2. ExpertMode (nur für Admins) - LINEAR
            gcs = get_gcs_linear()
            if gcs and gcs.is_admin:
                settings_menu.addSeparator()

                # ExpertMode Toggle
                expert_text = "ExpertMode (ausschalten)" if gcs.expert_mode else "ExpertMode (einschalten)"
                action_expert = QAction(expert_text, self)
                action_expert.triggered.connect(self._toggle_expert_mode)
                settings_menu.addAction(action_expert)

            # 3. Filter anzeigen/ausblenden
            settings_menu.addSeparator()
            action_filter = QAction("Filter (anzeigen / ausblenden)", self)
            action_filter.triggered.connect(self._toggle_filter_panel)
            settings_menu.addAction(action_filter)

            # 4. Zurücksetzen
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
        """Spalten-Verwaltung öffnen"""
        try:
            from pdvm_spalten_verwaltung_dialog import show_spalten_verwaltung
            
            # Dialog anzeigen
            result = show_spalten_verwaltung(self.view_dialog, self)
            
            # Bei OK: Tabelle neu erstellen
            if result:
                self.refresh_table()
                logger.info("✅ Spaltenverwaltung abgeschlossen, Tabelle aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Verwaltung: {e}")
            QMessageBox.warning(self, "Fehler", f"Spalten-Verwaltung Fehler:\n{e}")
    
    def _toggle_expert_mode(self):
        """ExpertMode ein/aus schalten - LINEAR"""
        try:
            gcs = get_gcs_linear()
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
            
            # Titel aktualisieren (falls ExpertMode aktiv)
            self.header_label.setText(self._get_title_text())
            
            # Tabelle komplett neu aufbauen
            self.refresh_table()
            
            logger.info("✅ View erfolgreich zurückgesetzt - Standard-Controls persistent gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim View-Reset: {e}")
            QMessageBox.critical(self, "Fehler", f"View konnte nicht zurückgesetzt werden:\n{e}")


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
    
    def _create_column_search_fields(self, parent_layout):
        """Erstellt Suchfelder für jede searchable UND sichtbare Spalte"""
        column_search_group = QGroupBox("Spalten-spezifische Suche")
        column_search_layout = QVBoxLayout(column_search_group)

        self.column_search_fields = {}

        # Sichtbare Spalten ermitteln (wie in der Tabelle angezeigt)
        visible_columns = []
        if hasattr(self.view_dialog, '_get_visible_columns'):
            visible_columns = self.view_dialog._get_visible_columns()
        else:
            # Fallback: Alle Spalten aus controls_config
            visible_columns = list(self.view_dialog.controls_config.keys())

        # Nur searchable Spalten aus den sichtbaren Spalten filtern
        searchable_columns = []
        for field_name in visible_columns:
            field_config = self.view_dialog.controls_config.get(field_name, {})
            if field_config.get('searchable', False) and field_name.endswith('_show'):
                original_field = field_name.replace('_show', '_original')
                if original_field in self.view_dialog.controls_config:
                    display_name = field_config.get('name', field_name)
                    searchable_columns.append((field_name, display_name))

        if not searchable_columns:
            no_search_label = QLabel("Keine searchable Spalten verfügbar")
            no_search_label.setStyleSheet("color: #666; font-style: italic;")
            column_search_layout.addWidget(no_search_label)
        else:
            for field_name, display_name in searchable_columns:
                # Container für jedes Suchfeld
                field_layout = QHBoxLayout()

                # Label
                label = QLabel(f"{display_name}:")
                label.setMinimumWidth(100)
                field_layout.addWidget(label)

                # Suchfeld
                search_edit = QLineEdit()
                search_edit.setPlaceholderText(f"Suche in {display_name}...")
                search_edit.textChanged.connect(lambda text, fn=field_name: self._on_column_search_changed(fn, text))
                field_layout.addWidget(search_edit)

                # Negative Checkbox
                negative_checkbox = QCheckBox("Neg.")
                negative_checkbox.setToolTip("Negative Suche für diese Spalte")
                field_layout.addWidget(negative_checkbox)

                column_search_layout.addLayout(field_layout)
                self.column_search_fields[field_name] = {
                    'edit': search_edit,
                    'negative': negative_checkbox
                }

        parent_layout.addWidget(column_search_group)

    def _load_filter_settings(self):
        """Lädt persistente Filter-Einstellungen"""
        try:
            gcs = get_gcs_linear()
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
            gcs = get_gcs_linear()
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
        """Handler für globale Suchfeld-Änderungen"""
        # Automatische Filter-Anwendung (optional)
        pass

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

        original_matrix = self.view_dialog.display_matrix
        if not original_matrix:
            return

        filtered_matrix = []

        for row in original_matrix:
            include_row = True

            # Globale Suche
            if filter_config['global_search']:
                global_match = self._check_global_search(row, filter_config)
                if filter_config['global_negative']:
                    include_row = not global_match
                else:
                    include_row = global_match

            # Spalten-spezifische Suche (additiv)
            if include_row and filter_config['column_filters']:
                for field_name, column_filter in filter_config['column_filters'].items():
                    if not self._check_column_search(row, field_name, column_filter, filter_config):
                        include_row = False
                        break

            if include_row:
                filtered_matrix.append(row)

        # Gefilterte Matrix anwenden
        self.view_dialog.display_matrix = filtered_matrix

        # Tabelle aktualisieren
        if hasattr(self.view_dialog, 'refresh_table'):
            self.view_dialog.refresh_table()

        logger.info(f"🔍 Filter angewendet: {len(filtered_matrix)} von {len(original_matrix)} Zeilen")

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

    def _reset_search_filters(self):
        """Setzt alle Suchfilter zurück"""
        # Original-Matrix wiederherstellen
        if hasattr(self.view_dialog, 'original_matrix'):
            self.view_dialog.display_matrix = self.view_dialog.original_matrix.copy()
        else:
            # Fallback: Matrix neu erstellen
            self.view_dialog._create_display_matrix()

        # Tabelle aktualisieren
        if hasattr(self.view_dialog, 'refresh_table'):
            self.view_dialog.refresh_table()

        logger.info("🔄 Suchfilter zurückgesetzt")