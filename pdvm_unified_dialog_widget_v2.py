# -*- coding: utf-8 -*-
"""
PDVM Unified Dialog Widget - Version 2
Stufenweiser Aufbau basierend auf originalem PdvmDialogWidget-Ablauf
Mit Tab-Architektur: View-Tab und Input-Tab
"""

import sys
import json
import logging
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
    QGroupBox, QSplitter, QFrame, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class UnifiedDialogManager:
    """Vereinfachter Dialog Manager - Stufe 1"""
    
    def __init__(self, call_data: dict):
        """Initialisiert Manager mit Call-Daten"""
        self.call_data = call_data
        self.user_guid = call_data.get('user_guid')
        self.frame_guid = call_data.get('frame_guid')
        self.language = call_data.get('language', 'de')
        
        # Vereinfachte Test-Daten
        self.frame_name = f"Test Frame {self.frame_guid[:8]}" if self.frame_guid else "Test Frame"
        self.view_guid = f"view-{self.frame_guid[:8]}" if self.frame_guid else "view-test"
        self.root_table = "test_table"
        
        # Status-Variablen
        self.last_root_guid = None
        self.current_stichtag = "2025-01-01"
        
        logger.info(f"✅ UnifiedDialogManager initialisiert")
        logger.info(f"   Frame: {self.frame_name}")
        logger.info(f"   View-GUID: {self.view_guid}")
        logger.info(f"   User: {self.user_guid}")
    
    def get_call_data(self, **overrides):
        """Erstellt Call-Daten für Child-Widgets"""
        result = self.call_data.copy()
        result.update(overrides)
        return result
    
    def save_last_guid(self, guid: str):
        """Speichert letzte ausgewählte GUID"""
        self.last_root_guid = guid
        logger.info(f"✅ Letzte GUID gespeichert: {guid}")


class UnifiedPdvmDialogWidget(QWidget):
    """Unified PDVM Dialog Widget - Version 2 mit Tab-Architektur"""
    
    # Signale wie im Original
    selection_made = pyqtSignal(dict)
    dialog_closed = pyqtSignal()
    field_edited = pyqtSignal(object, object, object)
    
    def __init__(self, call_data: dict, parent=None):
        super().__init__(parent)
        logger.info("🔹 UnifiedPdvmDialogWidget V2 gestartet")
        
        self.manager = UnifiedDialogManager(call_data)
        self.parent_window = parent
        
        # Haupt-Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab-Widget Container
        self.tab_widget = None
        self.view_tab = None
        self.input_tab = None
        
        self._init_ui()
        
        logger.info("✅ Dialog-Widget erfolgreich initialisiert")
    
    def _init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        # Header mit Frame-Info
        self._create_header()
        
        # Tab-Widget erstellen
        self._create_tab_widget()
        
        # Button-Bereich unten
        self._create_button_area()
    
    def _create_header(self):
        """Erstellt Header mit Frame-Informationen"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # Frame-Titel
        title_label = QLabel(f"📋 {self.manager.frame_name}")
        title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setStyleSheet("color: #1976d2;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status-Info
        status_info = QLabel(f"User: {self.manager.user_guid[:8]}... | View: {self.manager.view_guid}")
        status_info.setStyleSheet("font-size: 10px; color: #666;")
        header_layout.addWidget(status_info)
        
        # GUID-Status
        guid_status = "✅ GUID ausgewählt" if self.manager.last_root_guid else "❌ Keine GUID"
        guid_label = QLabel(guid_status)
        guid_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        header_layout.addWidget(guid_label)
        
        self.main_layout.addWidget(header_frame)
    
    def _create_tab_widget(self):
        """Erstellt das Tab-Widget mit View- und Input-Tab"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 2px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #e3f2fd;
                border-bottom-color: #e3f2fd;
            }
        """)
        
        # View-Tab erstellen
        self._create_view_tab()
        
        # Input-Tab erstellen
        self._create_input_tab()
        
        self.main_layout.addWidget(self.tab_widget)
    
    def _create_view_tab(self):
        """Erstellt den View-Tab (Auswahl/Suche)"""
        self.view_tab = QWidget()
        view_layout = QVBoxLayout(self.view_tab)
        view_layout.setContentsMargins(15, 15, 15, 15)
        
        # View-Header
        view_header = QLabel("🔍 Datenauswahl / View-Manager")
        view_header.setFont(QFont("", 12, QFont.Bold))
        view_header.setStyleSheet("color: #1976d2; margin-bottom: 10px;")
        view_layout.addWidget(view_header)
        
        # View-Info Bereich
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        view_info = QLabel(f"""
📊 View-Manager Informationen

