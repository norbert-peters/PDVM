#!/usr/bin/env python3
# demo_date_range_filter_final.py
"""
Finale Demonstration des DateRange-Filter-Systems
"""

import sys
import os
import logging

# PyQt5 Imports
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout, QTextEdit
from PyQt5.QtCore import Qt, QTimer

# Lokale Imports
from pdvm_area_date_picker import PdvmAreaDatePicker
from pdvm_filter_manager import PdvmDateRangeFilterWidget
from pd_datetime import Pdvm_DateTime, PdvmDateTimeUtils

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DateRangeDemoWindow(QMainWindow):
    """Demo-Fenster für das DateRange-Filter-System"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🗓️ DateRange-Filter Demonstration")
        self.setGeometry(100, 100, 800, 600)
        
        # Test-Daten (korrekte Julian-Werte)
        self.test_data = [
            {"GEBURTSDATUM": 1985074.0, "NAME": "Max Mustermann", "ALTER": 40},
            {"GEBURTSDATUM": 1990335.0, "NAME": "Lisa Schmidt", "ALTER": 35},
            {"GEBURTSDATUM": 2000183.0, "NAME": "Tom Weber", "ALTER": 25},
            {"GEBURTSDATUM": 1975235.0, "NAME": "Anna Müller", "ALTER": 50},
            {"GEBURTSDATUM": 1970001.0, "NAME": "Hans Meier", "ALTER": 55},
            {"GEBURTSDATUM": "", "NAME": "Ohne Geburtsdatum", "ALTER": "?"}
        ]
        
        # Setup UI
        self._setup_ui()
        
        # Initiale Daten anzeigen
        self._update_data_display()
        
        logger.info("🚀 DateRange-Filter-Demo gestartet")
    
    def _setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Titel
        title = QLabel("🗓️ DateRange-Filter System - Finale Demonstration")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Info-Text
        info = QLabel("Testen Sie das neue DateRange-Filter-System mit Jahr/Monat/Tag-Eingabe")
        info.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(info)
        
        # AreaDatePicker
        picker_section = QWidget()
        picker_layout = QVBoxLayout(picker_section)
        
        picker_label = QLabel("📅 AreaDatePicker:")
        picker_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        picker_layout.addWidget(picker_label)
        
        self.area_picker = PdvmAreaDatePicker()
        self.area_picker.dateRangeChanged.connect(self._on_date_range_changed)
        picker_layout.addWidget(self.area_picker)
        
        layout.addWidget(picker_section)
        
        # Filter-Status
        self.filter_status = QLabel("Filter: Alle Daten werden angezeigt")
        self.filter_status.setStyleSheet("background: #ecf0f1; padding: 8px; margin: 10px; border-radius: 5px;")
        layout.addWidget(self.filter_status)
        
        # Control-Buttons
        button_section = QWidget()
        button_layout = QHBoxLayout(button_section)
        
        dialog_btn = QPushButton("🔧 Dialog-Filter öffnen")
        dialog_btn.clicked.connect(self._open_dialog_filter)
        button_layout.addWidget(dialog_btn)
        
        heute_btn = QPushButton("📅 Heute setzen")
        heute_btn.clicked.connect(self._set_heute)
        button_layout.addWidget(heute_btn)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self._reset_filter)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        layout.addWidget(button_section)
        
        # Daten-Anzeige
        data_label = QLabel("📊 Testdaten (mit DateRange-Filter):")
        data_label.setStyleSheet("font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(data_label)
        
        self.data_display = QTextEdit()
        self.data_display.setMaximumHeight(200)
        self.data_display.setStyleSheet("font-family: 'Courier New'; font-size: 11px; background: #f8f9fa;")
        layout.addWidget(self.data_display)
        
        # Statistiken
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #2c3e50; margin-top: 10px; font-size: 11px;")
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
    
    def _on_date_range_changed(self, range_data):
        """Callback für Änderungen im AreaDatePicker"""
        description = self.area_picker.get_filter_description()
        self.filter_status.setText(f"Filter: {description}")
        
        # Daten aktualisieren
        self._update_data_display(range_data)
        
        logger.info(f"🗓️ Filter geändert: {range_data}")
    
    def _update_data_display(self, filter_range=None):
        """Aktualisiert die Datenanzeige mit Filter"""
        filtered_data = self._apply_filter(filter_range) if filter_range else self.test_data
        
        # Tabelle erstellen
        output = []
        output.append("┌─────────────────────┬─────────────────┬──────┬─────────────────────────────┐")
        output.append("│ Name                │ Geburtsdatum    │ Alter│ Interne Spalten             │")
        output.append("├─────────────────────┼─────────────────┼──────┼─────────────────────────────┤")
        
        for person in filtered_data:
            name = person["NAME"][:19].ljust(19)
            geburtsdatum = person["GEBURTSDATUM"]
            alter = str(person["ALTER"]).ljust(5)
            
            if geburtsdatum:
                try:
                    dt = Pdvm_DateTime("DEU")
                    dt.PdvmDateTime = float(geburtsdatum)
                    date_str = dt.Date.ljust(15)
                    internal = f"Y:{dt.Year} M:{dt.Month} D:{dt.Day}"
                except:
                    date_str = "Fehler".ljust(15)
                    internal = "N/A"
            else:
                date_str = "Leer".ljust(15)
                internal = "N/A"
            
            output.append(f"│ {name} │ {date_str} │ {alter}│ {internal.ljust(27)} │")
        
        output.append("└─────────────────────┴─────────────────┴──────┴─────────────────────────────┘")
        
        self.data_display.setText("\n".join(output))
        
        # Statistiken
        total_count = len(self.test_data)
        filtered_count = len(filtered_data)
        self.stats_label.setText(f"📈 Angezeigt: {filtered_count} von {total_count} Datensätzen")
    
    def _apply_filter(self, filter_range):
        """Wendet den DateRange-Filter an"""
        if not filter_range or not filter_range.get("active", False):
            return self.test_data
        
        filtered = []
        
        for person in self.test_data:
            geburtsdatum = person["GEBURTSDATUM"]
            
            # Ohne Datum
            if not geburtsdatum:
                if filter_range.get("show_empty", True):
                    filtered.append(person)
                continue
            
            try:
                dt = Pdvm_DateTime("DEU")
                dt.PdvmDateTime = float(geburtsdatum)
                
                # Filter-Checks
                matches = True
                
                # Jahr-Filter
                if filter_range.get("ab_jahr") and dt.Year < filter_range["ab_jahr"]:
                    matches = False
                if filter_range.get("bis_jahr") and dt.Year > filter_range["bis_jahr"]:
                    matches = False
                
                # Monat-Filter
                if filter_range.get("ab_monat") and dt.Month < filter_range["ab_monat"]:
                    matches = False
                if filter_range.get("bis_monat") and dt.Month > filter_range["bis_monat"]:
                    matches = False
                
                # Tag-Filter
                if filter_range.get("ab_tag") and dt.Day < filter_range["ab_tag"]:
                    matches = False
                if filter_range.get("bis_tag") and dt.Day > filter_range["bis_tag"]:
                    matches = False
                
                if matches:
                    filtered.append(person)
                    
            except Exception as e:
                logger.error(f"Fehler beim Filtern von {person['NAME']}: {e}")
        
        return filtered
    
    def _open_dialog_filter(self):
        """Öffnet den Dialog-Filter"""
        # Fake Filter-Manager für Demo
        class FakeFilterManager:
            def get_filter_state(self, field_name):
                return {
                    "type": "dateRange",
                    "ab_jahr": None,
                    "ab_monat": None,
                    "ab_tag": None,
                    "bis_jahr": None,
                    "bis_monat": None,
                    "bis_tag": None,
                    "show_empty": True,
                    "active": False
                }
        
        fake_manager = FakeFilterManager()
        
        # Dialog öffnen
        dialog = PdvmDateRangeFilterWidget("GEBURTSDATUM", fake_manager, self)
        dialog.filterApplied.connect(self._on_dialog_filter_applied)
        
        result = dialog.exec_()
        if result:
            logger.info("✅ Dialog-Filter angewendet")
        else:
            logger.info("❌ Dialog-Filter abgebrochen")
    
    def _on_dialog_filter_applied(self, field_name, range_data):
        """Callback für Dialog-Filter"""
        logger.info(f"🎯 Dialog-Filter angewendet für {field_name}: {range_data}")
        
        if range_data.get("active", False):
            description = f"Dialog: {field_name}"
            self.filter_status.setText(f"Filter: {description}")
            self._update_data_display(range_data)
        else:
            self.filter_status.setText("Filter: Alle Daten (Dialog-Filter deaktiviert)")
            self._update_data_display()
    
    def _set_heute(self):
        """Setzt heutiges Datum im AreaDatePicker"""
        self.area_picker._set_heute()
    
    def _reset_filter(self):
        """Reset alle Filter"""
        self.area_picker._reset_to_default()
        self.filter_status.setText("Filter: Alle Daten werden angezeigt")
        self._update_data_display()

def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    
    # Demo-Fenster erstellen und anzeigen
    window = DateRangeDemoWindow()
    window.show()
    
    print("🚀 DateRange-Filter-Demo gestartet!")
    print("=" * 50)
    print("✅ Funktionen:")
    print("   📅 AreaDatePicker: Jahr/Monat/Tag-Eingabe mit Auto-Copy")
    print("   🔧 Dialog-Filter: Modal-Dialog für Filtereinstellungen")
    print("   📊 Live-Filterung: Sofortige Anzeige der gefilterten Daten")
    print("   🔄 Reset-Funktion: Zurücksetzen aller Filter")
    print()
    print("🗓️ Testdaten:")
    print("   • Max Mustermann (15.03.1985)")
    print("   • Lisa Schmidt (01.12.1990)")
    print("   • Tom Weber (01.07.2000)")
    print("   • Anna Müller (23.08.1975)")
    print("   • Hans Meier (01.01.1970)")
    print("   • Ohne Geburtsdatum")
    
    # Event-Loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
