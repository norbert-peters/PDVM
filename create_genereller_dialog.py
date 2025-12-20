# -*- coding: utf-8 -*-
"""
Handler: Generellen Dialog erstellen

Workflow-Handler zum Erstellen neuer Frame/View/Dialog-Kombinationen

AUTOR: Norbert Peters
DATUM: 08.12.2025
VERSION: 1.0
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sqlite3

logger = logging.getLogger(__name__)


class CreateGenerellerDialogWizard(QDialog):
    """Dialog-Wizard zum Erstellen genereller Dialoge"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.frame_guid = None
        self.view_guid = None
        self.dialog_guid = None
        
        self.setWindowTitle("Generellen Dialog erstellen")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        self._load_existing_data()
        self._init_ui()
    
    def _load_existing_data(self):
        """Lade bestehende Views und Dialoge"""
        conn = sqlite3.connect("Daten/pdvm_system.db")
        cursor = conn.cursor()
        
        # Views laden
        cursor.execute("SELECT uid, name FROM sys_viewdaten ORDER BY name")
        self.existing_views = cursor.fetchall()
        
        # Dialoge laden
        cursor.execute("SELECT uid, name FROM sys_dialogdaten ORDER BY name")
        self.existing_dialogs = cursor.fetchall()
        
        conn.close()
        
        logger.info(f"📋 {len(self.existing_views)} Views und {len(self.existing_dialogs)} Dialoge geladen")
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🔧 Generellen Dialog erstellen")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        info = QLabel("Workflow: Name → Frame → View → Dialog → Ausführen")
        info.setStyleSheet("color: gray; font-size: 9pt; padding: 5px;")
        layout.addWidget(info)
        
        layout.addSpacing(10)
        
        # === SCHRITT 1: Name ===
        name_group = QGroupBox("📝 Schritt 1: Name")
        name_layout = QVBoxLayout()
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. 'Mandanten verwalten'")
        name_layout.addWidget(QLabel("Dialog-Name:"))
        name_layout.addWidget(self.input_name)
        
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)
        
        # === SCHRITT 2: View ===
        view_group = QGroupBox("🖼️ Schritt 2: View-GUID")
        view_layout = QVBoxLayout()
        
        self.radio_view_group = QButtonGroup()
        self.radio_view_existing = QRadioButton("Bestehende View verwenden")
        self.radio_view_new = QRadioButton("Neue View erstellen")
        self.radio_view_new.setChecked(True)
        
        self.radio_view_group.addButton(self.radio_view_existing)
        self.radio_view_group.addButton(self.radio_view_new)
        
        view_layout.addWidget(self.radio_view_existing)
        
        # Dropdown für bestehende Views
        self.combo_existing_views = QComboBox()
        self.combo_existing_views.addItem("-- View auswählen --", None)
        for view_guid, view_name in self.existing_views:
            self.combo_existing_views.addItem(f"{view_name} ({view_guid[:8]}...)", view_guid)
        self.combo_existing_views.setEnabled(False)
        view_layout.addWidget(self.combo_existing_views)
        
        view_layout.addSpacing(10)
        view_layout.addWidget(self.radio_view_new)
        
        # Input für neue View
        self.input_view_table = QLineEdit()
        self.input_view_table.setPlaceholderText("z.B. 'sys_mandanten'")
        self.input_view_table.setEnabled(True)
        view_layout.addWidget(QLabel("Tabellen-Name:"))
        view_layout.addWidget(self.input_view_table)
        
        # Signal-Verbindungen
        self.radio_view_existing.toggled.connect(self._on_view_mode_changed)
        
        view_group.setLayout(view_layout)
        layout.addWidget(view_group)
        
        # === SCHRITT 3: Dialog ===
        dialog_group = QGroupBox("💬 Schritt 3: Dialog-GUID")
        dialog_layout = QVBoxLayout()
        
        dialog_layout.addWidget(QLabel("Dialog auswählen (zuletzt verwendet wird vorgetragen):"))
        
        self.combo_dialogs = QComboBox()
        self.combo_dialogs.addItem("-- Dialog auswählen --", None)
        
        # Zuletzt verwendeten Dialog vorschlagen (aus Systemsteuerung)
        last_dialog_guid = self._get_last_dialog_guid()
        last_index = 0
        
        for i, (dialog_guid, dialog_name) in enumerate(self.existing_dialogs, start=1):
            self.combo_dialogs.addItem(f"{dialog_name} ({dialog_guid[:8]}...)", dialog_guid)
            if dialog_guid == last_dialog_guid:
                last_index = i
        
        if last_index > 0:
            self.combo_dialogs.setCurrentIndex(last_index)
        
        dialog_layout.addWidget(self.combo_dialogs)
        
        dialog_group.setLayout(dialog_layout)
        layout.addWidget(dialog_group)
        
        layout.addStretch()
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        
        btn_execute = QPushButton("✅ Ausführen")
        btn_execute.clicked.connect(self._on_execute)
        btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(btn_execute)
        
        layout.addLayout(button_layout)
    
    def _on_view_mode_changed(self, checked):
        """View-Modus umgeschaltet"""
        if checked:
            # Bestehende View
            self.combo_existing_views.setEnabled(True)
            self.input_view_table.setEnabled(False)
        else:
            # Neue View
            self.combo_existing_views.setEnabled(False)
            self.input_view_table.setEnabled(True)
    
    def _get_last_dialog_guid(self):
        """Hole zuletzt verwendete Dialog-GUID aus Systemsteuerung"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs:
                last_guid = gcs.field_value('LAST_DIALOG_GUID')
                return last_guid
        except Exception as e:
            logger.warning(f"Konnte letzte Dialog-GUID nicht laden: {e}")
        return None
    
    def _save_last_dialog_guid(self, dialog_guid):
        """Speichere zuletzt verwendete Dialog-GUID"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs:
                gcs.set_field_value('LAST_DIALOG_GUID', dialog_guid)
                gcs._db.save_all_data()
        except Exception as e:
            logger.warning(f"Konnte Dialog-GUID nicht speichern: {e}")
    
    def _on_execute(self):
        """Workflow ausführen"""
        # Validierung
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte Namen eingeben!")
            return
        
        # View-GUID ermitteln
        if self.radio_view_existing.isChecked():
            # Bestehende View
            self.view_guid = self.combo_existing_views.currentData()
            if not self.view_guid:
                QMessageBox.warning(self, "Fehler", "Bitte View auswählen!")
                return
        else:
            # Neue View erstellen
            table_name = self.input_view_table.text().strip()
            if not table_name:
                QMessageBox.warning(self, "Fehler", "Bitte Tabellen-Name eingeben!")
                return
            
            # View erstellen
            self.view_guid = self._create_view(name, table_name)
            if not self.view_guid:
                QMessageBox.critical(self, "Fehler", "View konnte nicht erstellt werden!")
                return
        
        # Dialog-GUID ermitteln
        self.dialog_guid = self.combo_dialogs.currentData()
        if not self.dialog_guid:
            QMessageBox.warning(self, "Fehler", "Bitte Dialog auswählen!")
            return
        
        # Frame erstellen
        self.frame_guid = self._create_frame(name, self.view_guid, self.dialog_guid)
        if not self.frame_guid:
            QMessageBox.critical(self, "Fehler", "Frame konnte nicht erstellt werden!")
            return
        
        # Letzte Dialog-GUID speichern
        self._save_last_dialog_guid(self.dialog_guid)
        
        # Erfolg
        QMessageBox.information(
            self,
            "Erfolg",
            f"✅ Genereller Dialog erstellt!\n\n"
            f"Frame-GUID: {self.frame_guid}\n"
            f"View-GUID: {self.view_guid}\n"
            f"Dialog-GUID: {self.dialog_guid}"
        )
        
        self.accept()
    
    def _create_view(self, name, table_name):
        """Erstellt neue View mit Template-basierter Methode"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # View-DB-Instanz erstellen
            view_db = PdvmCentralDatenbank('sys_viewdaten')
            
            # Neuen Datensatz mit Template anlegen
            view_guid = view_db.anlegen_mit_template()
            
            # ROOT-Properties setzen
            view_db.set_value('ROOT', 'TABLE', table_name)
            view_db.set_value('ROOT', 'VIEW_GUID', view_guid)
            view_db.set_value('ROOT', 'NO_DATA', True)
            
            # VIEW_CONFIG-Properties setzen
            view_db.set_value('VIEW_CONFIG', 'TITLE', name)
            view_db.set_value('VIEW_CONFIG', 'SHOW_SEARCH', True)
            view_db.set_value('VIEW_CONFIG', 'SHOW_FILTER', True)
            view_db.set_value('VIEW_CONFIG', 'SHOW_SORT', True)
            
            # Speichern
            view_db.save_all_values()
            
            logger.info(f"✅ View erstellt: {view_guid}")
            return view_guid
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der View: {e}")
            return None
    
    def _create_frame(self, name, view_guid, dialog_guid):
        """Erstellt Frame mit Template-basierter Methode"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Frame-DB-Instanz erstellen
            frame_db = PdvmCentralDatenbank('sys_framedaten')
            
            # Neuen Datensatz mit Template anlegen
            frame_guid = frame_db.anlegen_mit_template()
            
            # ROOT-Properties setzen
            frame_db.set_value('ROOT', 'TABLE', "")  # Wird aus View übernommen
            frame_db.set_value('ROOT', 'VIEW_GUID', view_guid)
            frame_db.set_value('ROOT', 'DIALOG_GUID', dialog_guid)
            frame_db.set_value('ROOT', 'HEADER_TEXT', name)
            frame_db.set_value('ROOT', 'EDIT_TYPE', "system_editor")  # Standard für generelle Dialoge
            
            # Speichern
            frame_db.save_all_values()
            
            logger.info(f"✅ Frame erstellt: {frame_guid}")
            return frame_guid
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Frames: {e}")
            return None


def handle_create_genereller_dialog(**kwargs):
    """
    Handler-Funktion für Menü-Integration
    
    Erstellt generellen Dialog mit Wizard
    """
    logger.info("🔧 Handler: create_genereller_dialog")
    
    # Main-App holen
    main_app = kwargs.get('main_app')
    if not main_app:
        logger.error("❌ main_app nicht gefunden!")
        return
    
    # Wizard öffnen
    wizard = CreateGenerellerDialogWizard(parent=main_app)
    if wizard.exec_() == QDialog.Accepted:
        logger.info(f"✅ Dialog erstellt:")
        logger.info(f"   Frame: {wizard.frame_guid}")
        logger.info(f"   View: {wizard.view_guid}")
        logger.info(f"   Dialog: {wizard.dialog_guid}")
        
        QMessageBox.information(
            main_app,
            "Erfolg",
            "Dialog erfolgreich erstellt!\n\n"
            "Sie können den Dialog jetzt über das Menü aufrufen."
        )