🔹 View-GUID: {self.manager.view_guid}
🔹 Root-Tabelle: {self.manager.root_table}
🔹 Letzte GUID: {self.manager.last_root_guid or 'Keine ausgewählt'}

Hier würde der echte PdvmViewManager stehen mit:
• Datensuche und -filter
• Listenansicht der verfügbaren Datensätze
• Sortierung und Gruppierung
• Auswahl-Rückgabe an Input-Widget

Status: {'Bereit für Auswahl' if not self.manager.last_root_guid else 'GUID ausgewählt'}
        """.strip())
        
        view_info.setWordWrap(True)
        view_info.setStyleSheet("font-family: 'Courier New'; font-size: 11px;")
        info_layout.addWidget(view_info)
        
        view_layout.addWidget(info_frame)
        
        # Simulierte Datenliste
        self._create_mock_data_list(view_layout)
        
        # View-Buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        select_button = QPushButton("✅ Auswahl übernehmen")
        select_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        select_button.clicked.connect(self._on_view_selection)
        button_layout.addWidget(select_button)
        
        new_button = QPushButton("➕ Neuen Datensatz erstellen")
        new_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        new_button.clicked.connect(self._on_new_record)
        button_layout.addWidget(new_button)
        
        button_layout.addStretch()
        view_layout.addWidget(button_frame)
        
        self.tab_widget.addTab(self.view_tab, "🔍 Auswahl")
    
    def _create_mock_data_list(self, parent_layout):
        """Erstellt eine simulierte Datenliste für Tests"""
        list_frame = QGroupBox("📋 Verfügbare Datensätze")
        list_layout = QVBoxLayout(list_frame)
        
        # Simulierte Daten
        mock_data = [
            {"guid": "12345678-1234-1234-1234-123456789001", "name": "Test Datensatz 1", "datum": "2025-01-15"},
            {"guid": "12345678-1234-1234-1234-123456789002", "name": "Test Datensatz 2", "datum": "2025-01-16"},
            {"guid": "12345678-1234-1234-1234-123456789003", "name": "Test Datensatz 3", "datum": "2025-01-17"},
        ]
        
        for i, data in enumerate(mock_data):
            item_frame = QFrame()
            item_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    padding: 8px;
                    margin: 2px;
                }
                QFrame:hover {
                    background-color: #f0f8ff;
                    border-color: #2196f3;
                }
            """)
            item_layout = QHBoxLayout(item_frame)
            
            # Dateninfo
            info_label = QLabel(f"📄 {data['name']} | {data['datum']} | {data['guid'][:8]}...")
            info_label.setStyleSheet("font-family: 'Courier New'; font-size: 10px;")
            item_layout.addWidget(info_label)
            
            item_layout.addStretch()
            
            # Auswahl-Button
            select_btn = QPushButton("Auswählen")
            select_btn.setMaximumWidth(80)
            select_btn.clicked.connect(lambda checked, guid=data['guid'], name=data['name']: self._select_mock_data(guid, name))
            item_layout.addWidget(select_btn)
            
            list_layout.addWidget(item_frame)
        
        parent_layout.addWidget(list_frame)
    
    def _create_input_tab(self):
        """Erstellt den Input-Tab (Eingabe/Bearbeitung)"""
        self.input_tab = QWidget()
        input_layout = QVBoxLayout(self.input_tab)
        input_layout.setContentsMargins(15, 15, 15, 15)
        
        # Input-Header
        input_header = QLabel("📝 Dateneingabe / InputControls")
        input_header.setFont(QFont("", 12, QFont.Bold))
        input_header.setStyleSheet("color: #1976d2; margin-bottom: 10px;")
        input_layout.addWidget(input_header)
        
        # Input-Info Bereich
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #fff9f0;
                border: 1px solid #ffd700;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        input_info = QLabel(f"""
📝 InputWidget Informationen

🔹 Frame: {self.manager.frame_name}
🔹 Root-GUID: {self.manager.last_root_guid or 'Keine ausgewählt'}
🔹 Root-Tabelle: {self.manager.root_table}
🔹 Stichtag: {self.manager.current_stichtag}

Hier würde das echte PdvmInputWidget stehen mit:
• InputControls aus Frame-Definition
• Automatisches Layout nach Konfiguration
• Datenvalidierung und -speicherung
• Stichtag-Management

