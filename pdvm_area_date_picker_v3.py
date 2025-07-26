# pdvm_area_date_picker_v3.py
"""
Area Date Picker V3 mit korrekter Layout-Behandlung
Behebt das Überlappungs-Problem zwischen Zeitraum-Checkbox und "Leere ausschließen"
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QSpinBox, QCheckBox, QPushButton, QFrame, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmAreaDatePickerV3(QWidget):
    """
    Area Date Picker V3 mit korrekter Layout-Behandlung
    
    Verbesserungen:
    1. Korrekte Layout-Struktur ohne Überlappungen
    2. Intelligente Übernahme (analoger Wert)
    3. Verbesserte Eingabefeld-Höhen
    4. Zeitraum-Checkbox richtig positioniert
    5. "Leere ausschließen" eigener Bereich
    """
    
    filterApplied = pyqtSignal(str, dict)  # field_name, range_data
    
    def __init__(self, field_name: str, current_range: dict = None, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.current_range = current_range or {}
        
        # State-Variablen
        self.zeitraum_mode = self.current_range.get("zeitraum_mode", False)
        self.show_empty = self.current_range.get("show_empty", True)
        
        # UI-Setup
        self._setup_ui()
        self._load_current_values()
        self._setup_connections()
    
    def _setup_ui(self):
        """Erstellt die UI-Struktur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel(f"🗓️ Datumsbereich-Filter: {self.field_name}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # Zeitraum-Modus Bereich (OBEN)
        self._create_zeitraum_mode_section(main_layout)
        
        # Von-Bis Eingabebereich
        self._create_date_input_section(main_layout)
        
        # Leere Werte Bereich (UNTEN, separater Bereich)
        self._create_empty_values_section(main_layout)
        
        # Button-Bereich
        self._create_button_section(main_layout)
    
    def _create_zeitraum_mode_section(self, layout):
        """Erstellt den Zeitraum-Modus-Bereich"""
        zeitraum_frame = QFrame()
        zeitraum_frame.setFrameShape(QFrame.StyledPanel)
        zeitraum_frame.setStyleSheet("background-color: #f8f8f8; padding: 8px; margin-bottom: 10px;")
        zeitraum_layout = QVBoxLayout(zeitraum_frame)
        zeitraum_layout.setContentsMargins(8, 8, 8, 8)
        zeitraum_layout.setSpacing(8)  # Mehr Abstand zwischen Elementen
        
        # Zeitraum-Checkbox
        self.zeitraum_checkbox = QCheckBox("🕐 Zeitraum-Modus (PDVM-DateTime-Bereich)")
        self.zeitraum_checkbox.setChecked(self.zeitraum_mode)
        self.zeitraum_checkbox.setToolTip(
            "Zeitraum-Modus: Filter auf Original-PDVM-DateTime-Spalte\\n" +
            "Standard-Modus: Filter auf Jahr/Monat/Tag-Komponenten"
        )
        zeitraum_layout.addWidget(self.zeitraum_checkbox)
        
        # Info-Label
        self.mode_info_label = QLabel()
        self.mode_info_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        self._update_mode_info()
        zeitraum_layout.addWidget(self.mode_info_label)
        
        layout.addWidget(zeitraum_frame)
    
    def _create_date_input_section(self, layout):
        """Erstellt den Eingabebereich für Von-Bis-Datum"""
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(10)
        
        # Von-Bis Grid
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(8)
        
        # Header
        grid_layout.addWidget(QLabel(""), 0, 0)
        grid_layout.addWidget(QLabel("Jahr"), 0, 1)
        grid_layout.addWidget(QLabel("Monat"), 0, 2)
        grid_layout.addWidget(QLabel("Tag"), 0, 3)
        
        # Von-Zeile
        von_label = QLabel("Von:")
        von_label.setFont(QFont("Arial", 9, QFont.Bold))
        grid_layout.addWidget(von_label, 1, 0)
        
        self.ab_jahr_spin = self._create_spin_box(1900, 2100, "Jahr")
        self.ab_monat_spin = self._create_spin_box(1, 12, "Monat")
        self.ab_tag_spin = self._create_spin_box(1, 31, "Tag")
        
        grid_layout.addWidget(self.ab_jahr_spin, 1, 1)
        grid_layout.addWidget(self.ab_monat_spin, 1, 2)
        grid_layout.addWidget(self.ab_tag_spin, 1, 3)
        
        # Bis-Zeile
        bis_label = QLabel("Bis:")
        bis_label.setFont(QFont("Arial", 9, QFont.Bold))
        grid_layout.addWidget(bis_label, 2, 0)
        
        self.bis_jahr_spin = self._create_spin_box(1900, 2100, "Jahr")
        self.bis_monat_spin = self._create_spin_box(1, 12, "Monat")
        self.bis_tag_spin = self._create_spin_box(1, 31, "Tag")
        
        grid_layout.addWidget(self.bis_jahr_spin, 2, 1)
        grid_layout.addWidget(self.bis_monat_spin, 2, 2)
        grid_layout.addWidget(self.bis_tag_spin, 2, 3)
        
        input_layout.addLayout(grid_layout)
        layout.addWidget(input_frame)
    
    def _create_empty_values_section(self, layout):
        """Erstellt den separaten Bereich für leere Werte"""
        # Zusätzlicher Abstand vor dem Empty-Values-Bereich
        layout.addSpacing(15)
        
        empty_frame = QFrame()
        empty_frame.setFrameShape(QFrame.StyledPanel)
        empty_frame.setStyleSheet("background-color: #fff3cd; padding: 8px; margin-top: 10px;")
        empty_layout = QVBoxLayout(empty_frame)
        empty_layout.setContentsMargins(8, 8, 8, 8)
        empty_layout.setSpacing(8)  # Mehr Abstand zwischen Elementen
        
        # Empty Values Checkbox
        self.show_empty_checkbox = QCheckBox("📝 Leere Geburtsdaten anzeigen")
        self.show_empty_checkbox.setChecked(self.show_empty)
        self.show_empty_checkbox.setToolTip(
            "Aktiviert: Datensätze ohne Geburtsdatum werden angezeigt\\n" +
            "Deaktiviert: Nur Datensätze mit Geburtsdatum werden angezeigt"
        )
        empty_layout.addWidget(self.show_empty_checkbox)
        
        # Info-Label
        empty_info = QLabel("💡 Diese Einstellung betrifft alle Datensätze ohne gültiges Datum")
        empty_info.setStyleSheet("color: #856404; font-size: 10px; font-style: italic; margin-top: 5px;")
        empty_layout.addWidget(empty_info)
        
        layout.addWidget(empty_frame)
        
        # Zusätzlicher Abstand nach dem Empty-Values-Bereich
        layout.addSpacing(10)
    
    def _create_button_section(self, layout):
        """Erstellt den Button-Bereich"""
        button_layout = QHBoxLayout()
        
        # Apply Button
        self.apply_btn = QPushButton("✅ Filter anwenden")
        self.apply_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.apply_btn)
        
        # Clear Button
        self.clear_btn = QPushButton("❌ Zurücksetzen")
        self.clear_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 8px;")
        button_layout.addWidget(self.clear_btn)
        
        # Cancel Button
        self.cancel_btn = QPushButton("🚫 Abbrechen")
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_spin_box(self, min_val: int, max_val: int, placeholder: str) -> QSpinBox:
        """Erstellt eine SpinBox mit verbesserten Eigenschaften"""
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSpecialValueText("")  # Leerer Wert
        spin.setValue(min_val - 1)    # Startwert = leer
        spin.setMinimumHeight(28)     # VERBESSERUNG: Höhere Eingabefelder
        spin.setToolTip(f"{placeholder} eingeben oder leer lassen")
        
        return spin
    
    def _setup_connections(self):
        """Richtet die Signal-Verbindungen ein"""
        # Zeitraum-Checkbox
        self.zeitraum_checkbox.toggled.connect(self._on_zeitraum_mode_changed)
        
        # Von-Eingaben (für intelligente Übernahme)
        self.ab_jahr_spin.valueChanged.connect(
            lambda: self._on_input_changed("ab", "jahr")
        )
        self.ab_monat_spin.valueChanged.connect(
            lambda: self._on_input_changed("ab", "monat")
        )
        self.ab_tag_spin.valueChanged.connect(
            lambda: self._on_input_changed("ab", "tag")
        )
        
        # Buttons
        self.apply_btn.clicked.connect(self._apply_filter)
        self.clear_btn.clicked.connect(self._clear_filter)
        self.cancel_btn.clicked.connect(self.close)
    
    def _load_current_values(self):
        """Lädt die aktuellen Werte in die UI"""
        try:
            # Von-Werte
            if self.current_range.get("ab_jahr"):
                self.ab_jahr_spin.setValue(self.current_range["ab_jahr"])
            if self.current_range.get("ab_monat"):
                self.ab_monat_spin.setValue(self.current_range["ab_monat"])
            if self.current_range.get("ab_tag"):
                self.ab_tag_spin.setValue(self.current_range["ab_tag"])
            
            # Bis-Werte
            if self.current_range.get("bis_jahr"):
                self.bis_jahr_spin.setValue(self.current_range["bis_jahr"])
            if self.current_range.get("bis_monat"):
                self.bis_monat_spin.setValue(self.current_range["bis_monat"])
            if self.current_range.get("bis_tag"):
                self.bis_tag_spin.setValue(self.current_range["bis_tag"])
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden der aktuellen Werte: {e}")
    
    def _on_zeitraum_mode_changed(self, checked: bool):
        """Behandelt Änderungen des Zeitraum-Modus"""
        self.zeitraum_mode = checked
        self._update_mode_info()
        logger.info(f"🕐 Zeitraum-Modus {'aktiviert' if checked else 'deaktiviert'}")
    
    def _update_mode_info(self):
        """Aktualisiert das Info-Label für den Modus"""
        if self.zeitraum_mode:
            info_text = "Filter auf Original-PDVM-DateTime-Spalte (präziser Zeitraum)"
        else:
            info_text = "Filter auf Jahr/Monat/Tag-Komponenten (flexibler)"
        
        self.mode_info_label.setText(info_text)
    
    def _on_input_changed(self, changed_prefix: str, field_type: str):
        """
        Behandelt Eingabe-Änderungen mit intelligenter Übernahme
        
        Args:
            changed_prefix: "ab" oder "bis"
            field_type: "jahr", "monat", "tag"
        """
        if changed_prefix == "ab":
            # VERBESSERUNG: Analoger Wert-Transfer von Ab zu Bis
            self._copy_analogous_field_to_bis(field_type)
    
    def _copy_analogous_field_to_bis(self, field_type: str):
        """
        Kopiert nur den entsprechenden Wert von Ab zu Bis
        
        Args:
            field_type: "jahr", "monat", "tag"
        """
        try:
            if field_type == "jahr":
                ab_value = self.ab_jahr_spin.value()
                if ab_value > self.ab_jahr_spin.minimum():
                    self.bis_jahr_spin.setValue(ab_value)
                    
            elif field_type == "monat":
                ab_value = self.ab_monat_spin.value()
                if ab_value > self.ab_monat_spin.minimum():
                    self.bis_monat_spin.setValue(ab_value)
                    
            elif field_type == "tag":
                ab_value = self.ab_tag_spin.value()
                if ab_value > self.ab_tag_spin.minimum():
                    self.bis_tag_spin.setValue(ab_value)
            
            logger.debug(f"🔄 Analoger Transfer: {field_type} von Ab zu Bis")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim analogen Transfer: {e}")
    
    def _apply_filter(self):
        """Wendet den Filter an"""
        try:
            # Werte sammeln
            range_data = {
                "zeitraum_mode": self.zeitraum_mode,
                "show_empty": self.show_empty_checkbox.isChecked()
            }
            
            # Von-Werte (nur wenn > minimum)
            if self.ab_jahr_spin.value() > self.ab_jahr_spin.minimum():
                range_data["ab_jahr"] = self.ab_jahr_spin.value()
            if self.ab_monat_spin.value() > self.ab_monat_spin.minimum():
                range_data["ab_monat"] = self.ab_monat_spin.value()
            if self.ab_tag_spin.value() > self.ab_tag_spin.minimum():
                range_data["ab_tag"] = self.ab_tag_spin.value()
            
            # Bis-Werte (nur wenn > minimum)
            if self.bis_jahr_spin.value() > self.bis_jahr_spin.minimum():
                range_data["bis_jahr"] = self.bis_jahr_spin.value()
            if self.bis_monat_spin.value() > self.bis_monat_spin.minimum():
                range_data["bis_monat"] = self.bis_monat_spin.value()
            if self.bis_tag_spin.value() > self.bis_tag_spin.minimum():
                range_data["bis_tag"] = self.bis_tag_spin.value()
            
            # Filter anwenden
            self.filterApplied.emit(self.field_name, range_data)
            
            logger.info(f"✅ Datumsfilter angewendet für {self.field_name}: {range_data}")
            
            # Dialog schließen
            self.close()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des Filters: {e}")
    
    def _clear_filter(self):
        """Setzt den Filter zurück"""
        try:
            # Alle SpinBoxes zurücksetzen
            for spin in [self.ab_jahr_spin, self.ab_monat_spin, self.ab_tag_spin,
                        self.bis_jahr_spin, self.bis_monat_spin, self.bis_tag_spin]:
                spin.setValue(spin.minimum() - 1)
            
            # Checkboxes zurücksetzen
            self.zeitraum_checkbox.setChecked(False)
            self.show_empty_checkbox.setChecked(True)
            
            logger.info(f"🔄 Filter zurückgesetzt für {self.field_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen: {e}")
    
    def get_current_range(self) -> dict:
        """Gibt den aktuellen Bereichs-Zustand zurück"""
        range_data = {
            "zeitraum_mode": self.zeitraum_mode,
            "show_empty": self.show_empty_checkbox.isChecked()
        }
        
        # Werte nur hinzufügen wenn gesetzt
        if self.ab_jahr_spin.value() > self.ab_jahr_spin.minimum():
            range_data["ab_jahr"] = self.ab_jahr_spin.value()
        if self.ab_monat_spin.value() > self.ab_monat_spin.minimum():
            range_data["ab_monat"] = self.ab_monat_spin.value()
        if self.ab_tag_spin.value() > self.ab_tag_spin.minimum():
            range_data["ab_tag"] = self.ab_tag_spin.value()
        
        if self.bis_jahr_spin.value() > self.bis_jahr_spin.minimum():
            range_data["bis_jahr"] = self.bis_jahr_spin.value()
        if self.bis_monat_spin.value() > self.bis_monat_spin.minimum():
            range_data["bis_monat"] = self.bis_monat_spin.value()
        if self.bis_tag_spin.value() > self.bis_tag_spin.minimum():
            range_data["bis_tag"] = self.bis_tag_spin.value()
        
        return range_data


# Dialog-Wrapper für Integration
class PdvmDateRangeFilterDialogV3(QDialog):
    """Dialog-Wrapper für den Area Date Picker V3"""
    
    def __init__(self, field_name: str, current_state: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Datumsfilter: {field_name}")
        self.setModal(True)
        self.resize(500, 400)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Area Date Picker einbetten
        self.date_picker = PdvmAreaDatePickerV3(field_name, current_state, self)
        self.date_picker.filterApplied.connect(self._on_filter_applied)
        layout.addWidget(self.date_picker)
        
        # Ergebnis speichern
        self.filter_settings = None
    
    def _on_filter_applied(self, field_name: str, range_data: dict):
        """Behandelt angewendeten Filter"""
        self.filter_settings = range_data
        self.accept()
    
    def get_filter_settings(self) -> dict:
        """Gibt die Filter-Einstellungen zurück"""
        return self.filter_settings or {}
