# pdvm_filter_manager.py
"""
Separater Filter-Manager für moderne View-Widgets
Verwaltet alle Filter-Logik getrennt von UI und Datenmanagement
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, 
    QScrollArea, QLabel, QFrame, QDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmFilterManager:
    """
    Filter-Manager für moderne View-Widgets
    Verwaltet alle Filter-States und -Logik getrennt von UI
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.filter_states = {}  # field_name -> FilterState
        self.original_data = []  # Original-Daten aus DB (nur bei refresh neu geladen)
        self.filtered_data = []  # Aktuell gefilterte Daten für View
        
        # Initialisierung
        self._initialize_filter_states()
    
    def _initialize_filter_states(self):
        """Initialisiert Filter-States für alle Felder"""
        for field_name in self.data_manager.get_field_names():
            field_config = self.data_manager.get_field_config(field_name)
            if not field_config:
                continue
                
            filter_type = field_config.get("ui", {}).get("filterType", "contains")
            
            if filter_type == "dropdown":
                # Dropdown-Filter State
                self.filter_states[field_name] = {
                    "type": "dropdown",
                    "selected_keys": set(),  # Ausgewählte Keys
                    "show_empty": True,      # Leere Werte anzeigen
                    "all_keys": set(),       # Alle verfügbaren Keys
                    "active": False          # Filter aktiv/inaktiv
                }
            elif filter_type == "dateRange":
                # DateRange-Filter State
                self.filter_states[field_name] = {
                    "type": "dateRange",
                    "ab_jahr": None, "ab_monat": None, "ab_tag": None,
                    "bis_jahr": None, "bis_monat": None, "bis_tag": None,
                    "show_empty": True,      # Leere Werte anzeigen
                    "active": False          # Filter aktiv/inaktiv
                }
            else:
                # Text-Filter State
                self.filter_states[field_name] = {
                    "type": "text",
                    "search_text": "",       # Suchtext
                    "exclude_empty": False,  # Leere Werte ausschließen
                    "active": False          # Filter aktiv/inaktiv
                }
    
    def load_original_data(self):
        """Lädt Original-Daten neu aus Datenbank (nur bei refresh)"""
        self.original_data = self.data_manager.get_data()
        
        # Dropdown-Optionen für alle Dropdown-Filter aktualisieren
        for field_name, filter_state in self.filter_states.items():
            if filter_state["type"] == "dropdown":
                self._update_dropdown_options(field_name)
        
        # Initiale Filterung anwenden
        self.apply_all_filters()
        
        logger.info(f"📊 Original-Daten geladen: {len(self.original_data)} Datensätze")
    
    def _update_dropdown_options(self, field_name):
        """Aktualisiert verfügbare Dropdown-Optionen aus Original-Daten"""
        if field_name not in self.filter_states:
            return
            
        filter_state = self.filter_states[field_name]
        if filter_state["type"] != "dropdown":
            return
        
        # KRITISCH: Raw-Werte aus _raw_{field_name} sammeln für Filter-Logik
        raw_field_name = f"_raw_{field_name}"
        unique_raw_values = set()
        unique_display_values = {}  # raw_value -> display_value mapping
        
        for record in self.original_data:
            # Raw-Wert für Filter-Logik
            raw_value = record.get(raw_field_name, record.get(field_name, ""))
            # Display-Wert für UI-Anzeige
            display_value = record.get(field_name, str(raw_value))
            
            if raw_value and str(raw_value).strip():
                raw_key = str(raw_value).strip()
                unique_raw_values.add(raw_key)
                unique_display_values[raw_key] = str(display_value).strip()
        
        filter_state["all_keys"] = unique_raw_values
        filter_state["key_display_mapping"] = unique_display_values  # Für UI-Anzeige
        
        # Initial alle Keys aktivieren (falls noch nicht gesetzt)
        if not filter_state["selected_keys"]:
            filter_state["selected_keys"] = unique_raw_values.copy()
            
        logger.debug(f"🔧 Dropdown-Optionen aktualisiert für {field_name}: {len(unique_raw_values)} Optionen")
        logger.debug(f"📋 Mapping: {unique_display_values}")
    
    def set_text_filter(self, field_name, search_text):
        """Setzt Text-Filter für ein Feld"""
        if field_name not in self.filter_states:
            return
            
        filter_state = self.filter_states[field_name]
        filter_state["search_text"] = search_text.strip()
        filter_state["active"] = bool(search_text.strip())
        
        logger.debug(f"🔍 Text-Filter gesetzt für {field_name}: '{search_text}'")
    
    def set_dropdown_filter(self, field_name, selected_keys, show_empty=True):
        """Setzt Dropdown-Filter für ein Feld"""
        if field_name not in self.filter_states:
            return
            
        filter_state = self.filter_states[field_name]
        if filter_state["type"] != "dropdown":
            return
        
        filter_state["selected_keys"] = set(selected_keys)
        filter_state["show_empty"] = show_empty
        
        # Filter ist aktiv wenn nicht alle Keys ausgewählt sind oder empty deaktiviert
        all_selected = len(filter_state["selected_keys"]) == len(filter_state["all_keys"])
        filter_state["active"] = not (all_selected and show_empty)
        
        logger.debug(f"🔍 Dropdown-Filter gesetzt für {field_name}: {len(selected_keys)} von {len(filter_state['all_keys'])} Keys")
    
    def set_empty_filter(self, field_name, exclude_empty=False):
        """Setzt Empty-Filter für ein Feld (für Text-Felder)"""
        if field_name not in self.filter_states:
            return
            
        filter_state = self.filter_states[field_name]
        filter_state["exclude_empty"] = exclude_empty
        
        # Kombiniere mit Text-Filter: Aktiv wenn Text-Suche ODER Empty-Filter
        has_text_search = bool(filter_state.get("search_text", "").strip())
        filter_state["active"] = has_text_search or exclude_empty
        
        logger.debug(f"🔘 Empty-Filter gesetzt für {field_name}: {'Leere ausschließen' if exclude_empty else 'Alle anzeigen'}")
    
    def set_date_range_filter(self, field_name, range_data):
        """Setzt DateRange-Filter für ein Feld mit Unterstützung für Zeitraum-Modus"""
        if field_name not in self.filter_states:
            return
            
        filter_state = self.filter_states[field_name]
        if filter_state["type"] != "dateRange":
            return
        
        # Prüfe ob Zeitraum-Modus aktiviert wurde
        zeitraum_mode = range_data.get("zeitraum_mode", False)
        
        if zeitraum_mode:
            # Zeitraum-Modus: Verwende PDVM Date-Bereich auf Originalspalte
            logger.info(f"🕒 Zeitraum-Modus aktiviert für {field_name}")
            self.apply_date_range_on_original_column(field_name, range_data)
            return
        
        # Standard-Modus: Range-Daten übernehmen für Jahr/Monat/Tag Filter
        filter_state["ab_jahr"] = range_data.get("ab_jahr")
        filter_state["ab_monat"] = range_data.get("ab_monat")
        filter_state["ab_tag"] = range_data.get("ab_tag")
        filter_state["bis_jahr"] = range_data.get("bis_jahr")
        filter_state["bis_monat"] = range_data.get("bis_monat")
        filter_state["bis_tag"] = range_data.get("bis_tag")
        filter_state["show_empty"] = range_data.get("show_empty", True)
        
        # Filter ist aktiv wenn mindestens ein Datums-Teil gesetzt ist
        has_date_filter = any([
            filter_state["ab_jahr"], filter_state["ab_monat"], filter_state["ab_tag"],
            filter_state["bis_jahr"], filter_state["bis_monat"], filter_state["bis_tag"]
        ])
        filter_state["active"] = has_date_filter
        
        # Standard-Modus: Normale Filterung anwenden
        if has_date_filter:
            self.apply_all_filters()
        
        logger.debug(f"🗓️ DateRange-Filter gesetzt für {field_name}: Ab({range_data.get('ab_jahr')}-{range_data.get('ab_monat')}-{range_data.get('ab_tag')}) Bis({range_data.get('bis_jahr')}-{range_data.get('bis_monat')}-{range_data.get('bis_tag')})")
    
    def reset_all_filters(self):
        """Setzt alle Filter auf Default zurück"""
        for field_name, filter_state in self.filter_states.items():
            if filter_state["type"] == "dropdown":
                filter_state["selected_keys"] = filter_state["all_keys"].copy()
                filter_state["show_empty"] = True
                filter_state["active"] = False
            elif filter_state["type"] == "dateRange":
                filter_state["ab_jahr"] = None
                filter_state["ab_monat"] = None
                filter_state["ab_tag"] = None
                filter_state["bis_jahr"] = None
                filter_state["bis_monat"] = None
                filter_state["bis_tag"] = None
                filter_state["show_empty"] = True
                filter_state["active"] = False
            else:
                filter_state["search_text"] = ""
                filter_state["exclude_empty"] = False  # ERWEITERT: Empty-Filter zurücksetzen
                filter_state["active"] = False
        
        logger.info("🔄 Alle Filter zurückgesetzt (inklusive Empty-Filter)")
    
    def reset_filter(self, field_name):
        """Setzt einen einzelnen Filter zurück"""
        if field_name not in self.filter_states:
            return
            
        filter_state = self.filter_states[field_name]
        if filter_state["type"] == "dropdown":
            filter_state["selected_keys"] = filter_state["all_keys"].copy()
            filter_state["show_empty"] = True
            filter_state["active"] = False
        else:
            filter_state["search_text"] = ""
            filter_state["active"] = False
        
        logger.debug(f"🔄 Filter zurückgesetzt für {field_name}")
    
    def apply_all_filters(self):
        """Wendet alle aktiven Filter auf Original-Daten an"""
        if not self.original_data:
            self.filtered_data = []
            return
        
        self.filtered_data = []
        
        for record in self.original_data:
            if self._record_matches_all_filters(record):
                self.filtered_data.append(record)
        
        logger.debug(f"🔍 Filterung: {len(self.filtered_data)} von {len(self.original_data)} Datensätzen")
    
    def _record_matches_all_filters(self, record):
        """Prüft ob ein Datensatz alle aktiven Filter erfüllt"""
        for field_name, filter_state in self.filter_states.items():
            if not filter_state["active"]:
                continue  # Inaktive Filter überspringen
                
            if not self._record_matches_filter(record, field_name, filter_state):
                return False
                
        return True
    
    def _record_matches_filter(self, record, field_name, filter_state):
        """Prüft ob ein Datensatz einen einzelnen Filter erfüllt"""
        # KRITISCH: Für Dropdown-Felder Raw-Wert verwenden
        if filter_state["type"] == "dropdown":
            raw_field_name = f"_raw_{field_name}"
            record_value = record.get(raw_field_name, record.get(field_name, ""))
        else:
            record_value = record.get(field_name, "")
        
        if filter_state["type"] == "dropdown":
            return self._check_dropdown_match(record_value, filter_state)
        elif filter_state["type"] == "dateRange":
            return self._check_date_range_match(record, field_name, filter_state)
        else:
            return self._check_text_match(record_value, filter_state)
    
    def _check_dropdown_match(self, record_value, filter_state):
        """Prüft Dropdown-Filter Match"""
        # Leere Werte
        if not record_value or str(record_value).strip() == "":
            return filter_state["show_empty"]
        
        # KRITISCH: Raw-Wert für Vergleich verwenden
        record_key = str(record_value).strip()
        is_match = record_key in filter_state["selected_keys"]
        
        logger.debug(f"🔍 Dropdown-Match: '{record_key}' in {filter_state['selected_keys']} = {is_match}")
        return is_match
    
    def _check_text_match(self, record_value, filter_state):
        """Prüft Text-Filter Match - ERWEITERT für Empty-Filter"""
        # Prüfe zunächst Empty-Filter
        is_empty = not record_value or str(record_value).strip() == ""
        exclude_empty = filter_state.get("exclude_empty", False)
        
        # Wenn Empty-Filter aktiv und Wert ist leer → nicht matchen
        if exclude_empty and is_empty:
            return False
        
        # Wenn kein Text-Search aktiv, dann nur Empty-Filter prüfen
        search_text = filter_state.get("search_text", "").strip()
        if not search_text:
            return True  # Kein Text-Filter, nur Empty-Filter war relevant
        
        # Standard Text-Contains-Suche
        record_text = str(record_value).lower() if record_value else ""
        is_text_match = search_text.lower() in record_text
        
        logger.debug(f"🔍 Text-Match für '{record_value}': search='{search_text}', exclude_empty={exclude_empty}, match={is_text_match}")
        return is_text_match
    
    def _check_date_range_match(self, record, field_name, filter_state):
        """Prüft DateRange-Filter Match mit internen Jahr/Monat/Tag-Spalten"""
        
        # Leere Werte behandeln: Original-Feld prüfen
        record_value = record.get(field_name, "")
        is_empty_date = not record_value or str(record_value).strip() == ""
        
        # Wenn Datum leer ist, Einstellung für leere Werte prüfen
        if is_empty_date:
            show_empty = filter_state.get("show_empty", True)
            logger.debug(f"🗓️ Leeres Datum für {field_name}: show_empty={show_empty}")
            return show_empty
        
        try:
            # EFFIZIENTER ANSATZ: Nutze die bereits berechneten internen Jahr/Monat/Tag-Spalten
            record_jahr = record.get(f"_{field_name}_year")
            record_monat = record.get(f"_{field_name}_month")
            record_tag = record.get(f"_{field_name}_day")
            
            # Fallback: Wenn interne Spalten nicht existieren, selbst berechnen
            if record_jahr is None or record_monat is None or record_tag is None:
                from pdvm_datetime import Pdvm_DateTime
                pdvm_dt = Pdvm_DateTime("DEU")
                pdvm_dt.PdvmDateTime = float(record_value)
                record_jahr = pdvm_dt.Year
                record_monat = pdvm_dt.Month
                record_tag = pdvm_dt.Day
            
            # Ab-Datum prüfen (wenn gesetzt)
            ab_jahr = filter_state.get("ab_jahr")
            ab_monat = filter_state.get("ab_monat")
            ab_tag = filter_state.get("ab_tag")
            
            if ab_jahr is not None:
                if record_jahr < ab_jahr:
                    return False
                elif record_jahr == ab_jahr:
                    if ab_monat is not None:
                        if record_monat < ab_monat:
                            return False
                        elif record_monat == ab_monat:
                            if ab_tag is not None and record_tag < ab_tag:
                                return False
            
            # Bis-Datum prüfen (wenn gesetzt)
            bis_jahr = filter_state.get("bis_jahr")
            bis_monat = filter_state.get("bis_monat")
            bis_tag = filter_state.get("bis_tag")
            
            if bis_jahr is not None:
                if record_jahr > bis_jahr:
                    return False
                elif record_jahr == bis_jahr:
                    if bis_monat is not None:
                        if record_monat > bis_monat:
                            return False
                        elif record_monat == bis_monat:
                            if bis_tag is not None and record_tag > bis_tag:
                                return False
            
            logger.debug(f"🗓️ DateRange-Match für {record_jahr}-{record_monat:02d}-{record_tag:02d}: MATCH")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei DateRange-Filter für {field_name}: {e}")
            # Bei Fehlern: Datensatz durchlassen
            return True
    
    def get_filtered_data(self):
        """Gibt aktuell gefilterte Daten zurück"""
        return self.filtered_data.copy()
    
    def get_filter_state(self, field_name):
        """Gibt Filter-State für ein Feld zurück"""
        return self.filter_states.get(field_name, {})
    
    def get_dropdown_options(self, field_name):
        """Gibt alle verfügbaren Dropdown-Optionen mit Display-Werten zurück"""
        filter_state = self.filter_states.get(field_name, {})
        if filter_state.get("type") == "dropdown":
            # Raw-Keys mit Display-Mapping zurückgeben
            raw_keys = filter_state.get("all_keys", set())
            display_mapping = filter_state.get("key_display_mapping", {})
            
            # Liste von (raw_key, display_value) Tupeln für UI
            options = []
            for raw_key in sorted(raw_keys):
                display_value = display_mapping.get(raw_key, raw_key)
                options.append((raw_key, display_value))
            
            return options
        return []
    
    def is_any_filter_active(self):
        """Prüft ob irgendein Filter aktiv ist"""
        return any(filter_state["active"] for filter_state in self.filter_states.values())
    
    def get_active_filter_summary(self):
        """Gibt Zusammenfassung der aktiven Filter zurück"""
        active_filters = []
        for field_name, filter_state in self.filter_states.items():
            if filter_state["active"]:
                if filter_state["type"] == "dropdown":
                    count = len(filter_state["selected_keys"])
    
    def apply_date_range_on_original_column(self, field_name, range_data):
        """Filtert die Originaldaten direkt nach einem PDVM Date-Bereich (Zeitraum-Modus)."""
        from pdvm_datetime import Pdvm_DateTime
        ab_jahr = range_data.get("ab_jahr")
        ab_monat = range_data.get("ab_monat")
        ab_tag = range_data.get("ab_tag")
        bis_jahr = range_data.get("bis_jahr")
        bis_monat = range_data.get("bis_monat")
        bis_tag = range_data.get("bis_tag")

        # Defaults ergänzen
        ab_monat = ab_monat if ab_monat is not None else 1
        bis_monat = bis_monat if bis_monat is not None else 12
        ab_tag = ab_tag if ab_tag is not None else 1
        # Letzter Tag des Monats für bis_tag
        if bis_tag is None:
            try:
                tmp_dt = Pdvm_DateTime("DEU")
                tmp_dt.PdvmDateTimeT = (bis_jahr, bis_monat, 1, 0, 0, 0, 0)
                bis_tag = tmp_dt.monthDayLen[tmp_dt.Month]
            except Exception:
                bis_tag = 31

        # PDVM Date für Ab und Bis berechnen
        ab_dt = Pdvm_DateTime("DEU")
        ab_dt.PdvmDateTimeT = (ab_jahr, ab_monat, ab_tag, 0, 0, 0, 0)
        ab_value = ab_dt.PdvmDateTime

        bis_dt = Pdvm_DateTime("DEU")
        bis_dt.PdvmDateTimeT = (bis_jahr, bis_monat, bis_tag, 23, 59, 59, 999999)
        bis_value = bis_dt.PdvmDateTime

        # Filterung auf Originalspalte
        result = []
        for record in self.original_data:
            value = record.get(field_name)
            try:
                value_f = float(value)
                if ab_value <= value_f <= bis_value:
                    result.append(record)
            except Exception:
                continue
        self.filtered_data = result
        logger.info(f"🗓️ Zeitraum-Filter auf Originalspalte: {len(result)} Treffer")

    def get_active_filter_summary(self):
        """Gibt Zusammenfassung der aktiven Filter zurück"""
        active_filters = []
        for field_name, filter_state in self.filter_states.items():
            if filter_state["active"]:
                if filter_state["type"] == "dropdown":
                    count = len(filter_state["selected_keys"])
                    total = len(filter_state["all_keys"])
                    active_filters.append(f"{field_name}: {count}/{total} Keys")
                elif filter_state["type"] == "dateRange":
                    # DateRange-Filter Anzeige
                    active_filters.append(f"{field_name}: Datumsbereich")
                else:
                    # Text-Filter mit sicherem Zugriff
                    search_text = filter_state.get("search_text", "")
                    if search_text:
                        active_filters.append(f"{field_name}: '{search_text}'")
                    elif filter_state.get("exclude_empty", False):
                        active_filters.append(f"{field_name}: Leere ausschließen")
        return active_filters