InputControls können auch OHNE Daten aufgebaut werden.
Bei Auswahl im View werden die entsprechenden Daten geladen.
        """.strip())
        
        input_info.setWordWrap(True)
        input_info.setStyleSheet("font-family: 'Courier New'; font-size: 11px;")
        info_layout.addWidget(input_info)
        
        input_layout.addWidget(info_frame)
        
        # Simulierte InputControls
        self._create_mock_input_controls(input_layout)
        
        # Input-Buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        save_button = QPushButton("💾 Speichern")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_button.setEnabled(bool(self.manager.last_root_guid))
        save_button.clicked.connect(self._on_save_data)
        button_layout.addWidget(save_button)
        
        reset_button = QPushButton("🔄 Zurücksetzen")
        reset_button.clicked.connect(self._on_reset_input)
        button_layout.addWidget(reset_button)
        
        button_layout.addStretch()
        
        to_view_button = QPushButton("⬅️ Zurück zur Auswahl")
        to_view_button.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        button_layout.addWidget(to_view_button)
        
        input_layout.addWidget(button_frame)
        
        self.tab_widget.addTab(self.input_tab, "📝 Eingabe")
    
    def _create_mock_input_controls(self, parent_layout):
        """Erstellt simulierte InputControls für Tests"""
        controls_frame = QGroupBox("🔧 InputControls (Simulation)")
        controls_layout = QVBoxLayout(controls_frame)
        
        # Simulierte Controls
        from PyQt5.QtWidgets import QLineEdit, QTextEdit, QComboBox, QDateEdit
        from PyQt5.QtCore import QDate
        
        # Name-Feld
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Datensatz-Name eingeben...")
        name_layout.addWidget(name_edit)
        controls_layout.addLayout(name_layout)
        
        # Beschreibung-Feld
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Beschreibung:"))
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(80)
        desc_edit.setPlaceholderText("Beschreibung eingeben...")
        desc_layout.addWidget(desc_edit)
        controls_layout.addLayout(desc_layout)
        
        # Kategorie-Auswahl
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Kategorie:"))
        cat_combo = QComboBox()
        cat_combo.addItems(["Kategorie 1", "Kategorie 2", "Kategorie 3"])
        cat_layout.addWidget(cat_combo)
        controls_layout.addLayout(cat_layout)
        
        # Datum-Feld
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Datum:"))
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(date_edit)
        controls_layout.addLayout(date_layout)
        
        parent_layout.addWidget(controls_frame)
    
    def _create_button_area(self):
        """Erstellt den Button-Bereich unten"""
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        
        # Hauptaktionen
        ok_button = QPushButton("✅ OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ok_button.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_button)
        
        apply_button = QPushButton("🔄 Anwenden")
        apply_button.clicked.connect(self._on_apply)
        button_layout.addWidget(apply_button)
        
        button_layout.addStretch()
        
        # Info-Button
        info_button = QPushButton("ℹ️ Info")
        info_button.clicked.connect(self._show_info)
        button_layout.addWidget(info_button)
        
        close_button = QPushButton("🔒 Schließen")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        close_button.clicked.connect(self._on_close)
        button_layout.addWidget(close_button)
        
        self.main_layout.addWidget(button_frame)
    
    # Event Handlers
    def _select_mock_data(self, guid: str, name: str):
        """Handler für Auswahl von Mock-Daten"""
        logger.info(f"🎯 Mock-Daten ausgewählt: {name} ({guid})")
        
        # GUID speichern
        self.manager.save_last_guid(guid)
        
        # UI aktualisieren
        self._update_ui_after_selection(guid, name)
        
        # Zum Input-Tab wechseln
        self.tab_widget.setCurrentIndex(1)
        
        # Signal senden
        selection_data = {
            'selected_guid': guid,
            'selected_name': name,
            'frame_guid': self.manager.frame_guid,
            'view_guid': self.manager.view_guid
        }
        self.selection_made.emit(selection_data)
    
    def _on_view_selection(self):
        """Handler für View-Auswahl (Dummy)"""
        logger.info("🔍 Dummy-Auswahl wird übernommen")
        
        # Simuliere Auswahl
        dummy_guid = "dummy-guid-12345"
        dummy_name = "Dummy-Auswahl"
        
        self._select_mock_data(dummy_guid, dummy_name)
    
    def _on_new_record(self):
        """Handler für neuen Datensatz"""
        logger.info("➕ Neuer Datensatz wird erstellt")
        
        # Neue GUID generieren
        import uuid
        new_guid = str(uuid.uuid4())
        
        self._select_mock_data(new_guid, "Neuer Datensatz")
    
    def _update_ui_after_selection(self, guid: str, name: str):
        """Aktualisiert UI nach Auswahl"""
        logger.info(f"🔄 UI wird nach Auswahl aktualisiert: {name}")
        
        # Header neu erstellen
        old_header = self.main_layout.itemAt(0).widget()
        if old_header:
            self.main_layout.removeWidget(old_header)
            old_header.setParent(None)
        
        # Neuen Header erstellen
        self._create_header()
        
        # Header an erste Position setzen
        header_widget = self.main_layout.itemAt(-1).widget()
        self.main_layout.removeWidget(header_widget)
        self.main_layout.insertWidget(0, header_widget)
        
        # Save-Button aktivieren
        input_tab_widgets = self.input_tab.findChildren(QPushButton)
        for button in input_tab_widgets:
            if "Speichern" in button.text():
                button.setEnabled(True)
    
    def _on_save_data(self):
        """Handler für Daten speichern"""
        logger.info("💾 Daten werden gespeichert")
        
        if not self.manager.last_root_guid:
            QMessageBox.warning(self, "Warnung", "Keine GUID ausgewählt!")
            return
        
        QMessageBox.information(self, "Speichern", f"Daten für GUID {self.manager.last_root_guid[:8]}... erfolgreich gespeichert!")
    
    def _on_reset_input(self):
        """Handler für Input zurücksetzen"""
        logger.info("🔄 Input wird zurückgesetzt")
        
        # Input-Controls leeren (würde in echter Implementierung gemacht)
        QMessageBox.information(self, "Reset", "InputControls wurden zurückgesetzt!")
    
    def _on_ok(self):
        """Handler für OK"""
        logger.info("✅ Dialog mit OK beendet")
        self._on_save_data()
        self._on_close()
    
    def _on_apply(self):
        """Handler für Anwenden"""
        logger.info("🔄 Änderungen angewendet")
        self._on_save_data()
    
    def _show_info(self):
        """Zeigt Dialog-Informationen"""
        info_text = f"""
