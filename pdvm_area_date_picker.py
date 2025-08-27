# pdvm_area_date_picker.py
"""
AreaDatePicker für Datums-Bereichsfilter
Ermöglicht separate Eingabe von Jahr (4), Monat (2) und Tag (2) für Ab- und Bis-Datum
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QSizePolicy, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIntValidator
from pdvm_datetime import Pdvm_DateTime, PdvmDateTimeUtils
import logging

logger = logging.getLogger(__name__)

class PdvmAreaDatePicker(QWidget):
    """
    Datums-Bereichs-Picker für dateRange-Filter
    
    Features:
    - Separate Eingabe für Jahr (4), Monat (2), Tag (2)
    - Ab-Datum und Bis-Datum untereinander
    - Default: alle Werte leer (---, --, --) = alle Daten inklusive leer
    - Übernahme von Ab-Datum zu Bis-Datum bei Eingabe
    - Interne View-Spalten für Jahr, Monat, Tag über PdvmDateTime
    """
    
    # Signal wird ausgesendet wenn sich der Datumsbereich ändert
    dateRangeChanged = pyqtSignal(dict)  # {"ab_jahr": int, "ab_monat": int, "ab_tag": int, ...}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 180)  # Größere Größe für Checkbox und bessere Lesbarkeit
        
        # Status-Variablen
        self._updating = False  # Verhindert Rekursion bei Updates
        self.zeitraum_mode = False  # Schalter für Zeitraum-Modus
        
        # UI aufbauen
        self._setup_ui()
        
        # Initial alle Daten anzeigen (Default)
        self._reset_to_default()
        
        logger.debug("🗓️ AreaDatePicker initialisiert")
    
    def _setup_ui(self):
        """Baut die UI auf"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Titel
        title = QLabel("Datums-Bereich")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 9, QFont.Bold))
        title.setStyleSheet("color: #495057; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        layout.addWidget(separator)
        
        # Ab-Datum Sektion
        layout.addWidget(self._create_date_section("Ab:", "ab"))
        
        # Bis-Datum Sektion
        layout.addWidget(self._create_date_section("Bis:", "bis"))
        
        # Button-Leiste
        button_layout = QHBoxLayout()
        
        # Zeitraum-Modus Checkbox
        self.zeitraum_checkbox = QCheckBox("Zeitraum-Modus")
        self.zeitraum_checkbox.setToolTip("Aktiviert: PDVM Date-Bereich auf Originalspalte\nDeaktiviert: Jahr/Monat/Tag AND-Filter")
        self.zeitraum_checkbox.toggled.connect(self._on_zeitraum_mode_toggled)
        self.zeitraum_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 10px;
                color: #495057;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border: 1px solid #0056b3;
            }
        """)
        button_layout.addWidget(self.zeitraum_checkbox)
        
        button_layout.addStretch()
        
        # Reset Button
        reset_btn = QPushButton("↻")
        reset_btn.setMaximumWidth(25)
        reset_btn.setToolTip("Alle Werte zurücksetzen")
        reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(reset_btn)
        
        # Heute Button
        heute_btn = QPushButton("H")
        heute_btn.setMaximumWidth(25)
        heute_btn.setToolTip("Heutiges Datum für Ab und Bis")
        heute_btn.clicked.connect(self._set_heute)
        button_layout.addWidget(heute_btn)
        
        layout.addLayout(button_layout)
        
        # Stretch für kompakte Darstellung
        layout.addStretch()
    
    def _on_zeitraum_mode_toggled(self, checked):
        """Callback für Zeitraum-Modus Checkbox"""
        self.zeitraum_mode = checked
        
        # Signal mit entsprechendem Modus senden
        current_range = self.get_current_range()
        current_range["zeitraum_mode"] = checked
        
        self.dateRangeChanged.emit(current_range)
        
        mode_text = "Zeitraum-Modus (PDVM Date)" if checked else "Standard-Modus (Jahr/Monat/Tag AND)"
        logger.info(f"🔀 {mode_text} aktiviert")
    
    def _apply_zeitraum_filter(self):
        """Wendet den Zeitraum-Filter (PDVM Date-Bereich) an - Legacy-Methode"""
        # Legacy-Unterstützung: Checkbox aktivieren und Signal senden
        if not self.zeitraum_mode:
            self.zeitraum_checkbox.setChecked(True)  # Aktiviert automatisch den Modus
        else:
            # Wenn bereits aktiv, Signal erneut senden
            current_range = self.get_current_range()
            current_range["zeitraum_mode"] = True
            self.dateRangeChanged.emit(current_range)
            logger.info(f"🕒 Zeitraum-Filter erneut angewendet: {current_range}")
    
    def _create_date_section(self, label_text, prefix):
        """Erstellt eine Datums-Eingabe-Sektion (Ab oder Bis)"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(3)
        
        # Label
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 9))
        label.setStyleSheet("font-weight: bold; color: #495057; margin-bottom: 2px;")
        section_layout.addWidget(label)
        
        # Eingabe-Zeile: Jahr - Monat - Tag
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(4)
        
        # Jahr (4 Stellen)
        jahr_edit = QLineEdit()
        jahr_edit.setPlaceholderText("----")
        jahr_edit.setMaxLength(4)
        jahr_edit.setValidator(QIntValidator(1000, 9999))
        jahr_edit.setMinimumWidth(45)
        jahr_edit.setMaximumWidth(50)
        jahr_edit.setMinimumHeight(25)  # Erhöhte Mindesthöhe
        jahr_edit.setAlignment(Qt.AlignCenter)
        jahr_edit.setStyleSheet("padding: 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px;")
        jahr_edit.textChanged.connect(lambda: self._on_input_changed(prefix, "jahr"))
        setattr(self, f"{prefix}_jahr_edit", jahr_edit)
        
        # Monat (2 Stellen)
        monat_edit = QLineEdit()
        monat_edit.setPlaceholderText("--")
        monat_edit.setMaxLength(2)
        monat_edit.setValidator(QIntValidator(1, 12))
        monat_edit.setMinimumWidth(30)
        monat_edit.setMaximumWidth(35)
        monat_edit.setMinimumHeight(25)  # Erhöhte Mindesthöhe
        monat_edit.setAlignment(Qt.AlignCenter)
        monat_edit.setStyleSheet("padding: 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px;")
        monat_edit.textChanged.connect(lambda: self._on_input_changed(prefix, "monat"))
        setattr(self, f"{prefix}_monat_edit", monat_edit)
        
        # Tag (2 Stellen)
        tag_edit = QLineEdit()
        tag_edit.setPlaceholderText("--")
        tag_edit.setMaxLength(2)
        tag_edit.setValidator(QIntValidator(1, 31))
        tag_edit.setMinimumWidth(30)
        tag_edit.setMaximumWidth(35)
        tag_edit.setMinimumHeight(25)  # Erhöhte Mindesthöhe
        tag_edit.setAlignment(Qt.AlignCenter)
        tag_edit.setStyleSheet("padding: 6px; border: 1px solid #ced4da; border-radius: 3px; font-size: 12px;")
        tag_edit.textChanged.connect(lambda: self._on_input_changed(prefix, "tag"))
        setattr(self, f"{prefix}_tag_edit", tag_edit)
        
        # Layout zusammenbauen
        input_layout.addWidget(jahr_edit)
        sep1 = QLabel("-")
        sep1.setStyleSheet("color: #6c757d; font-weight: bold;")
        input_layout.addWidget(sep1)
        input_layout.addWidget(monat_edit)
        sep2 = QLabel("-")
        sep2.setStyleSheet("color: #6c757d; font-weight: bold;")
        input_layout.addWidget(sep2)
        input_layout.addWidget(tag_edit)
        input_layout.addStretch()
        
        section_layout.addLayout(input_layout)
        
        return section
    
    def _on_input_changed(self, changed_prefix, field_type):
        """Wird aufgerufen wenn sich ein Eingabefeld ändert - nur analoger Wert wird übernommen"""
        if self._updating:
            return
        
        self._updating = True
        
        try:
            # Wenn Ab-Datum geändert wurde, nur den entsprechenden Wert ins Bis-Datum übernehmen
            if changed_prefix == "ab":
                self._copy_analogous_field_to_bis(field_type)
            
            # Aktuellen Bereich validieren und Signal senden
            current_range = self.get_current_range()
            current_range["zeitraum_mode"] = self.zeitraum_mode  # Aktuellen Modus hinzufügen
            self.dateRangeChanged.emit(current_range)
            
            logger.debug(f"🗓️ Datums-Bereich geändert ({field_type}): {current_range}")
            
        finally:
            self._updating = False
    
    def _copy_analogous_field_to_bis(self, field_type):
        """Kopiert nur den geänderten Feldtyp vom Ab- ins Bis-Datum"""
        # Nur das entsprechende Feld übernehmen
        if field_type == "jahr":
            self.bis_jahr_edit.setText(self.ab_jahr_edit.text())
        elif field_type == "monat":
            self.bis_monat_edit.setText(self.ab_monat_edit.text())
        elif field_type == "tag":
            self.bis_tag_edit.setText(self.ab_tag_edit.text())
        
        logger.debug(f"🔄 Analoger Wert übernommen: {field_type}")
    
    def _copy_ab_to_bis(self):
        """Kopiert Ab-Datum-Werte ins Bis-Datum (komplette Übernahme - für Buttons)"""
        # SOFORTIGE Übernahme: Kopiere aktuellen Ab-Wert ins entsprechende Bis-Feld
        self.bis_jahr_edit.setText(self.ab_jahr_edit.text())
        self.bis_monat_edit.setText(self.ab_monat_edit.text())
        self.bis_tag_edit.setText(self.ab_tag_edit.text())
    
    def _reset_to_default(self):
        """Setzt alle Felder auf Default (leer) zurück"""
        self._updating = True
        
        try:
            # Alle Eingabefelder leeren
            for prefix in ["ab", "bis"]:
                getattr(self, f"{prefix}_jahr_edit").clear()
                getattr(self, f"{prefix}_monat_edit").clear()
                getattr(self, f"{prefix}_tag_edit").clear()
            
            # Signal für "alle Daten anzeigen"
            reset_range = self.get_current_range()
            reset_range["zeitraum_mode"] = self.zeitraum_mode
            self.dateRangeChanged.emit(reset_range)
            
            logger.debug("🗓️ AreaDatePicker auf Default zurückgesetzt")
            
        finally:
            self._updating = False
    
    def _set_heute(self):
        """Setzt heutiges Datum für Ab und Bis"""
        self._updating = True
        
        try:
            # Heutiges PdvmDateTime holen
            heute_dt = Pdvm_DateTime("DEU")
            heute_dt.PdvmDateTime = PdvmDateTimeUtils.PdvmDateTimeNow()
            
            # In beide Bereiche setzen
            for prefix in ["ab", "bis"]:
                getattr(self, f"{prefix}_jahr_edit").setText(str(heute_dt.Year))
                getattr(self, f"{prefix}_monat_edit").setText(f"{heute_dt.Month:02d}")
                getattr(self, f"{prefix}_tag_edit").setText(f"{heute_dt.Day:02d}")
            
            # Signal senden
            heute_range = self.get_current_range()
            heute_range["zeitraum_mode"] = self.zeitraum_mode
            self.dateRangeChanged.emit(heute_range)
            
            logger.debug(f"🗓️ Heutiges Datum gesetzt: {heute_dt.Date}")
            
        finally:
            self._updating = False
    
    def get_current_range(self):
        """
        Liefert den aktuellen Datums-Bereich
        
        Returns:
            dict: {
                "ab_jahr": int|None, "ab_monat": int|None, "ab_tag": int|None,
                "bis_jahr": int|None, "bis_monat": int|None, "bis_tag": int|None,
                "active": bool  # True wenn mindestens ein Wert gesetzt
            }
        """
        def parse_int_or_none(text):
            try:
                return int(text) if text.strip() else None
            except (ValueError, AttributeError):
                return None
        
        range_data = {
            "ab_jahr": parse_int_or_none(self.ab_jahr_edit.text()),
            "ab_monat": parse_int_or_none(self.ab_monat_edit.text()),
            "ab_tag": parse_int_or_none(self.ab_tag_edit.text()),
            "bis_jahr": parse_int_or_none(self.bis_jahr_edit.text()),
            "bis_monat": parse_int_or_none(self.bis_monat_edit.text()),
            "bis_tag": parse_int_or_none(self.bis_tag_edit.text())
        }
        
        # Filter ist aktiv wenn mindestens ein Wert gesetzt ist
        range_data["active"] = any(v is not None for v in range_data.values())
        
        return range_data
    
    def set_date_range(self, range_data):
        """
        Setzt einen Datums-Bereich
        
        Args:
            range_data (dict): Wie von get_current_range() zurückgegeben
        """
        self._updating = True
        
        try:
            for prefix in ["ab", "bis"]:
                # Jahr
                jahr_val = range_data.get(f"{prefix}_jahr")
                getattr(self, f"{prefix}_jahr_edit").setText(str(jahr_val) if jahr_val else "")
                
                # Monat (mit führender Null)
                monat_val = range_data.get(f"{prefix}_monat")
                getattr(self, f"{prefix}_monat_edit").setText(f"{monat_val:02d}" if monat_val else "")
                
                # Tag (mit führender Null)
                tag_val = range_data.get(f"{prefix}_tag")
                getattr(self, f"{prefix}_tag_edit").setText(f"{tag_val:02d}" if tag_val else "")
            
            logger.debug(f"🗓️ Datums-Bereich gesetzt: {range_data}")
            
        finally:
            self._updating = False
    
    def is_empty(self):
        """Prüft ob alle Felder leer sind (Default-Zustand)"""
        current_range = self.get_current_range()
        return not current_range["active"]
    
    def get_filter_description(self):
        """Liefert eine Beschreibung des aktuellen Filters für UI-Anzeige"""
        current_range = self.get_current_range()
        
        if not current_range["active"]:
            return "Alle Daten"
        
        def format_date_part(jahr, monat, tag):
            parts = []
            if jahr: parts.append(str(jahr))
            if monat: parts.append(f"{monat:02d}")
            if tag: parts.append(f"{tag:02d}")
            return "-".join(parts) if parts else "***"
        
        ab_str = format_date_part(
            current_range["ab_jahr"], 
            current_range["ab_monat"], 
            current_range["ab_tag"]
        )
        
        bis_str = format_date_part(
            current_range["bis_jahr"], 
            current_range["bis_monat"], 
            current_range["bis_tag"]
        )
        
        if ab_str == bis_str:
            return f"📅 {ab_str}"
        else:
            return f"📅 {ab_str} ↔ {bis_str}"
