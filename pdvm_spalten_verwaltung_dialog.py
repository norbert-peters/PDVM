#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPALTENVERWALTUNGS-DIALOG - PyQt5

Modaler Dialog für die Verwaltung von Tabellenspalten mit:
1. Modus-spezifische Spalten-Projektion
2. Show-Checkboxen 
3. Expert_mode-Checkboxen (nur im ExpertMode)
4. Reihenfolge-Verschiebung (expert_order/display_order)
5. Persistierung in GCS
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTableWidget, QTableWidgetItem, QCheckBox,
                            QHeaderView, QMessageBox, QSizePolicy, QAbstractItemView)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import logging
from global_gcs import gcs

logger = logging.getLogger(__name__)

class PdvmSpaltenVerwaltungsDialog(QDialog):
    """Modaler Dialog für Spaltenverwaltung"""
    
    def __init__(self, view_dialog, parent=None):
        """
        Initialisierung des Spaltenverwaltungs-Dialogs
        
        Args:
            view_dialog: Referenz auf den PdvmViewDialog
            parent: Parent-Fenster (optional)
        """
        super().__init__(parent)
        self.view_dialog = view_dialog
        self.gcs = gcs  # GCS als Instanzvariable setzen
        
        # Working-Copy der Controls für Bearbeitung
        self.working_controls = {}
        self.spalten_liste = []
        
        # UI-Komponenten
        self.table = None
        self.btn_up = None
        self.btn_down = None
        self.btn_ok = None
        self.btn_cancel = None
        
        self._setup_dialog()
        self._create_working_copy()
        self._create_gui()
        self._populate_table()
        
        logger.info("🔧 Spaltenverwaltungs-Dialog erstellt")
    
    def _setup_dialog(self):
        """Dialog-Eigenschaften konfigurieren"""
        self.setWindowTitle("Spaltenverwaltung")
        self.setModal(True)
        self.setFixedSize(800, 600)
        
        # Dialog zentrieren
        self._center_dialog()
    
    def _center_dialog(self):
        """Dialog auf dem Bildschirm zentrieren"""
        if self.parent():
            # Zentriere relativ zum Parent
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Zentriere auf dem Bildschirm
            screen = self.screen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def _create_working_copy(self):
        """Erstelle Working-Copy der Controls für Bearbeitung"""
        try:
            # Kopiere alle Controls aus view_dialog
            self.working_controls = {}
            for key, control in self.view_dialog.controls_config.items():
                self.working_controls[key] = control.copy()
            
            # Filtere Spalten basierend auf Modus
            self._filter_columns_by_mode()
            
            logger.info(f"✅ Working-Copy erstellt: {len(self.spalten_liste)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Working-Copy: {e}")
            raise
    
    def _filter_columns_by_mode(self):
        """Spalten basierend auf GCS-Projektions-Tabellen laden (EINZIGE QUELLE DER WAHRHEIT)"""
        try:
            # Spaltenverwaltung verwendet spezielle Projektionen für ALLE verfügbaren Spalten (LINEARES SYSTEM)
            if self.gcs.expert_mode:
                self.spalten_liste = self.gcs.get_projection_table(self.view_dialog.view_guid, 'change_expert')
                mode_info = "Change Expert (alle Spalten)"
            else:
                self.spalten_liste = self.gcs.get_projection_table(self.view_dialog.view_guid, 'change_standard')  
                mode_info = "Change Standard (non-expert Spalten)"
            
            # Sicherstellung dass spalten_liste eine Liste ist
            if not isinstance(self.spalten_liste, list):
                self.spalten_liste = []
                
            logger.info(f"✅ Spalten aus GCS-Projektion ({mode_info}): {len(self.spalten_liste)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der GCS-Projektion: {e}")
            # Fallback: Alle Controls verwenden
            self.spalten_liste = []
            for control_key, control in self.working_controls.items():
                if control_key != 'dummy':
                    if self.gcs.expert_mode or not control.get('expert_mode', False):
                        self.spalten_liste.append(control_key)
            logger.warning(f"⚠️ Fallback auf Controls: {len(self.spalten_liste)} Spalten")
    
    def _create_gui(self):
        """GUI-Elemente erstellen"""
        try:
            # Hauptlayout
            main_layout = QVBoxLayout(self)
            main_layout.setSpacing(15)
            main_layout.setContentsMargins(20, 20, 20, 20)
            
            # Titel
            mode_text = "Experten-Modus" if gcs.expert_mode else "Standard-Modus"
            title_label = QLabel(f"Spaltenverwaltung ({mode_text})")
            title_font = QFont("Arial", 14, QFont.Bold)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(title_label)
            
            # Tabellen-Container
            table_container = QHBoxLayout()
            
            # Tabelle
            self.table = QTableWidget()
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
            
            # Spalten konfigurieren
            if gcs.expert_mode:
                self.table.setColumnCount(4)  # Name, Show, Expert_mode, Control_type
                headers = ["Spaltenname", "Anzeigen", "Expert-Modus", "Typ"]
            else:
                self.table.setColumnCount(2)  # Name, Show
                headers = ["Spaltenname", "Anzeigen"]
            
            self.table.setHorizontalHeaderLabels(headers)
            
            # Header-Schrift
            header_font = QFont("Segoe UI", 10, QFont.Bold)
            self.table.horizontalHeader().setFont(header_font)
            
            # Spaltenbreiten
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # Name
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Show
            if self.gcs.expert_mode:
                header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Expert_mode
                header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Type
            
            table_container.addWidget(self.table)
            
            # Button-Panel für Reihenfolge
            button_panel = QVBoxLayout()
            button_panel.addStretch()
            
            self.btn_up = QPushButton("↑ Nach oben")
            self.btn_up.setFixedSize(120, 40)
            self.btn_up.clicked.connect(self._move_up)
            button_panel.addWidget(self.btn_up)
            
            self.btn_down = QPushButton("↓ Nach unten")
            self.btn_down.setFixedSize(120, 40)
            self.btn_down.clicked.connect(self._move_down)
            button_panel.addWidget(self.btn_down)
            
            button_panel.addStretch()
            
            table_container.addLayout(button_panel)
            main_layout.addLayout(table_container)
            
            # Dialog-Buttons
            dialog_buttons = QHBoxLayout()
            dialog_buttons.addStretch()
            
            self.btn_cancel = QPushButton("Abbrechen")
            self.btn_cancel.clicked.connect(self.reject)
            dialog_buttons.addWidget(self.btn_cancel)
            
            self.btn_ok = QPushButton("OK")
            self.btn_ok.clicked.connect(self._save_and_close)
            self.btn_ok.setDefault(True)
            dialog_buttons.addWidget(self.btn_ok)
            
            main_layout.addLayout(dialog_buttons)
            
            logger.info("✅ GUI-Elemente erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der GUI: {e}")
            raise
    
    def _populate_table(self):
        """Tabelle mit Spaltendaten füllen"""
        try:
            self.table.setRowCount(len(self.spalten_liste))
            
            for row_idx, control_key in enumerate(self.spalten_liste):
                control = self.working_controls.get(control_key, {})
                
                # Spaltenname
                name_item = QTableWidgetItem(control.get('name', control_key))
                name_item.setData(Qt.UserRole, control_key)  # Control-Key speichern
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Nicht editierbar
                self.table.setItem(row_idx, 0, name_item)
                
                # Show-Checkbox
                show_checkbox = QCheckBox()
                show_checkbox.setChecked(control.get('show', False))
                show_checkbox.stateChanged.connect(lambda state, key=control_key: self._on_show_changed(key, state))
                self.table.setCellWidget(row_idx, 1, show_checkbox)
                
                # Expert_mode-Checkbox (nur im ExpertMode)
                if self.gcs.expert_mode:
                    expert_checkbox = QCheckBox()
                    expert_checkbox.setChecked(control.get('expert_mode', False))
                    expert_checkbox.stateChanged.connect(lambda state, key=control_key: self._on_expert_mode_changed(key, state))
                    self.table.setCellWidget(row_idx, 2, expert_checkbox)
                    
                    # Control-Type
                    type_item = QTableWidgetItem(control.get('control_type', ''))
                    type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_idx, 3, type_item)
            
            logger.info(f"✅ Tabelle gefüllt: {len(self.spalten_liste)} Zeilen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Füllen der Tabelle: {e}")
            raise
    
    def _on_show_changed(self, control_key, state):
        """Show-Checkbox Änderung"""
        self.working_controls[control_key]['show'] = (state == Qt.Checked)
        logger.debug(f"Show geändert für {control_key}: {state == Qt.Checked}")
    
    def _on_expert_mode_changed(self, control_key, state):
        """Expert_mode-Checkbox Änderung"""
        self.working_controls[control_key]['expert_mode'] = (state == Qt.Checked)
        logger.debug(f"Expert_mode geändert für {control_key}: {state == Qt.Checked}")
    
    def _move_up(self):
        """Ausgewählte Zeile nach oben verschieben"""
        try:
            current_row = self.table.currentRow()
            if current_row > 0:
                # Vertausche in spalten_liste
                self.spalten_liste[current_row], self.spalten_liste[current_row - 1] = \
                    self.spalten_liste[current_row - 1], self.spalten_liste[current_row]
                
                # Tabelle neu füllen
                self._populate_table()
                
                # Selection beibehalten
                self.table.selectRow(current_row - 1)
                
                logger.debug(f"Zeile {current_row} nach oben verschoben")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Verschieben nach oben: {e}")
    
    def _move_down(self):
        """Ausgewählte Zeile nach unten verschieben"""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0 and current_row < len(self.spalten_liste) - 1:
                # Vertausche in spalten_liste
                self.spalten_liste[current_row], self.spalten_liste[current_row + 1] = \
                    self.spalten_liste[current_row + 1], self.spalten_liste[current_row]
                
                # Tabelle neu füllen
                self._populate_table()
                
                # Selection beibehalten
                self.table.selectRow(current_row + 1)
                
                logger.debug(f"Zeile {current_row} nach unten verschoben")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Verschieben nach unten: {e}")
    
    def _save_and_close(self):
        """Änderungen speichern und Dialog schließen"""
        try:
            # Order-Werte basierend auf neuer Reihenfolge setzen
            self._update_order_values()
            
            # Sortierung für NormalMode-Controls (vor GCS-Speicherung!)
            self._resort_display_order()
            
            # Änderungen in GCS übernehmen
            self.gcs._db.set_value(
                gruppe=self.view_dialog.view_guid,
                feld='controls',
                wert=self.working_controls
            )
            
            # Persistieren
            self.gcs._db.save_all_values()
            
            # Controls im view_dialog aktualisieren
            self.view_dialog.controls_config = self.working_controls.copy()
            
            # GCS-Projektions-Tabellen neu aufbauen für sofortige Aktualisierung
            self.gcs.rebuild_projection_tables(self.view_dialog.view_guid)
            
            # Sort-Projektionen werden automatisch durch GCS-Rebuild aktualisiert (LINEARES SYSTEM)
            logger.info("✅ Sort-Projektionen über lineares GCS-System automatisch aktualisiert")
            
            logger.info("✅ Spalteneinstellungen gespeichert und persistiert")
            
            # Dialog schließen mit OK
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")
    
    def _update_order_values(self):
        """Order-Werte basierend auf neuer Reihenfolge aktualisieren"""
        try:
            order_key = 'expert_order' if self.gcs.expert_mode else 'display_order'
            
            for index, control_key in enumerate(self.spalten_liste):
                if control_key in self.working_controls:
                    self.working_controls[control_key][order_key] = index + 1
                    logger.debug(f"{control_key}.{order_key} = {index + 1}")
            
            logger.info(f"✅ Order-Werte aktualisiert ({order_key})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Order-Werte: {e}")
            raise
    
    def _resort_display_order(self):
        """Neu-Sortierung der display_order für Controls mit expert_mode=false"""
        try:
            # Sammle alle Controls mit expert_mode=false und show=true
            show_controls = []
            for control_key, control in self.working_controls.items():
                if not control.get('expert_mode', False) and control.get('show', False):
                    show_controls.append(control_key)
            
            # Sortiere nach aktueller display_order
            show_controls.sort(key=lambda k: self.working_controls[k].get('display_order', 999))
            
            # Weise neue display_order Werte zu
            for index, control_key in enumerate(show_controls):
                self.working_controls[control_key]['display_order'] = index + 1
            
            logger.info(f"✅ Display_order neu sortiert für {len(show_controls)} aktive Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Display_order Neusortierung: {e}")

def show_spalten_verwaltung(view_dialog, parent=None):
    """
    Hilfsfunktion zum Anzeigen des Spaltenverwaltungs-Dialogs
    
    Args:
        view_dialog: Referenz auf PdvmViewDialog
        parent: Parent-Fenster (optional)
        
    Returns:
        True wenn OK gedrückt wurde, False bei Abbrechen
    """
    try:
        dialog = PdvmSpaltenVerwaltungsDialog(view_dialog, parent)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            logger.info("✅ Spaltenverwaltung mit OK geschlossen")
            return True
        else:
            logger.info("ℹ️ Spaltenverwaltung abgebrochen")
            return False
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen der Spaltenverwaltung: {e}")
        if parent:
            QMessageBox.critical(parent, "Fehler", f"Spaltenverwaltung konnte nicht geöffnet werden:\n{e}")
        return False

# Test-Funktion
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Logging konfigurieren
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("❌ Spaltenverwaltung benötigt einen aktiven ViewDialog - kann nicht standalone getestet werden")
    sys.exit(1)