# -*- coding: utf-8 -*-
"""
Handler: Generellen Dialog erstellen

Workflow-Handler zum Erstellen neuer Frame/View/Dialog-Kombinationen
für generelle Dialoge mit system_editor oder input_controls.

AUTOR: Norbert Peters
DATUM: 08.12.2025
VERSION: 1.0
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QComboBox, QMessageBox,
    QWidget, QScrollArea, QFrame, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sqlite3

logger = logging.getLogger(__name__)


class CreateGenerellerDialogWizard(QDialog):
    """Dialog-Wizard zum Erstellen genereller Dialoge"""
    
    def __init__(self, gcs, parent=None):
        super().__init__(parent)
        
        self.gcs = gcs  # ← GCS aus Context verfügbar
        self.frame_guid = None
        self.view_guid = None
        self.dialog_guid = None
        
        self.setWindowTitle("Generellen Dialog erstellen")
        self.setModal(True)
        self.setFixedWidth(500)  # Feste Breite
        self.setMinimumHeight(550)
        
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
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Content-Bereich (feste Breite)
        content_widget = QWidget()
        content_widget.setFixedWidth(500)
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        main_layout.addWidget(content_widget)
        main_layout.addStretch()  # Spacer für Rest
        
        # Header
        header = QLabel("🔧 Generellen Dialog erstellen")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        info = QLabel("Workflow: Name → View → Dialog → Edit-Type → Ausführen")
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
        
        # Zuletzt verwendeten Dialog vorschlagen (aus GCS)
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
        
        # === SCHRITT 4: Edit-Type ===
        edit_type_group = QGroupBox("⚙️ Schritt 4: Edit-Type")
        edit_type_layout = QVBoxLayout()
        
        edit_type_layout.addWidget(QLabel("Bearbeitungs-Modus wählen:"))
        
        self.combo_edit_type = QComboBox()
        self.combo_edit_type.addItem("system_editor - Direkte Tabellen-Bearbeitung", "system_editor")
        self.combo_edit_type.addItem("input_controls - Template-basierte Input-Controls", "input_controls")
        
        # Tooltip mit Erklärung
        self.combo_edit_type.setToolTip(
            "system_editor: Bearbeitet Datensätze direkt in der Tabelle\n"
            "input_controls: Verwendet Template 55555... für Control-Konfiguration"
        )
        
        edit_type_layout.addWidget(self.combo_edit_type)
        
        # Info-Label
        self.label_edit_type_info = QLabel()
        self.label_edit_type_info.setWordWrap(True)
        self.label_edit_type_info.setStyleSheet("color: gray; font-size: 9pt; padding: 5px;")
        self._update_edit_type_info()
        edit_type_layout.addWidget(self.label_edit_type_info)
        
        # Signal für Info-Update
        self.combo_edit_type.currentIndexChanged.connect(self._update_edit_type_info)
        
        edit_type_group.setLayout(edit_type_layout)
        layout.addWidget(edit_type_group)
        
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
    
    def _update_edit_type_info(self):
        """Aktualisiert Info-Text für Edit-Type"""
        edit_type = self.combo_edit_type.currentData()
        
        if edit_type == "system_editor":
            info = (
                "📝 <b>system_editor</b>: Bearbeitet Datensätze direkt in der Tabelle.<br>"
                "→ Verwendet für: sys_mandanten Stammdaten, sys_benutzer, etc.<br>"
                "→ Properties werden aus ROOT_CONTROLS generiert"
            )
        else:  # input_controls
            info = (
                "🎛️ <b>input_controls</b>: Template-basierte Input-Control-Konfiguration.<br>"
                "→ Verwendet für: Verwaltung von Input-Controls aus Template 55555...<br>"
                "→ Tabs und Controls aus CONTROL_PROPERTIES"
            )
        
        self.label_edit_type_info.setText(info)
    
    def _get_last_dialog_guid(self):
        """Hole zuletzt verwendete Dialog-GUID aus GCS"""
        try:
            last_guid = self.gcs.field_value('LAST_DIALOG_GUID')
            return last_guid
        except Exception as e:
            logger.warning(f"Konnte letzte Dialog-GUID nicht laden: {e}")
        return None
    
    def _save_last_dialog_guid(self, dialog_guid):
        """Speichere zuletzt verwendete Dialog-GUID in GCS"""
        try:
            self.gcs.set_field_value('LAST_DIALOG_GUID', dialog_guid)
            self.gcs._db.save_all_values()
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
        
        # Edit-Type ermitteln
        edit_type = self.combo_edit_type.currentData()
        
        # Frame erstellen
        self.frame_guid = self._create_frame(name, self.view_guid, self.dialog_guid, edit_type)
        if not self.frame_guid:
            QMessageBox.critical(self, "Fehler", "Frame konnte nicht erstellt werden!")
            return
        
        # Letzte Dialog-GUID speichern
        self._save_last_dialog_guid(self.dialog_guid)
        
        # Erfolg-Nachricht
        logger.info(f"✅ Genereller Dialog erstellt!")
        logger.info(f"   Frame-GUID: {self.frame_guid}")
        logger.info(f"   View-GUID: {self.view_guid}")
        logger.info(f"   Dialog-GUID: {self.dialog_guid}")
        logger.info(f"   Edit-Type: {edit_type}")
        
        # Success-Message
        QMessageBox.information(
            self,
            "Erfolg",
            f"✅ Genereller Dialog erstellt!\n\n"
            f"Frame-GUID: {self.frame_guid}\n"
            f"View-GUID: {self.view_guid}\n"
            f"Dialog-GUID: {self.dialog_guid}\n"
            f"Edit-Type: {edit_type}\n\n"
            f"Der Dialog kann jetzt über das Menü aufgerufen werden."
        )
        
        # Wizard schließen (Widget aus Arbeitsbereich entfernen)
        parent_widget = self.parent()
        if parent_widget:
            parent_widget.deleteLater()
    
    def _create_record_pipeline(self, table_name, record_name, call_daten):
        """
        ZENTRALE PIPELINE zum Anlegen von Datensätzen mit Template 55555...
        
        Args:
            table_name: Tabellenname (z.B. 'sys_viewdaten', 'sys_framedaten')
            record_name: Name für DB-Spalte 'name'
            call_daten: Dictionary mit Properties für ROOT-Gruppe
        
        Pipeline:
        1. Template 55555... laden (ROOT_CONTROLS aus SYS_VIEWDATEN!)
        2. Neuen Datensatz anlegen mit GUID
        3. ROOT-Properties aus Template befüllen
        4. call_daten in ROOT setzen/überschreiben
        5. DB-Spalte 'name' setzen
        6. Speichern
        
        Returns:
            str: Neue GUID oder None bei Fehler
        """
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        logger.info(f"🔧 Pipeline: Erstelle {table_name} mit Name '{record_name}'")
        
        # 1. Template aus sys_viewdaten laden (NICHT aus table_name!)
        #    Alle Tabellen verwenden das gleiche Template aus sys_viewdaten
        template_guid = '55555555-5555-5555-5555-555555555555'
        template_db = PdvmCentralDatenbank('sys_viewdaten', template_guid)
        root_controls = template_db.get_value_by_group('ROOT_CONTROLS')
        
        if not root_controls:
            raise ValueError(f"Template {template_guid} hat keine ROOT_CONTROLS!")
        
        logger.info(f"  ✅ Template geladen: {len(root_controls)} ROOT_CONTROLS")
        
        # 2. Neue Instanz für Ziel-Tabelle (noch ohne GUID)
        from pdvm_datenbank import PdvmDatenbank
        db = PdvmDatenbank(table_name)
        
        # 3. Leeren Datensatz anlegen → GUID generieren
        new_guid = db.anlegen({})
        logger.info(f"  ✅ Datensatz angelegt: {new_guid}")
        
        # 4. PdvmCentralDatenbank-Instanz mit neuer GUID
        inst = PdvmCentralDatenbank(table_name, new_guid)
        
        # 5. Stichtag aus GCS
        stichtag = self.gcs.st_inst.PdvmDateTime
        
        # 6. ROOT-Properties aus Template befüllen
        for control_guid, control_def in root_controls.items():
            prop_name = control_def.get('name')
            if not prop_name:
                continue
            
            # Default-Wert aus Template
            default = control_def.get('default', '')
            inst.set_value('ROOT', prop_name, default, stichtag)
        
        logger.info(f"  ✅ {len(root_controls)} Properties aus Template befüllt")
        
        # 7. TABLE und SELF_GUID mit korrekten Werten überschreiben
        inst.set_value('ROOT', 'TABLE', table_name, stichtag)
        inst.set_value('ROOT', 'SELF_GUID', new_guid, stichtag)
        
        # 8. call_daten in ROOT setzen/überschreiben
        for prop_name, prop_value in call_daten.items():
            inst.set_value('ROOT', prop_name, prop_value, stichtag)
        
        logger.info(f"  ✅ {len(call_daten)} call_daten Properties gesetzt")
        
        # 9. DB-Spalte 'name' setzen (außerhalb JSON)
        #    Daten neu laden und mit name speichern
        conn = db.conn if hasattr(db, 'conn') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(db.db_name)
        
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET name = ? WHERE uid = ?", (record_name, new_guid))
        conn.commit()
        
        logger.info(f"  ✅ DB-Spalte 'name' gesetzt: '{record_name}'")
        
        # 10. JSON-Daten speichern
        inst.save_all_values()
        
        logger.info(f"✅ Pipeline abgeschlossen: {new_guid}")
        return new_guid
    
    def _create_view(self, name, table_name):
        """
        Erstellt neue View - PIPELINE mit call_daten
        
        Pipeline:
        1. Template 55555... aus sys_viewdaten laden (ROOT_CONTROLS)
        2. Neuen Datensatz anlegen mit GUID
        3. ROOT-Properties aus Template befüllen
        4. call_daten (name, table_name) in ROOT setzen
        5. Spalte 'name' in DB setzen
        6. Speichern
        """
        try:
            return self._create_record_pipeline(
                table_name='sys_viewdaten',
                record_name=name,
                call_daten={
                    'TABLE': table_name,
                    'NO_DATA': True
                }
            )
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der View: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _create_frame(self, name, view_guid, dialog_guid, edit_type):
        """
        Erstellt Frame - PIPELINE mit call_daten
        
        Pipeline:
        1. Template 55555... aus sys_framedaten laden (ROOT_CONTROLS)
        2. Neuen Datensatz anlegen mit GUID
        3. ROOT-Properties aus Template befüllen
        4. call_daten (view_guid, dialog_guid, edit_type) in ROOT setzen
        5. Spalte 'name' in DB setzen
        6. Speichern
        """
        try:
            return self._create_record_pipeline(
                table_name='sys_framedaten',
                record_name=name,
                call_daten={
                    'VIEW_GUID': view_guid,
                    'DIALOG_GUID': dialog_guid,
                    'HEADER_TEXT': name,
                    'EDIT_TYPE': edit_type
                }
            )
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Frames: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


def execute(params: dict, context: dict, gcs) -> bool:
    """
    Handler: Generellen Dialog erstellen
    
    Zeigt Wizard im Arbeitsbereich zum Erstellen neuer Frame/View/Dialog-Kombinationen.
    
    Args:
        params: Handler-Parameter (leer)
        context: Kontext mit main_app
        gcs: Globale Systemsteuerung
        
    Returns:
        bool: True bei Erfolg, False bei Abbruch
    """
    logger.info("🔧 === GENERELLEN DIALOG ERSTELLEN ===")
    
    try:
        # Main-App aus Context holen
        main_app = context.get('main_app')
        if not main_app:
            logger.error("❌ main_app nicht im Context gefunden!")
            return False
        
        # Workspace-Pipeline verwenden (Arbeitsbereich leeren)
        def _show_wizard():
            """Zeigt Wizard im Arbeitsbereich"""
            from PyQt5.QtWidgets import QWidget, QHBoxLayout
            
            # Container-Widget für Arbeitsbereich
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # Wizard erstellen (ohne Modal, ohne exec_())
            wizard = CreateGenerellerDialogWizard(gcs=gcs, parent=container)
            wizard.setWindowFlags(wizard.windowFlags() & ~Qt.Dialog)  # Kein Dialog-Flag
            
            # Wizard in Container einbetten
            container_layout.addWidget(wizard)
            container_layout.addStretch()  # Spacer für Rest
            
            # Arbeitsbereich leeren und Wizard anzeigen
            workspace_layout = main_app.workspace_layout  # Layout ist Member!
            
            # Alte Widgets entfernen
            while workspace_layout.count():
                item = workspace_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Neues Widget hinzufügen
            workspace_layout.addWidget(container)
            
            logger.info("✅ Wizard im Arbeitsbereich angezeigt")
            return True
        
        # Wizard anzeigen
        result = _show_wizard()
        
        if result:
            logger.info("✅ Wizard angezeigt")
            return True
        else:
            logger.error("❌ Fehler beim Anzeigen des Wizards")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des Dialogs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        if context.get('main_app'):
            QMessageBox.critical(
                context['main_app'],
                "Fehler",
                f"Fehler beim Erstellen des Dialogs:\n{str(e)}"
            )
        
        return False
