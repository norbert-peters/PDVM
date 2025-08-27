# pdvm_filter_manager_v3.py
"""
Filter-Manager V3 mit korrekter Original/Show-Spalten-Logik
Implementiert zentrale Filter-Routinen mit regulären Ausdrücken
"""

import logging
import re
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, 
    QScrollArea, QLabel, QFrame, QDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Import der verbesserten Filter-Funktionen
from pdvm_filter_improvements_v3 import is_empty_value, apply_improved_empty_filter

logger = logging.getLogger(__name__)

class PdvmFilterManagerV3:
    """
    Filter-Manager V3 mit korrekter Original/Show-Spalten-Architektur
    
    Architektur:
    1. Jeder Filter-Typ hat eine zentrale Routine
    2. Filter arbeiten standardmäßig auf Show-Spalten
    3. Ausnahme: Datum-Zeitraum-Modus arbeitet auf Original-Spalten
    4. Alle Filter verwenden reguläre Ausdrücke
    5. Filter-Einstellungen werden in systemsteuerung gespeichert
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.filter_states = {}  # field_name -> FilterState
        self.original_data = []  # Original-Daten (nur bei refresh neu geladen)
        self.filtered_data = []  # Gefilterte Daten für UI
        
        # Initialisierung
        self._initialize_filter_states()
        self._load_filter_settings()
    
    def _initialize_filter_states(self):
        """Initialisiert Filter-States für alle Felder"""
        for field_config in self.data_manager.get_fields_config():
            field_name = field_config.get("feld")
            if not field_name:
                continue
                
            filter_type = field_config.get("ui", {}).get("filterType", "contains")
            field_type = field_config.get("type", "string")
            
            if filter_type == "dropdown":
                # Dropdown-Filter State
                self.filter_states[field_name] = {
                    "type": "dropdown",
                    "selected_keys": set(),
                    "show_empty": True,
                    "all_keys": set(),
                    "active": False,
                    "regex_pattern": ""
                }
            elif filter_type == "dateRange":
                # DateRange-Filter State
                self.filter_states[field_name] = {
                    "type": "dateRange", 
                    "ab_jahr": None,
                    "ab_monat": None,
                    "ab_tag": None,
                    "bis_jahr": None,
                    "bis_monat": None,
                    "bis_tag": None,
                    "show_empty": True,
                    "zeitraum_mode": False,  # Standard vs. Zeitraum-Modus
                    "active": False,
                    "regex_pattern": ""
                }
            else:
                # Text-Filter State (contains, exact, etc.)
                self.filter_states[field_name] = {
                    "type": "text",
                    "filter_type": filter_type,
                    "search_text": "",
                    "active": False,
                    "regex_pattern": ""
                }
    
    def _load_filter_settings(self):
        """Lädt gespeicherte Filter-Einstellungen aus systemsteuerung"""
        try:
            saved_filters = self.data_manager.get_user_setting("filter_states", {})
            
            for field_name, saved_state in saved_filters.items():
                if field_name in self.filter_states:
                    # Gespeicherte Einstellungen übernehmen
                    self.filter_states[field_name].update(saved_state)
                    
            logger.info(f"📋 Filter-Einstellungen geladen: {len(saved_filters)} Filter")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der Filter-Einstellungen: {e}")
    
    def save_filter_settings(self):
        """Speichert aktuelle Filter-Einstellungen in systemsteuerung"""
        try:
            self.data_manager.save_user_settings({
                "filter_states": self.filter_states
            })
            
            logger.info("💾 Filter-Einstellungen gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Filter-Einstellungen: {e}")
    
    def load_original_data(self):
        """Lädt Original-Daten vom Data-Manager"""
        self.original_data = self.data_manager.get_original_data()
        self.filtered_data = self.original_data.copy()
        logger.info(f"📊 Original-Daten geladen: {len(self.original_data)} Datensätze")
    
    def apply_all_filters(self):
        """Wendet alle aktiven Filter an"""
        try:
            # Mit Original-Daten starten
            self.filtered_data = self.original_data.copy()
            
            # Alle aktiven Filter anwenden
            for field_name, filter_state in self.filter_states.items():
                if filter_state.get("active", False):
                    self._apply_single_filter(field_name, filter_state)
            
            logger.info(f"🔍 Filter angewendet: {len(self.original_data)} → {len(self.filtered_data)} Datensätze")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Filter: {e}")
            # Fallback: Ungefilterte Daten
            self.filtered_data = self.original_data.copy()
    
    def _apply_single_filter(self, field_name: str, filter_state: Dict):
        """
        Wendet einen einzelnen Filter an
        
        Args:
            field_name: Name des Feldes
            filter_state: Filter-Zustand
        """
        filter_type = filter_state.get("type")
        
        if filter_type == "text":
            self._apply_text_filter(field_name, filter_state)
        elif filter_type == "dropdown":
            self._apply_dropdown_filter(field_name, filter_state)
        elif filter_type == "dateRange":
            self._apply_date_range_filter(field_name, filter_state)
    
    def _apply_text_filter(self, field_name: str, filter_state: Dict):
        """
        Zentrale Text-Filter-Routine mit regulären Ausdrücken
        """
        try:
            search_text = filter_state.get("search_text", "").strip()
            if not search_text:
                return
            
            filter_type = filter_state.get("filter_type", "contains")
            
            # Spalte bestimmen (immer Show-Spalte für Text-Filter)
            column_name = f"{field_name}_show"
            
            # Regex-Pattern erstellen
            if filter_type == "contains":
                pattern = re.escape(search_text)
            elif filter_type == "exact":
                pattern = f"^{re.escape(search_text)}$"
            elif filter_type == "startsWith":
                pattern = f"^{re.escape(search_text)}"
            elif filter_type == "endsWith":
                pattern = f"{re.escape(search_text)}$"
            else:
                # Custom regex
                pattern = search_text
            
            # Pattern kompilieren (case-insensitive)
            regex = re.compile(pattern, re.IGNORECASE)
            
            # Filter anwenden
            self.filtered_data = [
                record for record in self.filtered_data
                if self._matches_regex(record.get(column_name, ""), regex)
            ]
            
            logger.debug(f"🔍 Text-Filter {field_name}: '{search_text}' → {len(self.filtered_data)} Treffer")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Text-Filter {field_name}: {e}")
    
    def _apply_dropdown_filter(self, field_name: str, filter_state: Dict):
        """
        Zentrale Dropdown-Filter-Routine mit verbesserter leere-Werte-Behandlung
        """
        try:
            selected_keys = filter_state.get("selected_keys", set())
            show_empty = filter_state.get("show_empty", True)
            
            if not selected_keys and show_empty:
                return  # Keine Filterung
            
            # VERBESSERTE FILTERUNG mit robusten leere-Werte-Prüfungen
            new_filtered_data = []
            for record in self.filtered_data:
                original_value = record.get(f"{field_name}_original")
                show_value = record.get(f"{field_name}_show", "")
                
                # Robuste leere-Werte-Erkennung
                is_original_empty = is_empty_value(original_value)
                is_show_empty = is_empty_value(show_value)
                is_completely_empty = is_original_empty and is_show_empty
                
                if is_completely_empty:
                    if show_empty:
                        new_filtered_data.append(record)
                    # Wenn show_empty=False, wird der Datensatz ausgeschlossen
                    continue
                
                # Nicht-leere Werte: Prüfe ob in ausgewählten Keys
                if selected_keys:
                    original_str = str(original_value) if original_value is not None else ""
                    if original_str in selected_keys:
                        new_filtered_data.append(record)
                else:
                    # Keine Keys ausgewählt aber show_empty=True → alle nicht-leeren anzeigen
                    new_filtered_data.append(record)
            
            self.filtered_data = new_filtered_data
            
            logger.debug(f"🔍 Dropdown-Filter {field_name}: {len(selected_keys)} ausgewählt → {len(self.filtered_data)} Treffer (show_empty={show_empty})")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Dropdown-Filter {field_name}: {e}")
    
    def _apply_date_range_filter(self, field_name: str, filter_state: Dict):
        """
        Zentrale DateRange-Filter-Routine mit zwei Modi
        """
        try:
            zeitraum_mode = filter_state.get("zeitraum_mode", False)
            show_empty = filter_state.get("show_empty", True)
            
            ab_jahr = filter_state.get("ab_jahr")
            ab_monat = filter_state.get("ab_monat")
            ab_tag = filter_state.get("ab_tag")
            bis_jahr = filter_state.get("bis_jahr")
            bis_monat = filter_state.get("bis_monat")
            bis_tag = filter_state.get("bis_tag")
            
            if not any([ab_jahr, ab_monat, ab_tag, bis_jahr, bis_monat, bis_tag]):
                return  # Keine Datumsfilterung
            
            if zeitraum_mode:
                # Zeitraum-Modus: Original-Spalte mit PDVM-DateTime-Bereich
                self._apply_date_range_zeitraum_mode(field_name, filter_state)
            else:
                # Standard-Modus: Jahr/Monat/Tag-Filter auf internen Spalten
                self._apply_date_range_standard_mode(field_name, filter_state)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei DateRange-Filter {field_name}: {e}")
    
    def _apply_date_range_zeitraum_mode(self, field_name: str, filter_state: Dict):
        """
        Zeitraum-Modus: Filter auf Original-Spalte mit PDVM-DateTime-Bereich
        """
        try:
            ab_jahr = filter_state.get("ab_jahr")
            ab_monat = filter_state.get("ab_monat")
            ab_tag = filter_state.get("ab_tag")
            bis_jahr = filter_state.get("bis_jahr")
            bis_monat = filter_state.get("bis_monat")
            bis_tag = filter_state.get("bis_tag")
            show_empty = filter_state.get("show_empty", True)
            
            # PDVM-DateTime-Bereich berechnen
            if ab_jahr and ab_monat and ab_tag:
                from pdvm_datetime import Pdvm_DateTime
                ab_dt = Pdvm_DateTime("DEU")
                ab_dt.PdvmDateTimeT = (ab_jahr, ab_monat, ab_tag, 0, 0, 0, 0)
                ab_value = ab_dt.PdvmDateTime
            else:
                ab_value = None
            
            if bis_jahr and bis_monat and bis_tag:
                from pdvm_datetime import Pdvm_DateTime
                bis_dt = Pdvm_DateTime("DEU")
                bis_dt.PdvmDateTimeT = (bis_jahr, bis_monat, bis_tag, 23, 59, 59, 999999)
                bis_value = bis_dt.PdvmDateTime
            else:
                bis_value = None
            
            # Filter auf Original-Spalte anwenden
            column_name = f"{field_name}_original"
            
            new_filtered_data = []
            for record in self.filtered_data:
                value = record.get(column_name)
                is_empty = not value or str(value).strip() == ""
                
                # Leere Werte
                if is_empty and show_empty:
                    new_filtered_data.append(record)
                    continue
                
                # Zeitraum-Prüfung
                try:
                    value_float = float(value)
                    
                    if ab_value is not None and value_float < ab_value:
                        continue
                    if bis_value is not None and value_float > bis_value:
                        continue
                    
                    new_filtered_data.append(record)
                    
                except (ValueError, TypeError):
                    continue
            
            self.filtered_data = new_filtered_data
            
            logger.debug(f"🔍 DateRange-Zeitraum {field_name}: {ab_value} - {bis_value} → {len(self.filtered_data)} Treffer")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei DateRange-Zeitraum-Filter {field_name}: {e}")
    
    def _apply_date_range_standard_mode(self, field_name: str, filter_state: Dict):
        """
        Standard-Modus: Jahr/Monat/Tag-Filter auf interne Spalten
        """
        try:
            ab_jahr = filter_state.get("ab_jahr")
            ab_monat = filter_state.get("ab_monat")
            ab_tag = filter_state.get("ab_tag")
            bis_jahr = filter_state.get("bis_jahr")
            bis_monat = filter_state.get("bis_monat")
            bis_tag = filter_state.get("bis_tag")
            show_empty = filter_state.get("show_empty", True)
            
            new_filtered_data = []
            for record in self.filtered_data:
                # Leere Datumswerte prüfen
                original_value = record.get(f"{field_name}_original")
                is_empty = not original_value or str(original_value).strip() == ""
                
                if is_empty and show_empty:
                    new_filtered_data.append(record)
                    continue
                elif is_empty:
                    continue
                
                # Jahr/Monat/Tag-Werte aus internen Spalten
                record_jahr = record.get(f"_{field_name}_year")
                record_monat = record.get(f"_{field_name}_month")
                record_tag = record.get(f"_{field_name}_day")
                
                # Jahr-Filter
                if ab_jahr is not None and (record_jahr is None or record_jahr < ab_jahr):
                    continue
                if bis_jahr is not None and (record_jahr is None or record_jahr > bis_jahr):
                    continue
                
                # Monat-Filter (nur wenn Jahr-Filter erfüllt)
                if ab_monat is not None and (record_monat is None or record_monat < ab_monat):
                    continue
                if bis_monat is not None and (record_monat is None or record_monat > bis_monat):
                    continue
                
                # Tag-Filter (nur wenn Jahr- und Monat-Filter erfüllt)
                if ab_tag is not None and (record_tag is None or record_tag < ab_tag):
                    continue
                if bis_tag is not None and (record_tag is None or record_tag > bis_tag):
                    continue
                
                new_filtered_data.append(record)
            
            self.filtered_data = new_filtered_data
            
            logger.debug(f"🔍 DateRange-Standard {field_name}: Jahr {ab_jahr}-{bis_jahr}, Monat {ab_monat}-{bis_monat}, Tag {ab_tag}-{bis_tag} → {len(self.filtered_data)} Treffer")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei DateRange-Standard-Filter {field_name}: {e}")
    
    def _matches_regex(self, value: str, regex) -> bool:
        """
        Prüft ob ein Wert einem Regex-Pattern entspricht
        """
        try:
            return bool(regex.search(str(value)))
        except Exception:
            return False
    
    # Filter-Management-Methoden
    
    def set_text_filter(self, field_name: str, search_text: str, filter_type: str = "contains"):
        """Setzt einen Text-Filter"""
        if field_name not in self.filter_states:
            return
        
        filter_state = self.filter_states[field_name]
        filter_state["search_text"] = search_text
        filter_state["filter_type"] = filter_type
        filter_state["active"] = bool(search_text.strip())
    
    def set_dropdown_filter(self, field_name: str, selected_keys: set, show_empty: bool = True):
        """Setzt einen Dropdown-Filter"""
        if field_name not in self.filter_states:
            return
        
        filter_state = self.filter_states[field_name]
        filter_state["selected_keys"] = selected_keys
        filter_state["show_empty"] = show_empty
        filter_state["active"] = bool(selected_keys) or not show_empty
    
    def set_date_range_filter(self, field_name: str, range_data: Dict):
        """Setzt einen DateRange-Filter"""
        if field_name not in self.filter_states:
            return
        
        filter_state = self.filter_states[field_name]
        filter_state.update(range_data)
        
        # Prüfen ob Filter aktiv ist
        has_range = any([
            range_data.get("ab_jahr"),
            range_data.get("ab_monat"), 
            range_data.get("ab_tag"),
            range_data.get("bis_jahr"),
            range_data.get("bis_monat"),
            range_data.get("bis_tag")
        ])
        filter_state["active"] = has_range
    
    def clear_filter(self, field_name: str):
        """Löscht einen Filter"""
        if field_name not in self.filter_states:
            return
        
        filter_state = self.filter_states[field_name]
        filter_type = filter_state.get("type")
        
        if filter_type == "text":
            filter_state["search_text"] = ""
        elif filter_type == "dropdown":
            filter_state["selected_keys"] = set()
            filter_state["show_empty"] = True
        elif filter_type == "dateRange":
            for key in ["ab_jahr", "ab_monat", "ab_tag", "bis_jahr", "bis_monat", "bis_tag"]:
                filter_state[key] = None
            filter_state["show_empty"] = True
            filter_state["zeitraum_mode"] = False
        
        filter_state["active"] = False
    
    def clear_all_filters(self):
        """Löscht alle Filter"""
        for field_name in self.filter_states:
            self.clear_filter(field_name)
    
    def get_filtered_data(self) -> List[Dict[str, Any]]:
        """Gibt die gefilterten Daten zurück"""
        return self.filtered_data
    
    def get_filter_state(self, field_name: str) -> Dict:
        """Gibt den Filter-Zustand für ein Feld zurück"""
        return self.filter_states.get(field_name, {})
    
    def is_filter_active(self, field_name: str) -> bool:
        """Prüft ob ein Filter aktiv ist"""
        return self.filter_states.get(field_name, {}).get("active", False)
    
    def get_active_filter_count(self) -> int:
        """Gibt die Anzahl aktiver Filter zurück"""
        return sum(1 for state in self.filter_states.values() if state.get("active", False))