📋 Dialog-Informationen

🔹 Frame-GUID: {self.manager.frame_guid}
🔹 User-GUID: {self.manager.user_guid}
🔹 View-GUID: {self.manager.view_guid}
🔹 Aktuelle GUID: {self.manager.last_root_guid or 'Keine'}
🔹 Sprache: {self.manager.language}

📊 Tab-Status:
• View-Tab: {'Aktiv' if self.tab_widget.currentIndex() == 0 else 'Inaktiv'}
• Input-Tab: {'Aktiv' if self.tab_widget.currentIndex() == 1 else 'Inaktiv'}

🔧 Version: UnifiedPdvmDialogWidget V2
        """.strip()
        
        QMessageBox.information(self, "Dialog-Info", info_text)
    
    def _on_close(self):
        """Handler für Schließen"""
        logger.info("🔒 Dialog wird geschlossen")
        
        # Cleanup
        self.dialog_closed.emit()
        
        if self.parent_window:
            self.parent_window.close()
        else:
            self.close()
    
    def closeEvent(self, event):
        """Event beim Schließen"""
        try:
            logger.info("✅ Dialog ordnungsgemäß geschlossen")
            self.dialog_closed.emit()
        except Exception as e:
            logger.error(f"❌ Fehler beim Schließen: {e}")
        
        event.accept()


# Kompatibilitäts-Alias
PdvmDialogWidget = UnifiedPdvmDialogWidget


if __name__ == "__main__":
    # Test-Programm für das Unified Dialog Widget
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = QApplication(sys.argv)
    
    # Test-Call-Data - einfach änderbar für verschiedene Tests
    test_call_data = {
        "user_guid": "4886ad26-061b-4662-a762-c8c83f36692d",
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "language": "de"
    }
    
    # Test-Window
    main_window = QMainWindow()
    main_window.setWindowTitle("🧪 Unified PDVM Dialog Widget V2 - Test")
    main_window.resize(900, 700)
    
    try:
        # Dialog Widget erstellen
        widget = UnifiedPdvmDialogWidget(test_call_data, main_window)
        main_window.setCentralWidget(widget)
        
        # Signal-Handler für Tests
        def on_selection_made(data):
            print(f"✅ Auswahl gemacht: {data}")
        
        def on_dialog_closed():
            print("✅ Dialog geschlossen")
        
        widget.selection_made.connect(on_selection_made)
        widget.dialog_closed.connect(on_dialog_closed)
        
        main_window.show()
        
        print("✅ Unified PDVM Dialog Widget V2 erfolgreich gestartet")
        print("📋 Test-Call-Data:")
        for key, value in test_call_data.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Fehler beim Starten: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(app.exec_())
