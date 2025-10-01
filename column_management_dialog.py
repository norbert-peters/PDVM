"""
MODAL-DIALOG: SPALTEN VERWALTEN
===============================

Blockierendes Fenster für Spalten-Management mit aktueller Sicht
"""

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QListWidgetItem, QCheckBox,
                             QDialogButtonBox, QFrame, QScrollArea, QWidget,
                             QMessageBox, QGroupBox, QGridLayout, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import logging
from global_gcs import gcs  # Globaler Zugriff auf GCS

logger = logging.getLogger(__name__)

class ColumnManagementDialog(QDialog):
    """
    Modal-Dialog für Spalten-Management.
    
    Öffnet mit aktueller Sicht (Standard/Expert), blockiert bis OK/Abbrechen.
    Benutzer kann Spalten ein-/ausblenden und Reihenfolge ändern.
    """
    
    # Signal wenn Spalten geändert wurden
    columns_changed = pyqtSignal(list)  # Neue Spalten-Liste
    
    def __init__(self, parent, view_guid, controls_config, current_mode="table"):
        """
        Args:
            parent: Parent-Widget
            view_guid: GUID der View für Controls
            controls_config: Dictionary mit Controls direkt vom Dialog
            current_mode: "table", "search" oder "management"
        """
        super().__init__(parent)
        
        self.view_guid = view_guid
        self.controls_config = controls_config  # Direkt vom Dialog erhalten
        self.current_mode = current_mode
        
        # Dialog-Ergebnis
        self.result_columns = None
        self.was_accepted = False
        
        self.setup_ui()
        self.load_current_columns()
        
        logger.info(f"🏗️ Spalten-Management Dialog geöffnet (Mode: {current_mode}, Expert: {gcs.expert_mode})")
    
    def setup_ui(self):
        """Erstelle die Dialog-UI"""
        # Dialog-Eigenschaften
        mode_name = self.current_mode.title()
        expert_label = "ExpertMode" if gcs.expert_mode else "StandardMode"
        self.setWindowTitle(f"Spalten verwalten - {mode_name} ({expert_label})")
        self.setModal(True)  # Blockierend!
        self.resize(500, 400)
        
        # Haupt-Layout
        layout = QVBoxLayout(self)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Spalten-Liste
        self.columns_widget = self.create_columns_widget()
        layout.addWidget(self.columns_widget)
        
        # Button-Bereich
        buttons = self.create_buttons()
        layout.addWidget(buttons)
        
    def create_header(self):
        """Erstelle Header-Bereich"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        
        # Titel
        title = QLabel("Spalten-Konfiguration")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Info
        mode_name = self.current_mode.title()
        expert_label = "ExpertMode" if gcs.expert_mode else "StandardMode"
        info = QLabel(f"📋 Bereich: {mode_name} | 🎯 Modus: {expert_label}")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info)
        
        return frame
    
    def create_columns_widget(self):
        """Erstelle sortierbare Spalten-Auswahl Widget"""
        group = QGroupBox("Verfügbare Spalten")
        layout = QVBoxLayout(group)
        
        # Info-Text
        info = QLabel("🔄 Drag & Drop um Reihenfolge zu ändern • ✅ Checkbox für Sichtbarkeit")
        info.setStyleSheet("color: #666; font-size: 11px; margin: 5px;")
        layout.addWidget(info)
        
        # Sortierbare Liste
        self.columns_list = QListWidget()
        self.columns_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.columns_list.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(self.columns_list)
        
        return group
    
    def create_buttons(self):
        """Erstelle Button-Bereich"""
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # OK Button
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("✅ Spalten übernehmen")
        ok_button.clicked.connect(self.accept_changes)
        
        # Cancel Button  
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        
        return button_box
    
    def load_current_columns(self):
        """Lade aktuelle Spalten-Konfiguration direkt aus GCS (NEUE EINFACHE ARCHITEKTUR)"""
        try:
            # GCS direkt verwenden für zentrale Daten
            if not gcs:
                QMessageBox.warning(self, "Fehler", "GCS nicht verfügbar")
                return
            
            # Controls direkt aus GCS-Datenbank holen
            all_controls, _ = gcs.db.get_value(self.view_guid, 'controls')
            if not all_controls:
                QMessageBox.warning(self, "Fehler", "Keine Controls-Konfiguration in GCS verfügbar")
                return
            
            # STATISCHE PROJEKTION für Column Management - je nach Expert Mode
            projection_key = 'change_expert' if gcs.expert_mode else 'change_standard'
            current_projection = gcs.get_projection_table(self.view_guid, projection_key)
            
            # SORTIERUNG: Spalten nach der korrekten Order sortieren (je nach Modus)
            order_field = 'expert_order' if gcs.expert_mode else 'display_order'
            
            # Erstelle sortierte Liste aus der Projektion
            sortable_columns = []
            for column_key in current_projection:
                config = all_controls.get(column_key, {})
                order_value = config.get(order_field, 999)
                sortable_columns.append((column_key, order_value, config))
            
            # Nach Order sortieren
            sortable_columns.sort(key=lambda x: x[1])  # Sortiere nach order_value
            
            logger.info(f"📋 Spalten sortiert nach {order_field}: {len(sortable_columns)} Spalten")
            
            # LINEARE IMPLEMENTATION: Zeige alle verfügbaren Spalten in korrekter Reihenfolge
            for column_key, order_value, config in sortable_columns:
                
                # Erstelle List-Item
                item = QListWidgetItem()
                
                # Custom Widget für Eigenschaften-Anzeige
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 2, 5, 2)
                
                # Spalten-Name
                name_label = QLabel(self._format_column_name(column_key))
                name_label.setMinimumWidth(200)
                layout.addWidget(name_label)
                
                # SHOW Eigenschaft (in beiden Modi verfügbar)
                show_checkbox = QCheckBox("Sichtbar")
                show_checkbox.setChecked(config.get('show', False))
                show_checkbox.setObjectName(f"show_{column_key}")
                layout.addWidget(show_checkbox)
                
                # EXPERT_MODE Eigenschaft (nur im Expert Mode verfügbar)
                if gcs.expert_mode:
                    expert_checkbox = QCheckBox("Nur Experten")
                    expert_checkbox.setChecked(config.get('expert_mode', False))
                    expert_checkbox.setObjectName(f"expert_{column_key}")
                    expert_checkbox.setStyleSheet("color: #0066cc;")
                    layout.addWidget(expert_checkbox)
                
                layout.addStretch()
                
                # Item konfigurieren
                item.setSizeHint(widget.sizeHint())
                item.setData(Qt.UserRole, column_key)  # Speichere Column-Key für Speicherung
                
                self.columns_list.addItem(item)
                self.columns_list.setItemWidget(item, widget)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Spalten: {e}")
            QMessageBox.warning(self, "Fehler", f"Spalten konnten nicht geladen werden:\n{e}")
    
    def _format_column_name(self, key):
        """Formatiere Control-Key zu lesbarem Namen"""
        # Entferne _show Suffix
        name = key.replace('_show', '')
        
        # Formatiere zu lesbarem Text
        name_map = {
            'uid': 'ID',
            'vorname': 'Vorname', 
            'familienname': 'Familienname',
            'geburtsdatum': 'Geburtsdatum',
            'geburtsdatum_alter': 'Alter',
            'geburtsdatum_jahr': 'Geburtsjahr',
            'geburtsdatum_monat': 'Geburtsmonat',
            'geburtsdatum_tag': 'Geburtstag',
            'anrede': 'Anrede',
            'email': 'E-Mail',
            'debug_info': 'Debug-Info'
        }
        
        return name_map.get(name, name.title())
    
    def accept_changes(self):
        """Benutzer hat OK geklickt - übernehme Änderungen der Properties UND der Sortierung"""
        try:
            # GCS direkt verwenden
            if not gcs:
                QMessageBox.warning(self, "Fehler", "GCS nicht verfügbar")
                return
                
            # Controls direkt aus GCS-Datenbank holen
            all_controls, _ = gcs.db.get_value(self.view_guid, 'controls')
            if not all_controls:
                QMessageBox.warning(self, "Fehler", "Keine Controls-Konfiguration verfügbar")
                return
            
            # 1. REIHENFOLGE ERFASSEN (Drag & Drop Änderungen)
            new_order = []
            for row in range(self.columns_list.count()):
                item = self.columns_list.item(row)
                column_key = item.data(Qt.UserRole)
                if column_key:
                    new_order.append(column_key)
            
            logger.info(f"📋 Neue Reihenfolge erfasst: {len(new_order)} Spalten")
            
            # 2. PROPERTIES ERFASSEN (Show/Expert_Mode Änderungen)
            changes_made = False
            
            for row in range(self.columns_list.count()):
                item = self.columns_list.item(row)
                widget = self.columns_list.itemWidget(item)
                column_key = item.data(Qt.UserRole)
                
                if column_key not in all_controls:
                    continue
                
                # Finde die Checkboxes im Widget
                show_checkbox = widget.findChild(QCheckBox, f"show_{column_key}")
                expert_checkbox = widget.findChild(QCheckBox, f"expert_{column_key}")
                
                # Show Property prüfen
                if show_checkbox:
                    new_show = show_checkbox.isChecked()
                    old_show = all_controls[column_key].get('show', False)
                    
                    if new_show != old_show:
                        all_controls[column_key]['show'] = new_show
                        changes_made = True
                        logger.debug(f"📝 {column_key}: show {old_show} → {new_show}")
                
                # Expert Mode Property prüfen (nur im Expert Mode verfügbar)
                if expert_checkbox and gcs.expert_mode:
                    new_expert = expert_checkbox.isChecked()
                    old_expert = all_controls[column_key].get('expert_mode', False)
                    
                    if new_expert != old_expert:
                        all_controls[column_key]['expert_mode'] = new_expert
                        changes_made = True
                        logger.debug(f"📝 {column_key}: expert_mode {old_expert} → {new_expert}")
            
            # 3. SORTIERUNGS-INDEX AKTUALISIEREN (modusspezifisch)
            # Standard Mode: display_order | Expert Mode: expert_order
            order_field = 'expert_order' if gcs.expert_mode else 'display_order'
            
            for index, column_key in enumerate(new_order):
                if column_key in all_controls:
                    old_order = all_controls[column_key].get(order_field, 999)
                    new_order_value = index
                    
                    if old_order != new_order_value:
                        all_controls[column_key][order_field] = new_order_value
                        changes_made = True
                        logger.debug(f"📋 {column_key}: {order_field} {old_order} → {new_order_value}")
            
            # 4. ÄNDERUNGEN SPEICHERN UND PROJEKTIONEN NEU AUFBAUEN
            if changes_made or len(new_order) > 0:  # Auch bei Sortierung ohne Property-Änderung
                # Aktualisierte Controls direkt speichern
                gcs.db.set_value(self.view_guid, 'controls', all_controls)
                logger.info(f"💾 Controls gespeichert für View {self.view_guid}")
                
                # Projektions-Tabellen neu aufbauen
                gcs.rebuild_projection_tables(self.view_guid)
                
                # Persistieren
                gcs.db.save_all_values()
                logger.info(f"✅ Spalten-Properties und Sortierung aktualisiert - Projektionen automatisch neu aufgebaut")
                
                # Signal senden für View-Update
                self.columns_changed.emit(new_order)  # Neue Sortierung senden
            else:
                logger.info("ℹ️ Keine Änderungen erkannt")
            
            # 5. DIALOG-ERGEBNIS SETZEN UND SCHLIEßEN
            self.result_columns = new_order
            self.was_accepted = True
            
            # Dialog schließen
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Spalten-Änderungen: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {e}")

    def closeEvent(self, event):
        """Dialog wird geschlossen"""
        if not self.was_accepted:
            logger.info("🚪 Spalten-Dialog abgebrochen")
        event.accept()
        
    def reject(self):
        """Dialog wurde abgebrochen"""
        self.was_accepted = False
        logger.info("❌ Spalten-Management abgebrochen")
        super().reject()

    def get_result(self):
        """Hole Dialog-Ergebnis"""
        return self.result_columns if self.was_accepted else None


def show_column_management_dialog(parent, view_guid, controls_config, current_mode="table"):
    """
    Zeige Modal-Dialog für Spalten-Management.
    
    Args:
        parent: Parent-Widget
        view_guid: GUID der View für Controls
        controls_config: Dictionary mit Controls direkt vom Dialog
        current_mode: "table", "search" oder "management"
        
    Returns:
        list: Neue Spalten-Liste oder None bei Abbruch
    """
    dialog = ColumnManagementDialog(parent, view_guid, controls_config, current_mode)
    
    # Modal ausführen (blockiert!)
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return dialog.get_result()
    else:
        logger.info("❌ Spalten-Management abgebrochen")
        return None


if __name__ == "__main__":
    # Test des Modal-Dialogs
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Test: Modal Spalten-Dialog")
            
            button = QPushButton("Spalten verwalten")
            button.clicked.connect(self.show_dialog)
            self.setCentralWidget(button)
        
        def show_dialog(self):
            # Mock Projection Manager
            class MockManager:
                def __init__(self):
                    self.controls = {
                        'uid_show': {'show': True, 'expert_mode': False},
                        'vorname_show': {'show': True, 'expert_mode': False},
                        'debug_info_show': {'show': False, 'expert_mode': True}
                    }
                    self.table_projection_standard = ['uid_show', 'vorname_show']
                    self.table_projection_expert = ['uid_show', 'vorname_show', 'debug_info_show']
                    
                    class MockGCS:
                        expert_mode = False
                    gcs = MockGCS()
                
                def _save_projections(self):
                    print("💾 Projektionen gespeichert (Mock)")
            
            manager = MockManager()
            result = show_column_management_dialog(self, manager, "table")
            
            if result:
                print(f"✅ Neue Spalten: {result}")
            else:
                print("❌ Abgebrochen")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())