class PdvmDropdownFilterWidget(QDialog):
    """
    Separates Dropdown-Filter-Widget als Dialog
    Komplett unabhängig von der Haupt-UI
    """
    
    # Signals
    filterApplied = pyqtSignal(str, set, bool)  # field_name, selected_keys, show_empty
    
    def __init__(self, field_name, filter_manager, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.filter_manager = filter_manager
        
        self.setWindowTitle(f"Filter: {field_name}")
        self.setModal(True)
        self.setMinimumSize(350, 450)
        
        # Aktuelle Filter-Daten laden
        self.filter_state = filter_manager.get_filter_state(field_name)
        self.all_options = filter_manager.get_dropdown_options(field_name)  # [(raw_key, display_value), ...]
        
        # UI Setup
        self._setup_ui()
        self._load_current_state()
    
    def _setup_ui(self):
        """Erstellt die kompakte Filter-UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)  # Kompakterer Abstand
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header_label = QLabel(f"Filter: {self.field_name}")
        header_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(header_label)
        
        # Info-Label
        info_label = QLabel(f"{len(self.all_options)} Optionen verfügbar")
        info_label.setStyleSheet("color: #666; font-size: 9px; margin-bottom: 5px;")
        layout.addWidget(info_label)
        
        # Buttons: Alle, Ohne - kompakter
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        
        self.all_button = QPushButton("✅ Alle")
        self.all_button.setMaximumHeight(28)
        self.all_button.clicked.connect(self._select_all)
        button_layout.addWidget(self.all_button)
        
        self.none_button = QPushButton("❌ Ohne")
        self.none_button.setMaximumHeight(28)
        self.none_button.clicked.connect(self._select_none)
        button_layout.addWidget(self.none_button)
        
        layout.addLayout(button_layout)
        
        # Leere-Werte Checkbox - kompakter
        self.empty_checkbox = QCheckBox("Leere Werte anzeigen")
        self.empty_checkbox.setStyleSheet("margin: 2px 0px;")
        layout.addWidget(self.empty_checkbox)
        
        # Separator - dünner
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setMaximumHeight(1)
        separator.setStyleSheet("margin: 4px 0px;")
        layout.addWidget(separator)
        
        # Kompakte Options-Liste OHNE ScrollArea bei wenigen Optionen
        self.option_checkboxes = {}  # raw_key -> checkbox mapping
        
        if len(self.all_options) <= 6:
            # Wenige Optionen: Direkt im Layout ohne ScrollArea
            for raw_key, display_value in self.all_options:
                checkbox = QCheckBox(f"{display_value}")
                checkbox.setToolTip(f"Raw-Key: {raw_key}")
                checkbox.setStyleSheet("margin: 1px 0px; padding: 2px;")
                self.option_checkboxes[raw_key] = checkbox
                layout.addWidget(checkbox)
        else:
            # Viele Optionen: ScrollArea mit kompakter Höhe
            scroll_area = QScrollArea()
            scroll_area.setMaximumHeight(150)  # Begrenzte Höhe
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_widget = QWidget()
            options_layout = QVBoxLayout(scroll_widget)
            options_layout.setSpacing(2)  # Sehr kompakt
            options_layout.setContentsMargins(4, 4, 4, 4)
            
            for raw_key, display_value in self.all_options:
                checkbox = QCheckBox(f"{display_value}")
                checkbox.setToolTip(f"Raw-Key: {raw_key}")
                checkbox.setStyleSheet("margin: 1px 0px; padding: 2px;")
                self.option_checkboxes[raw_key] = checkbox
                options_layout.addWidget(checkbox)
            
            # Layout straffen
            options_layout.addStretch(0)
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            layout.addWidget(scroll_area)
        
        # Action Buttons - kompakter
        action_layout = QHBoxLayout()
        action_layout.setSpacing(6)
        action_layout.setContentsMargins(0, 8, 0, 0)
        
        apply_button = QPushButton("Filter anwenden")
        apply_button.setMaximumHeight(30)
        apply_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 12px; }")
        apply_button.clicked.connect(self._apply_filter)
        action_layout.addWidget(apply_button)
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.setMaximumHeight(30)
        cancel_button.setStyleSheet("QPushButton { padding: 6px 12px; }")
        cancel_button.clicked.connect(self.reject)
        action_layout.addWidget(cancel_button)
        
        layout.addLayout(action_layout)
        
        # Dialog-Größe anpassen je nach Anzahl der Optionen
        option_count = len(self.all_options)
        if option_count <= 3:
            # Sehr wenige Optionen: Kompakte Größe
            self.setFixedSize(280, 200 + (option_count * 25))
        elif option_count <= 6:
            # Wenige Optionen: Mittlere Größe
            self.setFixedSize(300, 250 + (option_count * 25))
        else:
            # Viele Optionen: Feste Größe mit Scroll
            self.setFixedSize(320, 350)
        
        layout.addLayout(action_layout)
    
    def _load_current_state(self):
        """Lädt aktuellen Filter-Status basierend auf RAW-Keys"""
        selected_keys = self.filter_state.get("selected_keys", set())
        show_empty = self.filter_state.get("show_empty", True)
        
        # Checkboxes setzen - WICHTIG: RAW-Keys verwenden
        for raw_key, checkbox in self.option_checkboxes.items():
            checkbox.setChecked(raw_key in selected_keys)
            
        self.empty_checkbox.setChecked(show_empty)
        print(f"PdvmDropdownFilterWidget: Aktueller Status geladen - Selected keys: {selected_keys}")
    
    def _select_all(self):
        """Aktiviert alle Optionen"""
        for checkbox in self.option_checkboxes.values():
            checkbox.setChecked(True)
        self.empty_checkbox.setChecked(True)
    
    def _select_none(self):
        """Deaktiviert alle Optionen"""
        for checkbox in self.option_checkboxes.values():
            checkbox.setChecked(False)
        self.empty_checkbox.setChecked(False)
    
    def _apply_filter(self):
        """Wendet Filter an und schließt Dialog - WICHTIG: RAW-Keys sammeln"""
        selected_raw_keys = set()
        for raw_key, checkbox in self.option_checkboxes.items():
            if checkbox.isChecked():
                selected_raw_keys.add(raw_key)
        
        show_empty = self.empty_checkbox.isChecked()
        
        print(f"PdvmDropdownFilterWidget: Filter angewendet - Raw keys: {selected_raw_keys}, Show empty: {show_empty}")
        
        # Signal senden mit RAW-Keys
        self.filterApplied.emit(self.field_name, selected_raw_keys, show_empty)
        
        self.accept()


class PdvmDateRangeFilterWidget(QDialog):
    """
    DateRange-Filter-Widget als Dialog für Datums-Bereichsfilter
    Nutzt den AreaDatePicker für flexible Datums-Eingabe
    """
    
    # Signals
    filterApplied = pyqtSignal(str, dict)  # field_name, range_data
    
    def __init__(self, field_name, filter_manager, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.filter_manager = filter_manager
        
        self.setWindowTitle(f"Datumsfilter: {field_name}")
        self.setModal(True)
        self.setFixedSize(320, 280)  # Größere Größe für bessere Bedienbarkeit
        
        # Aktuelle Filter-Daten laden
        self.filter_state = filter_manager.get_filter_state(field_name)
        
        # UI Setup
        self._setup_ui()
        self._load_current_state()
    
    def _setup_ui(self):
        """Erstellt die DateRange-Filter-UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header
        header_label = QLabel(f"Datumsfilter: {self.field_name}")
        header_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(header_label)
        
        # Info-Label
        info_label = QLabel("Jahr-Monat-Tag Filter für Datumswerte")
        info_label.setStyleSheet("color: #666; font-size: 9px; margin-bottom: 5px;")
        layout.addWidget(info_label)
        
        # AreaDatePicker
        from pdvm_area_date_picker import PdvmAreaDatePicker
        self.date_picker = PdvmAreaDatePicker(self)
        self.date_picker.dateRangeChanged.connect(self._on_date_range_changed)
        layout.addWidget(self.date_picker)
        
        # Empty-Values Checkbox
        self.empty_checkbox = QCheckBox("Leere Datumswerte anzeigen")
        self.empty_checkbox.setChecked(True)
        layout.addWidget(self.empty_checkbox)
        
        # Button-Leiste
        button_layout = QHBoxLayout()
        
        # Reset Button
        reset_btn = QPushButton("Zurücksetzen")
        reset_btn.clicked.connect(self._reset_filter)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        # OK Button
        ok_btn = QPushButton("Anwenden")
        ok_btn.clicked.connect(self._apply_filter)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        # Cancel Button
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_current_state(self):
        """Lädt den aktuellen Filter-Status"""
        if self.filter_state.get("type") == "dateRange":
            # Bestehende Range-Daten in Picker setzen
            range_data = {
                "ab_jahr": self.filter_state.get("ab_jahr"),
                "ab_monat": self.filter_state.get("ab_monat"),
                "ab_tag": self.filter_state.get("ab_tag"),
                "bis_jahr": self.filter_state.get("bis_jahr"),
                "bis_monat": self.filter_state.get("bis_monat"),
                "bis_tag": self.filter_state.get("bis_tag")
            }
            self.date_picker.set_date_range(range_data)
            
            # Empty-Checkbox Status
            self.empty_checkbox.setChecked(self.filter_state.get("show_empty", True))
    
    def _on_date_range_changed(self, range_data):
        """Callback wenn sich der Datums-Bereich ändert"""
        # Für Live-Preview könnte hier die Anzeige aktualisiert werden
        pass
    
    def _reset_filter(self):
        """Setzt den Filter zurück"""
        self.date_picker._reset_to_default()
        self.empty_checkbox.setChecked(True)
    
    def _apply_filter(self):
        """Wendet den Filter an"""
        # Aktuelle Range-Daten vom Picker holen
        range_data = self.date_picker.get_current_range()
        
        # Empty-Checkbox-Status hinzufügen
        range_data["show_empty"] = self.empty_checkbox.isChecked()
        
        logger.info(f"🗓️ DateRange-Filter angewendet für {self.field_name}: {range_data}")
        
        # Signal senden
        self.filterApplied.emit(self.field_name, range_data)
        
        self.accept()
