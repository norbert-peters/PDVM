# pdvm_modern_view_widget.py
"""
Modernes View-Widget basierend auf viewdaten-Struktur
Ersetzt das alte PdvmDialogWidget mit erweiterten Funktionalitäten
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QLineEdit, QComboBox, QHeaderView, QPushButton, QLabel, QDateEdit,
    QFrame, QSplitter, QScrollArea, QMessageBox, QCheckBox, QSpinBox,
    QMenu, QAction, QWidgetAction, QListWidget, QListWidgetItem, QDialog
)

from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette
import json
from datetime import datetime, date

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_view_data_manager import PdvmViewDataManager


logger = logging.getLogger(__name__)

class ColumnSelectionDialog(QDialog):
    """
    Dialog für die Spaltenauswahl mit Checkboxen
    """
    
    def __init__(self, available_columns, selected_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spaltenauswahl")
        self.setModal(True)
        self.resize(400, 300)
        
        self.available_columns = available_columns  # Liste von {"name": str, "label": str}
        self.selected_columns = selected_columns.copy()  # Liste der ausgewählten Namen
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Überschrift
        title_label = QLabel("Wählen Sie die anzuzeigenden Spalten:")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Scroll-Bereich für Checkboxen
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.checkboxes = {}
        
        # Alle verfügbaren Spalten als Checkboxen
        for col_data in self.available_columns:
            name = col_data["name"]
            label = col_data["label"]
            
            checkbox = QCheckBox(label)
            checkbox.setChecked(name in self.selected_columns)
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            
            self.checkboxes[name] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Alle auswählen / Alle abwählen
        select_all_btn = QPushButton("Alle auswählen")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Alle abwählen") 
        deselect_all_btn.clicked.connect(self._deselect_all)
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        
        # OK / Abbrechen
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_checkbox_changed(self):
        """Aktualisiert die Liste der ausgewählten Spalten"""
        self.selected_columns = []
        for name, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                self.selected_columns.append(name)
    
    def _select_all(self):
        """Wählt alle Spalten aus"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def _deselect_all(self):
        """Wählt alle Spalten ab"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_columns(self):
        """Gibt die Liste der ausgewählten Spaltennamen zurück"""
        return self.selected_columns

class PdvmModernViewWidget(QWidget):
    """
    Modernes View-Widget mit Search, Sort und Filter-Funktionalitäten
    Basiert auf der viewdaten-Struktur für maximale Flexibilität
    """
    
    # Signals
    rowSelected = pyqtSignal(dict)  # Emitted when a row is selected
    dataChanged = pyqtSignal()     # Emitted when data changes
    
    def __init__(self, view_guid, user_guid=None, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.user_guid = user_guid
        self.stichtag = None  # Wird beim Laden gesetzt
        # WICHTIG: Manager-Pattern - UI verwendet nur den Data-Manager
        self.data_manager = None
        self.table_data = []  # Initialisiere table_data, um Attributfehler zu vermeiden
        self.filtered_data = []
        self.current_sort_column = None
        self.current_sort_order = Qt.AscendingOrder
        self.expert_mode = False
        self.visible_column_names = []
        self._custom_column_selection = None  # Für benutzerdefinierte Spaltenauswahl
        # Search delay timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._apply_filters)
        # UI Setup Timer (für korrekte Spaltenbreiten)
        self.setup_timer = QTimer()
        self.setup_timer.setSingleShot(True)
        self.setup_timer.timeout.connect(self._finalize_setup)
        self.dummy_mode = False  # Flag: Dummy-Modus (keine echten Spalten)
        logger.debug(f"[ModernViewWidget] __init__ called: view_guid={view_guid}, user_guid={user_guid}")
        # Initialisierung mit Manager-Pattern
        self._initialize_data_manager()
        logger.debug("[ModernViewWidget] Data-Manager initialisiert")
        # Gespeicherte Einstellungen laden BEVOR UI aufgebaut wird
        self._load_view_settings() 
        self._setup_ui()
        logger.debug("[ModernViewWidget] UI setup abgeschlossen")
        # Keine weiteren Methodenaufrufe, nur Minimal-Tabelle
    
    def _initialize_data_manager(self):
        """Initialisiert den Data-Manager für saubere Trennung von UI und Datenlogik."""
        try:
            self.data_manager = PdvmViewDataManager(
                view_guid=self.view_guid,
                user_guid=self.user_guid
            )
            # view_fields aus Manager extrahieren
            self.view_fields = self.data_manager.fields_config
            # Stichtag aus Manager übernehmen, falls vorhanden
            if hasattr(self.data_manager, 'stichtag'):
                self.stichtag = self.data_manager.stichtag
            logger.info(f"✅ Data-Manager initialisiert: {self.data_manager.get_table_info()}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren des Data-Managers: {e}")
            raise
    def _load_data_from_manager(self):
        """Lädt Daten über den Data-Manager (Manager-Pattern)."""
        try:
            # Daten vom Manager holen (bereits verarbeitet und mit Lookups)
            self.table_data = self.data_manager.get_data()
            
            # Initial alle Daten anzeigen
            self.filtered_data = self.table_data.copy()
            
            # Tabelle aufbauen
            self._setup_table_columns()
            self._populate_table()
            
            logger.info(f"📊 Daten vom Manager geladen: {len(self.table_data)} Datensätze")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten über Manager: {e}")

    def _get_dropdown_options(self, field_config):
        """Holt Dropdown-Optionen über den Data-Manager."""
        if not self.data_manager:
            return {}
        
        field_name = field_config["feld"]
        return self.data_manager.get_dropdown_options(field_name)
    
    def _setup_ui(self):
        from PyQt5.QtWidgets import QLabel, QTableWidget, QTableWidgetItem
        logger.debug("[ModernViewWidget] _setup_ui aufgerufen")
        """Erstellt die UI mit Expert-Mode-Button, Spaltenauswahl und Tabelle."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        # Überschrift und Stichtag-Bereich
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        # Überschrift
        title_label = QLabel("Datenansicht (Modernes View-Widget)")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 2px;")
        header_layout.addWidget(title_label)
        # Stichtag anzeigen (immer im PdvmFormat, wie in get_value verwendet)
        stichtag_label = QLabel(f"Stichtag (PdvmFormat): {self.stichtag if self.stichtag is not None else '-'}")
        stichtag_label.setStyleSheet("font-size: 14px; color: #555; margin-bottom: 8px;")
        header_layout.addWidget(stichtag_label)
        # Expert-Mode Button und Spaltenauswahl
        controls_row = QHBoxLayout()
        
        # Expert-Mode Button mit verbessertem Styling
        self.expert_button = QPushButton("🔬 Expert-Mode: AUS")
        self.expert_button.setCheckable(True)
        self.expert_button.setChecked(False)
        self.expert_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #333;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #0056b3;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:checked:hover {
                background-color: #0056b3;
                border-color: #004085;
            }
        """)
        self.expert_button.clicked.connect(self._toggle_expert_mode)
        controls_row.addWidget(self.expert_button)
        
        # Reset Einstellungen Button mit verbessertem Styling
        self.reset_button = QPushButton("🔄 Reset Einstellungen")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #6c757d;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: normal;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
                border-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #c82333;
                border-color: #bd2130;
            }
        """)
        self.reset_button.clicked.connect(self._reset_view_settings)
        controls_row.addWidget(self.reset_button)
        
        # Button für Spaltenauswahl mit Dialog
        self.column_selection_button = QPushButton("Spalten auswählen...")
        self.column_selection_button.setMinimumWidth(200)
        self.column_selection_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #333;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 16px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        self.column_selection_button.clicked.connect(self._open_column_selection_dialog)
        controls_row.addWidget(QLabel("Spalten anzeigen:"))
        controls_row.addWidget(self.column_selection_button)
        controls_row.addStretch(1)
        header_layout.addLayout(controls_row)
        layout.addWidget(header_widget)
        # Tabelle
        try:
            self._update_visible_columns()
            self._create_table_with_visible_columns(layout)
        except Exception as e:
            logger.error(f"❌ Fehler beim Aufbau der UI in _setup_ui: {e}")
            error_label = QLabel(f"❌ Fehler beim Aufbau der Tabelle:\n{str(e)}")
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)

    def _toggle_expert_mode(self):
        self.expert_mode = not self.expert_mode
        self.expert_button.setText("🔬 Expert-Mode: AN" if self.expert_mode else "🔬 Expert-Mode: AUS")
        self.expert_button.setChecked(self.expert_mode)  # Button-Status aktualisieren
        self._update_visible_columns()
        self._rebuild_table()
        # Einstellungen speichern
        self._save_view_settings()

    def _load_view_settings(self):
        """Lädt die gespeicherten View-Einstellungen aus der systemsteuerung-Tabelle."""
        if not self.user_guid or not self.view_guid:
            logger.debug("🔧 Keine user_guid oder view_guid - verwende Standard-Einstellungen")
            return
        
        try:
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Benutzerdaten laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            
            # ViewSettings-Struktur
            view_settings = user_data.get("ViewSettings", {})
            current_view_settings = view_settings.get(self.view_guid, {})
            
            # Expert-Mode laden
            saved_expert_mode = current_view_settings.get("expert_mode", False)
            if saved_expert_mode != self.expert_mode:
                self.expert_mode = saved_expert_mode
                self.expert_button.setChecked(saved_expert_mode)
                self.expert_button.setText("🔬 Expert-Mode: AN" if saved_expert_mode else "🔬 Expert-Mode: AUS")
                logger.info(f"📋 Expert-Mode aus Einstellungen geladen: {saved_expert_mode}")
            
            # Spaltenauswahl laden
            saved_column_selection = current_view_settings.get("custom_columns", None)
            if saved_column_selection:
                self._custom_column_selection = saved_column_selection
                logger.info(f"📋 Spaltenauswahl aus Einstellungen geladen: {len(saved_column_selection)} Spalten")
            
            # Weitere Einstellungen können hier geladen werden:
            # - column_widths = current_view_settings.get("column_widths", {})
            
            logger.info(f"✅ View-Einstellungen für {self.view_guid} geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Einstellungen: {e}")

    def _save_view_settings(self):
        """Speichert die aktuellen View-Einstellungen in der systemsteuerung-Tabelle."""
        if not self.user_guid or not self.view_guid:
            logger.debug("🔧 Keine user_guid oder view_guid - Speichern übersprungen")
            return
        
        try:
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Aktuelle Benutzerdaten laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            
            # ViewSettings-Struktur initialisieren falls nicht vorhanden
            if "ViewSettings" not in user_data:
                user_data["ViewSettings"] = {}
            
            # Aktuelle View-Einstellungen zusammenstellen
            current_settings = {
                "expert_mode": self.expert_mode,
                "custom_columns": getattr(self, '_custom_column_selection', []),
                "last_updated": datetime.now().isoformat(),
                # Platz für zukünftige Erweiterungen:
                # "column_widths": self.get_column_widths(),
                # "sort_column": self.current_sort_column,
                # "sort_order": self.current_sort_order
            }
            
            # Einstellungen für diese View speichern
            user_data["ViewSettings"][self.view_guid] = current_settings
            
            # Zurück in Datenbank speichern
            raw_data[self.user_guid] = user_data
            sys_db.speichern(self.user_guid, raw_data)
            
            logger.debug(f"💾 View-Einstellungen für {self.view_guid} gespeichert: expert_mode={self.expert_mode}, custom_columns={len(getattr(self, '_custom_column_selection', []))}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der View-Einstellungen: {e}")

    def _reset_view_settings(self):
        """Setzt alle View-Einstellungen auf Standard zurück und löscht gespeicherte Werte."""
        try:
            # Standard-Werte setzen
            self.expert_mode = False
            self.expert_button.setChecked(False)
            self.expert_button.setText("🔬 Expert-Mode: AUS")
            
            # Spaltenauswahl zurücksetzen
            self._custom_column_selection = None
            
            # Gespeicherte Einstellungen löschen
            if self.user_guid and self.view_guid:
                sys_db = PdvmCentralDatenbank(
                    db_name="PdvmManager.db",
                    table_name="systemsteuerung",
                    guid=self.user_guid
                )
                
                raw_data = sys_db.lesen() or {}
                user_data = raw_data.get(self.user_guid, {})
                
                # ViewSettings für diese View löschen
                if "ViewSettings" in user_data and self.view_guid in user_data["ViewSettings"]:
                    del user_data["ViewSettings"][self.view_guid]
                    raw_data[self.user_guid] = user_data
                    sys_db.speichern(self.user_guid, raw_data)
                    logger.info(f"🗑️ Gespeicherte Einstellungen für View {self.view_guid} gelöscht")
            
            # UI aktualisieren
            self._update_visible_columns()
            self._rebuild_table()
            
            logger.info("🔄 View-Einstellungen auf Standard zurückgesetzt")
            
            # Erfolgs-Meldung anzeigen
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Einstellungen zurückgesetzt", 
                f"Die View-Einstellungen wurden auf Standard zurückgesetzt.\n\n• Expert-Mode: AUS\n• Spaltenauswahl: Standard\n\nZukünftige Erweiterungen:\n• Spaltenbreiten: Standard\n• Sortierung: Standard"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der View-Einstellungen: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Fehler", f"Fehler beim Zurücksetzen:\n{str(e)}")

    def _update_visible_columns(self):
        """Setzt self.visible_column_names und aktualisiert das Dropdown."""
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            self.visible_column_names = []
            self.column_dropdown.clear()
            logger.debug("[ModernViewWidget] Keine Controlstruktur oder keine columns vorhanden!")
            return
        columns = control.columns
        logger.debug(f"[ModernViewWidget] Alle Spalten (columns): {columns}")
        
        # Filter nach show/expert - KORRIGIERTE LOGIK FÜR EXPERT-SPALTEN
        filtered = []
        for col in columns:
            # Robust: show/expert direkt als Key, mit Fallback
            show_val = col['show'] if 'show' in col else False
            expert_val = col['expert'] if 'expert' in col else False
            
            if not ('show' in col and 'expert' in col):
                logger.error(f"[ModernViewWidget] Spalte '{col}': show/expert fehlt! Typ: {type(col)} Inhalt: {col}")
                
            logger.debug(f"[ModernViewWidget] Spalte '{col.get('name', str(col))}', show={show_val}, expert={expert_val}")
            
            # KORRIGIERTE FILTER-LOGIK FÜR EXPERT-SPALTEN:
            if self.expert_mode:
                # Expert-Mode: Zeige show=True Spalten UND expert=True Spalten
                # Expert-Spalten werden temporär als "show" behandelt
                if show_val or expert_val:
                    filtered.append(col)
                    if expert_val and not show_val:
                        logger.debug(f"[ModernViewWidget] Expert-Spalte '{col.get('name')}' wird im Expert-Mode angezeigt (show=False aber expert=True)")
            else:
                # Normal-Mode: Zeige nur Spalten mit show=True UND expert=False
                if show_val and not expert_val:
                    filtered.append(col)
        
        if self.expert_mode:
            logger.debug(f"[ModernViewWidget] Expert-Mode aktiv: Zeige alle show=True Spalten")
        else:
            logger.debug(f"[ModernViewWidget] Normal-Mode: Zeige nur show=True AND expert=False Spalten")
            
        logger.debug(f"[ModernViewWidget] Nach Filter: {[col.get('name', str(col)) for col in filtered]}")
        
        self.visible_column_names = [col['name'] for col in filtered]
        logger.debug(f"[ModernViewWidget] Sichtbare Spaltennamen: {self.visible_column_names}")
        
        # Button-Text für Spaltenauswahl aktualisieren
        self._update_column_selection_button(filtered)

    def _update_column_selection_button(self, available_columns):
        """Aktualisiert den Button-Text für die Spaltenauswahl"""
        current_selection = getattr(self, '_custom_column_selection', None)
        if current_selection is None:
            # Standard: Alle verfügbaren Spalten auswählen
            current_selection = [col['name'] for col in available_columns]
            self._custom_column_selection = current_selection
        
        # Button-Text aktualisieren - KORRIGIERT: Verwende 'label' statt 'anzeige'
        if not current_selection:
            button_text = "Keine Spalten ausgewählt"
        elif len(current_selection) == len(available_columns):
            button_text = "Alle Spalten ausgewählt"
        elif len(current_selection) == 1:
            # Eine Spalte: Zeige Label (korrigiert)
            for col in available_columns:
                if col['name'] == current_selection[0]:
                    # Verwende 'label' statt 'anzeige' und fallback zu 'name'
                    button_text = col.get('label', col.get('anzeige', col['name']))
                    break
            else:
                button_text = current_selection[0]
        else:
            button_text = f"{len(current_selection)} von {len(available_columns)} Spalten"
        
        self.column_selection_button.setText(button_text)
        
        # Sichtbare Spalten basierend auf aktueller Auswahl aktualisieren
        self.visible_column_names = [name for name in current_selection if name in [col['name'] for col in available_columns]]

    def _open_column_selection_dialog(self):
        """Öffnet den Dialog zur Spaltenauswahl"""
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            QMessageBox.warning(self, "Fehler", "Keine Spalten verfügbar")
            return
        
        columns = control.columns
        
        # Verfügbare Spalten für Dialog sammeln - KORRIGIERTE LOGIK FÜR EXPERT-SPALTEN
        available_columns = []
        for col in columns:
            show_val = col.get('show', False)
            expert_val = col.get('expert', False)
            
            # KORRIGIERTE FILTER-LOGIK FÜR EXPERT-SPALTEN:
            if self.expert_mode:
                # Expert-Mode: Zeige show=True Spalten UND expert=True Spalten
                # Expert-Spalten werden temporär als verfügbar behandelt
                if show_val or expert_val:
                    available_columns.append(col)
            else:
                # Normal-Mode: Zeige nur Spalten mit show=True UND expert=False
                if show_val and not expert_val:
                    available_columns.append(col)
        
        # Dialog-Format erstellen - KORRIGIERT: Verwende 'label' statt 'anzeige'
        dialog_columns = []
        for col in available_columns:
            dialog_columns.append({
                "name": col['name'],
                "label": col.get('label', col.get('anzeige', col['name']))
            })
        
        # Aktuelle Auswahl
        current_selection = getattr(self, '_custom_column_selection', [col['name'] for col in available_columns])
        
        # Dialog öffnen
        dialog = ColumnSelectionDialog(dialog_columns, current_selection, self)
        if dialog.exec_() == QDialog.Accepted:
            # Neue Auswahl übernehmen
            new_selection = dialog.get_selected_columns()
            self._custom_column_selection = new_selection
            self.visible_column_names = new_selection
            
            # Button-Text und Tabelle aktualisieren
            self._update_column_selection_button(available_columns)
            self._rebuild_table()
            
            # Einstellungen speichern
            self._save_view_settings()
            
            logger.info(f"📋 Spaltenauswahl geändert: {len(new_selection)} Spalten ausgewählt")

    def _on_column_selection_changed(self, selected_names):
        """Callback wenn sich die Spaltenauswahl ändert - Kompatibilität"""
        logger.debug(f"[ModernViewWidget] Spaltenauswahl geändert: {selected_names}")
        
        # Auswahl speichern
        self._custom_column_selection = selected_names
        
        # Sichtbare Spalten aktualisieren
        self.visible_column_names = selected_names
        
        # Tabelle neu aufbauen
        self._rebuild_table()
        
        # Einstellungen speichern
        self._save_view_settings()

    def _on_column_dropdown_changed(self, idx):
        # Veraltet - nicht mehr verwendet
        pass

    def _rebuild_table(self):
        # Tabelle neu aufbauen mit aktuellen sichtbaren Spalten
        layout = self.layout()
        if hasattr(self, 'table') and self.table:
            layout.removeWidget(self.table)
            self.table.deleteLater()
            self.table = None
        self._create_table_with_visible_columns(layout)

    def _create_table_with_visible_columns(self, layout):
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QLabel
        from PyQt5.QtWidgets import QAbstractItemView
        from PyQt5.QtCore import Qt
        logger.debug(f"[ModernViewWidget] _create_table_with_visible_columns: visible_column_names={self.visible_column_names}")
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            logger.error("❌ Keine Controlstruktur für die Spaltenanzeige gefunden!")
            control_columns = []
        else:
            control_columns = [col for col in control.columns if col['name'] in self.visible_column_names]

        data = self.data_manager.get_data() if self.data_manager else []
        # Dummy-Spalte erzeugen, wenn keine echten Spalten sichtbar sind
        if len(control_columns) == 0:
            self.dummy_mode = True
            logger.info("[ModernViewWidget] Keine sichtbaren Spalten. Zeige Dummy-Spalte 'keine Spalte'.")
            self.table = QTableWidget()
            self.table.setColumnCount(1)
            self.table.setRowCount(len(data) if data else 1)
            self.table.setHorizontalHeaderLabels(["keine Spalte"])
            # Dummy-Zeile füllen
            self.table.setItem(0, 0, QTableWidgetItem("Keine Daten"))
            layout.addWidget(self.table)
            return
        else:
            self.dummy_mode = False

        # Normale Tabelle mit echten Spalten und zweizeiliger Überschrift
        self.table = QTableWidget()
        self.table.setColumnCount(len(control_columns))
        self.table.setRowCount(len(data))


        # Setze Headerlabels je nach Expert-Mode
        if getattr(self, 'expert_mode', False):
            header_labels = [
                f"{str(col.get('anzeige', col.get('name', '')))}\n{str(col.get('name', ''))}"
                for col in control_columns
            ]
        else:
            header_labels = [str(col.get('anzeige', col.get('name', ''))) for col in control_columns]
        self.table.setHorizontalHeaderLabels(header_labels)
        # Header-Design: fett, 1 Punkt größer, linksbündig
        header = self.table.horizontalHeader()
        font = header.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        header.setFont(font)
        # Alle Header explizit linksbündig ausrichten
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, header.Interactive)
            self.table.model().setHeaderData(i, Qt.Horizontal, Qt.AlignLeft | Qt.AlignVCenter, Qt.TextAlignmentRole)
        # Wordwrap für Header aktivieren
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(40)
        self.table.horizontalHeader().setHighlightSections(False)
        # setWordWrap gibt es in PyQt5 nicht, Zeilenumbruch funktioniert trotzdem mit \n

        # Daten stumpf eintragen
        for row_idx, record in enumerate(data):
            if not isinstance(record, dict):
                continue
            for col_idx, col in enumerate(control_columns):
                key = col.get('name')
                value = record.get(key, "")
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        logger.debug(f"[ModernViewWidget] Tabelle erstellt: rows={len(data)}, cols={len(control_columns)}")
        layout.addWidget(self.table)

    def _toggle_expert_mode(self):
        self.expert_mode = not self.expert_mode
        self.expert_button.setText("🔬 Expert-Mode: AN" if self.expert_mode else "🔬 Expert-Mode: AUS")
        self._update_visible_columns()
        self._rebuild_table()
        # Zeige oder verstecke die zweite Kopfzeile
        if hasattr(self, 'header_label_row'):
            self.header_label_row.setVisible(self.expert_mode)

    def create_simple_table(self, layout):
        """Minimalistische Tabelle: Zeigt alle Spalten aus der Controlstruktur, stumpf, ohne Filter, ohne Mapping."""
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            logger.error("❌ Keine Controlstruktur für die Spaltenanzeige gefunden!")
            control_columns = []
        else:
            control_columns = control.columns

        data = self.data_manager.get_data() if self.data_manager else []
        self.table = QTableWidget()
        self.table.setColumnCount(len(control_columns))
        self.table.setRowCount(len(data))

        # Spaltennamen (interner Name)
        header_labels = []
        for col in control_columns:
            if isinstance(col, dict):
                header_labels.append(str(col.get('name', '')))
            else:
                header_labels.append(str(col))
        self.table.setHorizontalHeaderLabels(header_labels)

        # Daten stumpf eintragen
        for row_idx, record in enumerate(data):
            if not isinstance(record, dict):
                continue
            for col_idx, col in enumerate(control_columns):
                key = col.get('name') if isinstance(col, dict) else str(col)
                value = record.get(key, "")
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        layout.addWidget(self.table)
    def _create_table_minimal(self, layout):
        """Erstellt die Haupttabelle exakt nach Controlstruktur, zeigt IMMER alle Spalten aus der Controlstruktur, unabhängig von Daten."""
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        # Controlstruktur holen (Pflicht!)
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            logger.error("❌ Keine Controlstruktur für die Spaltenanzeige gefunden!")
            control_columns = []
        else:
            control_columns = control.columns

        # Daten holen (kann leer sein)
        data = self.data_manager.get_data()

        self.table.setColumnCount(len(control_columns))
        self.table.setRowCount(len(data) if data else 0)

        # Zweizeilige Überschrift: 1. Zeile interner Name, 2. Zeile Anzeigename (aus Controlstruktur)
        column_labels = self.data_manager.get_column_labels() if hasattr(self.data_manager, 'get_column_labels') else {}
        header_labels = []
        for idx, col in enumerate(control_columns):
            if not isinstance(col, dict):
                logger.warning(f"⚠️ Spalten-Definition an Position {idx} ist kein dict: {col}")
                internal = str(col)
                display = str(col)
            else:
                internal = col.get('name')
                display = column_labels.get(internal, internal)
            header_labels.append(f"{internal}\n{display}")
        self.table.setHorizontalHeaderLabels(header_labels)

        # Daten einfügen (immer alle Spalten, auch wenn leer)
        for row_idx, record in enumerate(data):
            if not isinstance(record, dict):
                logger.error(f"❌ Ungültiger Datensatz (kein dict) in Zeile {row_idx}: {record}")
                continue
            for col_idx, col in enumerate(control_columns):
                if not isinstance(col, dict):
                    logger.warning(f"⚠️ Spalten-Definition an Position {col_idx} ist kein dict: {col}")
                    key = str(col)
                else:
                    key = col.get('name')
                value = record.get(key, "")
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_idx, col_idx, item)

        layout.addWidget(self.table)
        
    def create_simple_table(self, layout):
        """Minimalistische Tabelle: Zeigt alle Spalten aus der Controlstruktur, stumpf, ohne Filter, ohne Mapping."""
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            logger.error("❌ Keine Controlstruktur für die Spaltenanzeige gefunden!")
            control_columns = []
        else:
            control_columns = control.columns

        data = self.data_manager.get_data() if self.data_manager else []
        self.table = QTableWidget()
        self.table.setColumnCount(len(control_columns))
        self.table.setRowCount(len(data))

        # Spaltennamen (interner Name)
        header_labels = []
        for col in control_columns:
            if isinstance(col, dict):
                header_labels.append(str(col.get('name', '')))
            else:
                header_labels.append(str(col))
        self.table.setHorizontalHeaderLabels(header_labels)

        # Daten stumpf eintragen
        for row_idx, record in enumerate(data):
            if not isinstance(record, dict):
                continue
            for col_idx, col in enumerate(control_columns):
                key = col.get('name') if isinstance(col, dict) else str(col)
                value = record.get(key, "")
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

            layout.addWidget(self.table)
    
    def _create_search_widget(self, field_config):
        """Erstellt das passende Search-Widget für einen Feld-Typ"""
        field_type = field_config["type"]
        ui_config = field_config.get("ui", {})
        filter_type = ui_config.get("filterType", "contains")
        field_name = field_config["feld"]  # KORREKTUR: Verwende "feld" für interne Referenz
        
        # WICHTIG: Search-Felder sind IMMER Text-basiert für maximale Flexibilität
        # Keine DatePicker oder andere spezielle Widgets in Search-Feldern!
        
        if field_type == "dropdown" or filter_type == "dropdown":
            # Multi-Select Dropdown-Filter für Dropdown-Felder
            field_display = field_config.get("name", field_name)
            widget = QPushButton()
            widget.setText(f"🔽 {field_display} (Alle)")
            widget.setStyleSheet("QPushButton { text-align: left; padding: 5px; }")
            
            # WICHTIG: Button als benanntes Attribut speichern für _clear_filters
            button_name = f'dropdown_btn_{field_name}'
            setattr(self, button_name, widget)
            
            # Filter-Menu erstellen
            menu = QMenu()
            widget.setMenu(menu)
            
            # Filter-Status für dieses Feld speichern
            if not hasattr(self, '_dropdown_filters'):
                self._dropdown_filters = {}
            self._dropdown_filters[field_name] = {"selected_keys": set(), "show_empty": True}
            
            # Menu-Aktionen hinzufügen
            self._setup_dropdown_filter_menu(menu, field_config, field_name)
            
            return widget
            
        elif field_type == "date":
            # KORREKTUR: Auch Datums-Felder bekommen Text-Search
            # Benutzer können "2024", "01.01.2024", "Januar" etc. eingeben
            widget = QLineEdit()
            widget.setPlaceholderText(f"Datum suchen (z.B. 2024, Jan, 01.01)...")
            widget.textChanged.connect(self._on_search_changed)
            return widget
            
        elif field_type in ["int", "float"] or filter_type == "numeric":
            # Numeric-Filter als Text (z.B. ">100", "50-100")
            widget = QLineEdit()
            widget.setPlaceholderText(f"Zahl suchen (z.B. 100, >50, 10-20)...")
            widget.textChanged.connect(self._on_search_changed)
            return widget
            
        else:
            # Standard Text-Search
            widget = QLineEdit()
            widget.setPlaceholderText(f"Suche in {field_name}...")
            widget.textChanged.connect(self._on_search_changed)
            return widget
    
    def _get_dropdown_options_direct(self, field_config):
        """
        Holt alle verfügbaren Optionen für ein Dropdown-Feld direkt aus der DB.
        
        Args:
            field_config: Feld-Konfiguration mit Dropdown-Informationen
            
        Returns:
            dict: {key: display_value} Mapping aller verfügbaren Optionen
        """
        options = {}
        
        try:
            dropdown_config = field_config.get("lookup")
            if not dropdown_config:
                return options
            
            dropdown_table = dropdown_config["table"]
            dropdown_key = dropdown_config["key"] 
            dropdown_group = dropdown_config["value"]
            
            # Dropdown-Daten laden
            
            dropdown_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=dropdown_table,
                guid=dropdown_key
            )
            
            dropdown_data = dropdown_db.lesen()
            
            if dropdown_data and "ROOT" in dropdown_data:
                group_data = dropdown_data["ROOT"].get(dropdown_group, {})
                values = group_data.get("werte", [])
                
                for entry in values:
                    key = entry.get("key", "")
                    display = entry.get("de", entry.get("en", key))
                    options[key] = display
                
                logger.debug(f"🔍 Dropdown-Optionen für {field_config['feld']}: {len(options)} Einträge")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Dropdown-Optionen: {e}")
        
        return options
    
    def _setup_dropdown_filter_menu(self, menu, field_config, field_name):
        """
        Erstellt das Multi-Select Filter-Menu für Dropdown-Felder.
        
        Args:
            menu: QMenu-Instanz
            field_config: Feld-Konfiguration
            field_name: Name des Feldes
        """
        try:
            # Dropdown-Optionen laden
            dropdown_options = self._get_dropdown_options(field_config)
            
            # Header-Bereich für Massenaktionen
            header_widget = QWidget()
            header_layout = QVBoxLayout(header_widget)
            header_layout.setContentsMargins(5, 5, 5, 5)
            
            # "Alle auswählen/abwählen" Buttons
            button_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("Alle")
            select_all_btn.setMaximumWidth(60)
            select_all_btn.clicked.connect(lambda: self._toggle_all_dropdown_options(field_name, True, menu))
            button_layout.addWidget(select_all_btn)
            
            select_none_btn = QPushButton("Keine")
            select_none_btn.setMaximumWidth(60)
            select_none_btn.clicked.connect(lambda: self._toggle_all_dropdown_options(field_name, False, menu))
            button_layout.addWidget(select_none_btn)
            
            button_layout.addStretch()
            
            # Reset-Button
            reset_btn = QPushButton("Reset")
            reset_btn.setMaximumWidth(60)
            reset_btn.clicked.connect(lambda: self._reset_dropdown_filter(field_name, menu))
            button_layout.addWidget(reset_btn)
            
            header_layout.addLayout(button_layout)
            
            # Anwenden-Button (prominent)
            apply_btn = QPushButton("📋 Filter anwenden")
            apply_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            apply_btn.clicked.connect(lambda: self._apply_dropdown_filter_and_close(field_name, menu))
            header_layout.addWidget(apply_btn)
            
            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet("color: #ccc;")
            header_layout.addWidget(separator)
            
            header_action = QWidgetAction(menu)
            header_action.setDefaultWidget(header_widget)
            menu.addAction(header_action)
            
            # "Leere Werte anzeigen" Option
            empty_checkbox = QCheckBox("(Leere Werte)")
            empty_checkbox.setChecked(True)  # Standard: alle anzeigen
            empty_checkbox.stateChanged.connect(lambda state: self._on_dropdown_filter_preview_changed(field_name, "__EMPTY__", state == 2))
            
            empty_action = QWidgetAction(menu)
            empty_action.setDefaultWidget(empty_checkbox)
            menu.addAction(empty_action)
            
            # Separator
            menu.addSeparator()
            
            # Optionen-Checkboxes
            for option_key, option_display in sorted(dropdown_options.items()):
                if option_key:  # Keine leeren Keys
                    checkbox = QCheckBox(f"{option_display} ({option_key})")
                    checkbox.setChecked(True)  # Standard: alle ausgewählt
                    checkbox.stateChanged.connect(
                        lambda state, key=option_key: self._on_dropdown_filter_preview_changed(field_name, key, state == 2)
                    )
                    
                    action = QWidgetAction(menu)
                    action.setDefaultWidget(checkbox)
                    menu.addAction(action)
            
            # Initial alle Keys als ausgewählt markieren
            self._dropdown_filters[field_name]["selected_keys"] = set(dropdown_options.keys())
            self._dropdown_filters[field_name]["show_empty"] = True
            
            # Preview-Status für Live-Updates ohne direkte Anwendung
            if not hasattr(self, '_dropdown_filter_previews'):
                self._dropdown_filter_previews = {}
            self._dropdown_filter_previews[field_name] = {
                "selected_keys": set(dropdown_options.keys()),
                "show_empty": True
            }
            
            logger.debug(f"🔧 Dropdown-Filter-Menu erstellt für {field_name} mit {len(dropdown_options)} Optionen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Dropdown-Filter-Menus für {field_name}: {e}")
    
    def _apply_dropdown_filter_and_close(self, field_name, menu):
        """Wendet den Dropdown-Filter an und schließt das Menu"""
        try:
            # Preview-Einstellungen zu aktiven Filtern übernehmen
            if hasattr(self, '_dropdown_filter_previews') and field_name in self._dropdown_filter_previews:
                preview = self._dropdown_filter_previews[field_name]
                self._dropdown_filters[field_name]["selected_keys"] = preview["selected_keys"].copy()
                self._dropdown_filters[field_name]["show_empty"] = preview["show_empty"]
            
            # Filter anwenden
            self._apply_filters()
            
            # Button-Text aktualisieren
            self._update_dropdown_filter_button_text(field_name)
            
            # Menu schließen
            menu.hide()
            
            # Status-Info
            selected_count = len(self._dropdown_filters[field_name]["selected_keys"])
            show_empty = self._dropdown_filters[field_name]["show_empty"]
            logger.info(f"✅ Dropdown-Filter für {field_name} angewendet: {selected_count} Keys, Leere: {show_empty}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des Dropdown-Filters: {e}")
    
    def _on_dropdown_filter_preview_changed(self, field_name, option_key, is_selected):
        """Wird aufgerufen wenn eine Dropdown-Filter-Option in der Vorschau geändert wird"""
        try:
            if not hasattr(self, '_dropdown_filter_previews'):
                self._dropdown_filter_previews = {}
            
            if field_name not in self._dropdown_filter_previews:
                # Initial alle Optionen als ausgewählt setzen
                dropdown_options = self._get_dropdown_options(self._get_field_config_by_name(field_name))
                self._dropdown_filter_previews[field_name] = {
                    "selected_keys": set(dropdown_options.keys()),
                    "show_empty": True
                }
            
            if option_key == "__EMPTY__":
                # Leere Werte Option
                self._dropdown_filter_previews[field_name]["show_empty"] = is_selected
            else:
                # Normale Option
                if is_selected:
                    self._dropdown_filter_previews[field_name]["selected_keys"].add(option_key)
                else:
                    self._dropdown_filter_previews[field_name]["selected_keys"].discard(option_key)
            
            # Live-Preview im Button-Text (ohne Filter anzuwenden)
            self._update_dropdown_filter_preview_text(field_name)
            
            logger.debug(f"🔧 Dropdown-Filter-Preview {field_name} geändert: {len(self._dropdown_filter_previews[field_name]['selected_keys'])} Keys")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ändern der Dropdown-Filter-Preview: {e}")
    
    def _update_dropdown_filter_preview_text(self, field_name):
        """Aktualisiert den Button-Text basierend auf der Preview-Auswahl"""
        try:
            if field_name not in self._dropdown_filter_previews:
                return
            
            preview = self._dropdown_filter_previews[field_name]
            selected_count = len(preview["selected_keys"])
            show_empty = preview["show_empty"]
            
            # Button finden (vereinfachte Suche)
            button = self._find_dropdown_filter_button(field_name)
            
            if button:
                # Preview-Text mit visueller Kennzeichnung
                total_options = len(self._get_dropdown_options(self._get_field_config_by_name(field_name)))
                
                if selected_count == 0 and not show_empty:
                    button.setText("🔸 Keine (Vorschau)")
                    button.setStyleSheet("QPushButton { text-align: left; padding: 5px; color: red; font-style: italic; }")
                elif show_empty and selected_count == total_options:
                    button.setText("🔸 Alle (Vorschau)")
                    button.setStyleSheet("QPushButton { text-align: left; padding: 5px; color: #666; font-style: italic; }")
                else:
                    button.setText(f"🔸 {selected_count} von {total_options} (Vorschau)")
                    button.setStyleSheet("QPushButton { text-align: left; padding: 5px; color: #0066cc; font-style: italic; }")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Preview-Button-Texts: {e}")
    
    def _find_dropdown_filter_button(self, field_name):
        """Findet den Filter-Button für ein bestimmtes Feld"""
        try:
            # Suche den Button in den Search-Widgets
            if hasattr(self, 'search_widgets') and field_name in self.search_widgets:
                widget = self.search_widgets[field_name]
                if isinstance(widget, QPushButton):
                    return widget
            return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Finden des Filter-Buttons: {e}")
            return None
    
    def _toggle_all_dropdown_options(self, field_name, select_all, menu):
        """Wählt alle oder keine Optionen im Dropdown-Filter aus"""
        try:
            # Alle Checkboxes im Menu finden und setzen
            for action in menu.actions():
                widget_action = action
                if isinstance(widget_action, QWidgetAction):
                    widget = widget_action.defaultWidget()
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(select_all)
            
            # Filter-Status aktualisieren wird durch die einzelnen Checkbox-Signals gemacht
            logger.debug(f"🔧 Dropdown-Filter {field_name}: {'Alle' if select_all else 'Keine'} ausgewählt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Toggle aller Dropdown-Optionen: {e}")
    
    def _reset_dropdown_filter(self, field_name, menu):
        """Setzt den Dropdown-Filter zurück (alle ausgewählt)"""
        try:
            # Alle Checkboxes aktivieren
            self._toggle_all_dropdown_options(field_name, True, menu)
            
            # Preview und aktiven Filter synchronisieren
            dropdown_options = self._get_dropdown_options(self._get_field_config_by_name(field_name))
            
            # Preview zurücksetzen
            if not hasattr(self, '_dropdown_filter_previews'):
                self._dropdown_filter_previews = {}
            self._dropdown_filter_previews[field_name] = {
                "selected_keys": set(dropdown_options.keys()),
                "show_empty": True
            }
            
            # Aktiven Filter zurücksetzen
            self._dropdown_filters[field_name] = {
                "selected_keys": set(dropdown_options.keys()),
                "show_empty": True
            }
            
            # Filter sofort anwenden und Button aktualisieren
            self._apply_filters()
            self._update_dropdown_filter_button_text(field_name)
            
            logger.info(f"🔄 Dropdown-Filter für {field_name} zurückgesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen des Dropdown-Filters: {e}")
    
    def _on_dropdown_filter_changed(self, field_name, option_key, is_selected):
        """DEPRECATED: Ersetzt durch Preview-System. Wird für Kompatibilität beibehalten."""
        # Weiterleitung an Preview-System
        self._on_dropdown_filter_preview_changed(field_name, option_key, is_selected)
        """Wird aufgerufen wenn eine Dropdown-Filter-Option geändert wird"""
        try:
            if field_name not in self._dropdown_filters:
                self._dropdown_filters[field_name] = {"selected_keys": set(), "show_empty": True}
            
            if option_key == "__EMPTY__":
                # Leere Werte Option
                self._dropdown_filters[field_name]["show_empty"] = is_selected
            else:
                # Normale Option
                if is_selected:
                    self._dropdown_filters[field_name]["selected_keys"].add(option_key)
                else:
                    self._dropdown_filters[field_name]["selected_keys"].discard(option_key)
            
            # Filter anwenden
            self._apply_filters()
            
            # Button-Text aktualisieren
            self._update_dropdown_filter_button_text(field_name)
            
            logger.debug(f"🔧 Dropdown-Filter {field_name} geändert: {len(self._dropdown_filters[field_name]['selected_keys'])} Keys ausgewählt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ändern des Dropdown-Filters: {e}")
    
    def _update_dropdown_filter_button_text(self, field_name):
        """Aktualisiert den Text des Filter-Buttons basierend auf der aktiven Auswahl"""
        try:
            if field_name not in self._dropdown_filters:
                return
            
            filter_data = self._dropdown_filters[field_name]
            selected_count = len(filter_data["selected_keys"])
            show_empty = filter_data["show_empty"]
            
            # Button finden (vereinfachte Suche)
            button = self._find_dropdown_filter_button(field_name)
            
            if button:
                # Button-Text basierend auf aktiver Auswahl (ohne Preview-Kennzeichnung)
                total_options = len(self._get_dropdown_options(self._get_field_config_by_name(field_name)))
                
                if selected_count == 0 and not show_empty:
                    button.setText("🔴 Keine aktiv")
                    button.setStyleSheet("QPushButton { text-align: left; padding: 5px; color: red; font-weight: bold; }")
                elif show_empty and selected_count == total_options:
                    button.setText("✅ Alle aktiv")
                    button.setStyleSheet("QPushButton { text-align: left; padding: 5px; color: green; }")
                else:
                    button.setText(f"🔵 {selected_count} von {total_options} aktiv")
                    button.setStyleSheet("QPushButton { text-align: left; padding: 5px; color: blue; font-weight: bold; }")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Button-Texts: {e}")
    
    def _get_field_config_by_name(self, field_name):
        """Hilfsmethode um die Feld-Konfiguration anhand des Namens zu finden"""
        for field_config in self.view_fields:
            if field_config["feld"] == field_name:
                return field_config
        return None
    
    def _create_table(self, layout):
        """Erstellt die Haupttabelle"""
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # Header-Styling
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)
        
        # Row selection
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        
        layout.addWidget(self.table)
    
    def _create_status_bar(self, layout):
        """Erstellt die Status-Leiste"""
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-top: 1px solid #ccc; }")
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("Bereit")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.row_count_label = QLabel("0 Datensätze")
        status_layout.addWidget(self.row_count_label)
        
        layout.addWidget(status_frame)
    
    def _detect_structure_type(self, data):
        """
        Erkennt automatisch, ob die Datenstruktur flach oder historisch ist.
        
        Returns:
            "flat": Flache Struktur mit direkten Werten
            "nested": Historische verschachtelte Struktur
        """
        if not isinstance(data, dict):
            return "flat"
        
        # Prüfe auf typische historische Gruppen
        nested_groups = ["PERSDATEN", "ANSCHRIFT_PERSON", "KOMMUNIKATION", "FINANZDATEN"]
        
        for group_name in nested_groups:
            if group_name in data:
                group_data = data[group_name]
                if isinstance(group_data, dict):
                    # Prüfe ob es verschachtelte Timestamp-Strukturen gibt
                    for field_name, field_data in group_data.items():
                        if isinstance(field_data, dict):
                            # Prüfe ob Keys wie Timestamps aussehen
                            for key in field_data.keys():
                                try:
                                    float(key)  # Timestamp-ähnlicher Key
                                    return "nested"
                                except:
                                    continue
                return "nested"
        
        # Wenn keine verschachtelten Gruppen, dann flach
        return "flat"
    
    def _get_field_value_smart(self, db_instance, field_name, stichtag):
        """
        Holt einen Feldwert intelligent über get_value() aus verschiedenen Gruppen.
        
        Args:
            db_instance: PdvmCentralDatenbank Instanz
            field_name: Name des gesuchten Feldes
            stichtag: Zeitpunkt für historische Daten
            
        Returns:
            Der Wert des Feldes oder None wenn nicht gefunden
        """
        # Typische Gruppen in denen Felder liegen können
        search_groups = ["PERSDATEN", "KOMMUNIKATION", "ANSCHRIFT_PERSON", "ANSCHRIFT", "FINANZDATEN", "STEUER", "SOZIALVERSICHERUNG"]
        
        for group in search_groups:
            try:
                result = db_instance.get_value(group, field_name, stichtag)
                if result and "wert" in result:
                    value = result["wert"]
                    logger.debug(f"      ✅ Gefunden in {group}: {field_name} = {value}")
                    return value
            except Exception as e:
                logger.debug(f"      ⚠️ Fehler in {group}.{field_name}: {e}")
                continue
        
        # Fallback: Direkt aus Root-Level versuchen
        try:
            if field_name in db_instance.data:
                value = db_instance.data[field_name]
                logger.debug(f"      ✅ Gefunden in Root: {field_name} = {value}")
                return value
        except:
            pass
        
        logger.debug(f"      🚫 Nicht gefunden: {field_name}")
        return None

    def _flatten_record(self, record):
        """
        Löst verschachtelte JSON-Strukturen in den Record-Daten auf
        
        Die persondaten-Tabelle hat folgende Struktur:
        - uid: GUID
        - PERSDATEN: Dict mit Personendaten
        - ANSCHRIFT_PERSON: Dict mit Adressdaten
        
        Jedes Feld in den Dicts hat die Struktur: {timestamp: wert}
        """
        flattened = {}
        
        logger.debug(f"🔍 Flattening record with keys: {list(record.keys())}")
        
        for key, value in record.items():
            if key == "uid":
                # UID direkt übernehmen
                flattened[key] = value
                logger.debug(f"   ✅ Direct: {key} = {value}")
            elif isinstance(value, dict):
                # JSON-Dict auflösen
                logger.debug(f"   🔧 Processing dict '{key}' with {len(value)} items")
                for field_name, field_data in value.items():
                    if isinstance(field_data, dict) and field_data:
                        # Nehme den neuesten Wert (letzter Timestamp)
                        latest_value = list(field_data.values())[-1]
                        flattened[field_name] = latest_value
                        logger.debug(f"      ✅ Extracted: {field_name} = {latest_value}")
                    else:
                        # Direkter Wert
                        flattened[field_name] = field_data
                        logger.debug(f"      ✅ Direct: {field_name} = {field_data}")
            else:
                # Andere Werte direkt übernehmen
                flattened[key] = value
                logger.debug(f"   ✅ Direct: {key} = {value}")
        
        logger.debug(f"🎯 Flattened record keys: {list(flattened.keys())}")
        return flattened

    def refresh(self):
        """Aktualisiert die Daten über den Data-Manager."""
        try:
            if self.data_manager:
                self.data_manager.refresh()
                self._load_data_from_manager()
                logger.info("🔄 View über Data-Manager aktualisiert")
            else:
                logger.warning("⚠️ Kein Data-Manager verfügbar für Refresh")
        except Exception as e:
            logger.error(f"❌ Fehler beim Refresh über Data-Manager: {e}")

    def set_stichtag(self, stichtag: float):
        """
        Setzt einen neuen Stichtag und lädt die Daten neu.
        
        Args:
            stichtag: Pdvm_DateTime Wert (z.B. 2025043.0)
        """
        logger.info(f"📅 Setze neuen Stichtag: {stichtag}")
        self.stichtag = stichtag
        self._load_data()  # Daten mit neuem Stichtag neu laden
        if hasattr(self, 'table'):
            self._populate_table()  # Tabelle aktualisieren
    
    def _setup_table_columns(self):
        """Konfiguriert die Tabellenspalten über den Data-Manager."""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Spalten-Setup wird ignoriert.")
            return
        if not self.data_manager:
            return
        
        field_names = self.data_manager.get_field_names()
        logger.debug(f"🔍 Spalten-Setup: {len(field_names)} Felder")
        
        # Spalten konfigurieren
        self.table.setColumnCount(len(field_names))
        headers = []
        
        for field_name in field_names:
            field_config = self.data_manager.get_field_config(field_name)
            if field_config:
                headers.append(field_config["name"])
            else:
                headers.append(field_name)
        
        self.table.setHorizontalHeaderLabels(headers)
        logger.debug(f"🔧 Tabellenspalten konfiguriert: {headers}")
        
        # Spaltenbreiten werden in _finalize_setup() gesetzt
        # um sicherzustellen, dass das Widget seine finale Größe hat
    
    def _finalize_setup(self):
        """Finalisiert das Setup nach dem Layout-Update über den Data-Manager."""
        try:
            if not self.data_manager:
                return
            
            field_names = self.data_manager.get_field_names()
            
            # Jetzt können wir die korrekten Spaltenbreiten setzen
            available_width = self.table.viewport().width()
            if available_width > 100:  # Nur wenn Widget eine vernünftige Breite hat
                
                for i, field_name in enumerate(field_names):
                    field_config = self.data_manager.get_field_config(field_name)
                    if not field_config:
                        continue
                        
                    ui_config = field_config.get("ui", {})
                    width = ui_config.get("width", "auto")
                    
                    if width != "auto":
                        if "%" in str(width):
                            # Prozentuale Breite
                            pct = int(str(width).replace("%", ""))
                            pixel_width = int(available_width * pct / 100)
                            self.table.setColumnWidth(i, pixel_width)
                        elif str(width).isdigit():
                            # Feste Pixel-Breite
                            self.table.setColumnWidth(i, int(width))
                
                # Auto-Resize für Spalten ohne explizite Breite
                header = self.table.horizontalHeader()
                header.setStretchLastSection(True)
                
                # Für die ersten Spalten ResizeToContents verwenden
                for i in range(min(3, len(field_names))):
                    header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
                
                logger.debug(f"✅ Spaltenbreiten finalisiert - Verfügbare Breite: {available_width}px")
            
            # Tabelle neu populieren, falls Daten bereits geladen
            if self.table_data:
                self._apply_filters()
                logger.debug(f"✅ Tabelle nach Setup neu populiert mit {len(self.filtered_data)} Zeilen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Finalisieren des Setups: {e}")
    
    def _apply_filters(self):
        """Wendet alle Filter über den Data-Manager an"""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Filterung wird ignoriert.")
            return
        if not self.data_manager:
            logger.debug("❌ Kein Data-Manager verfügbar für Filterung")
            return
            
        # Filter sammeln
        filters = self._collect_active_filters()
        
        # Filter über Manager anwenden
        self.filtered_data = self.data_manager.apply_filters(filters)
        
        logger.debug(f"🔍 Filterung: {len(self.filtered_data)} von {len(self.table_data)} Datensätzen")
        
        # Sortierung
        if self.current_sort_column is not None:
            self._sort_data()
        
        # Tabelle aktualisieren
        self._populate_table()
        self._update_status()
    
    def _collect_active_filters(self):
        """Sammelt alle aktiven Filter aus den UI-Widgets."""
        filters = {}
        
        if not hasattr(self, 'search_widgets') or not self.search_widgets:
            return filters
        
        for field_name, search_widget in self.search_widgets.items():
            # Text-Filter (QLineEdit)
            if isinstance(search_widget, QLineEdit):
                search_text = search_widget.text().strip()
                if search_text:
                    filters[field_name] = search_text
            
            # Dropdown-Filter (QPushButton)
            elif isinstance(search_widget, QPushButton):
                if hasattr(self, '_dropdown_filters') and field_name in self._dropdown_filters:
                    filter_data = self._dropdown_filters[field_name]
                    # Nur Filter hinzufügen wenn nicht alle ausgewählt sind
                    if not self._is_filter_showing_all(field_name, filter_data):
                        filters[field_name] = filter_data
        
        return filters
    
    def _is_filter_showing_all(self, field_name: str, filter_data: dict) -> bool:
        """Prüft ob ein Dropdown-Filter alle Optionen anzeigt."""
        if not self.data_manager:
            return True
        
        dropdown_options = self.data_manager.get_dropdown_options(field_name)
        selected_keys = filter_data.get('selected_keys', set())
        show_empty = filter_data.get('show_empty', True)
        
        # Alle Keys ausgewählt + leere Werte = alle anzeigen
        return len(selected_keys) == len(dropdown_options) and show_empty
    
    def _get_search_value(self, widget):
        """Holt den aktuellen Suchwert aus einem Search-Widget"""
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, QComboBox):
            current_text = widget.currentText().strip()
            if current_text == "-- Alle --" or not current_text:
                return None
            return current_text
        elif isinstance(widget, QPushButton):
            # Dropdown-Filter: Keine direkte Text-Suche, Filter wird in _field_matches_filter gehandhabt
            return None
        return None
    
    def _field_matches_filter(self, record, field_config, search_value):
        """
        Prüft ob ein Feld den Filter erfüllt.
        Für Dropdown-Felder wird der Multi-Select-Filter verwendet,
        für andere Felder die normale Text-Suche.
        """
        field_name = field_config["feld"]
        field_type = field_config["type"]
        filter_type = field_config.get("ui", {}).get("filterType", "contains")
        
        # Dropdown-Filter haben Priorität
        if (field_type == "dropdown" or filter_type == "dropdown") and hasattr(self, '_dropdown_filters'):
            return self._check_dropdown_filter(record, field_config)
        
        # Für normale Felder: Text-basierte Suche
        if not search_value:
            return True  # Kein Filter = alle anzeigen
        
        record_value = record.get(field_name, "")
        search_value_lower = str(search_value).lower()
        record_value_str = str(record_value).lower()
        
        if field_type == "string":
            if filter_type == "contains":
                return search_value_lower in record_value_str
            elif filter_type == "exact":
                return search_value_lower == record_value_str
                
        elif field_type == "date":
            # KORREKTUR: Flexible Datums-Suche über String-Vergleich
            # Unterstützt "2024", "01.01", "Januar", etc.
            if search_value_lower in record_value_str:
                return True
            
            # Zusätzlich: Formatierte Datumssuche
            if isinstance(record_value, str) and record_value:
                try:
                    # Versuche verschiedene Datumsformate
                    date_obj = datetime.strptime(record_value, "%Y-%m-%d")
                    formatted_dates = [
                        date_obj.strftime("%d.%m.%Y"),
                        date_obj.strftime("%d.%m.%y"),
                        date_obj.strftime("%Y"),
                        date_obj.strftime("%m/%Y"),
                        date_obj.strftime("%B %Y").lower(),  # "Januar 2024"
                        date_obj.strftime("%b %Y").lower(),  # "Jan 2024"
                    ]
                    
                    for formatted in formatted_dates:
                        if search_value_lower in formatted.lower():
                            return True
                except:
                    pass
            return False
                        
        elif field_type in ["int", "float"]:
            try:
                record_num = float(record_value)
                
                # Erweiterte Nummer-Suche
                if search_value_lower.startswith(">"):
                    threshold = float(search_value_lower[1:])
                    return record_num > threshold
                elif search_value_lower.startswith("<"):
                    threshold = float(search_value_lower[1:])
                    return record_num < threshold
                elif "-" in search_value_lower:
                    # Bereichsfilter
                    try:
                        min_val, max_val = map(float, search_value_lower.split("-"))
                        return min_val <= record_num <= max_val
                    except:
                        return False
                else:
                    # Exakte Suche oder "enthält" für Nummern
                    return search_value_lower in record_value_str or record_num == float(search_value)
            except:
                # Fallback: String-Vergleich
                return search_value_lower in record_value_str
        
        # Fallback: Immer String-Vergleich
        return search_value_lower in record_value_str
    
    def _check_dropdown_filter(self, record, field_config):
        """
        Prüft ob ein Datensatz den Dropdown-Filter erfüllt.
        Arbeitet direkt auf den Original-Keys, nicht auf Übersetzungen.
        
        Args:
            record: Der zu prüfende Datensatz
            field_config: Feld-Konfiguration
            
        Returns:
            bool: True wenn der Datensatz angezeigt werden soll
        """
        field_name = field_config["feld"]
        
        # Prüfe ob ein Filter für dieses Feld existiert
        if field_name not in self._dropdown_filters:
            return True  # Kein Filter = alle anzeigen
        
        filter_data = self._dropdown_filters[field_name]
        selected_keys = filter_data["selected_keys"]
        show_empty = filter_data["show_empty"]
        
        # Feld-Wert aus Record holen
        record_value = record.get(field_name, "")
        
        # Leere Werte prüfen
        if not record_value or record_value == "":
            return show_empty
        
        # Prüfen ob der Key in den ausgewählten Keys ist
        record_value_str = str(record_value).strip()
        is_selected = record_value_str in selected_keys
        
        logger.debug(f"🔍 Dropdown-Filter {field_name}: Wert '{record_value_str}' → {'✅' if is_selected else '❌'}")
        
        return is_selected
    
    def _sort_data(self):
        """Sortiert die gefilterten Daten nach der aktuellen Spalte."""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Sortierung wird ignoriert.")
            return
        if not self.filtered_data or self.current_sort_column is None:
            return
        
        if not self.data_manager:
            logger.debug("❌ Kein Data-Manager verfügbar für Sortierung")
            return
        
        # Feldname für Sortierung ermitteln
        field_name = self.data_manager.get_field_name_by_index(self.current_sort_column)
        if not field_name:
            logger.debug(f"❌ Kein Feldname für Spalte {self.current_sort_column} gefunden")
            return
        
        try:
            # Sortierung mit Nullwert-Behandlung
            def sort_key(record):
                value = record.get(field_name, '')
                if value is None:
                    return ''
                return str(value).lower()
            
            self.filtered_data.sort(
                key=sort_key,
                reverse=self.current_sort_order == Qt.DescendingOrder
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortieren: {e}")
    
    def _populate_table(self):
        """Füllt die Tabelle mit den gefilterten/sortierten Daten über den Data-Manager."""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Tabellen-Population wird ignoriert.")
            return
        if not self.data_manager or not self.filtered_data:
            logger.debug(f"❌ Tabellen-Population Check: data_manager={bool(self.data_manager)}, filtered_data={len(self.filtered_data) if self.filtered_data else 0}")
            self.table.setRowCount(0)
            return
        
        self.table.setRowCount(len(self.filtered_data))
        logger.debug(f"📊 Populiere Tabelle mit {len(self.filtered_data)} Zeilen über Data-Manager")
        
        field_names = self.data_manager.get_field_names()
        logger.debug(f"🔍 Verfügbare Felder: {field_names}")
        
        for row, record in enumerate(self.filtered_data):
            for col, field_name in enumerate(field_names):
                # Rohwert aus Datensatz holen
                raw_value = record.get(field_name)
                # Anzeigewert über Data-Manager ermitteln
                display_value = self.data_manager.get_display_value(field_name, raw_value)
                
                item = QTableWidgetItem(str(display_value))
                item.setData(Qt.UserRole, record)  # Vollständiger Datensatz für späteren Zugriff
                
                self.table.setItem(row, col, item)
        
        logger.debug(f"✅ Tabelle erfolgreich populiert mit {len(self.filtered_data)} Zeilen")
    
    def _get_display_value(self, record, field_name):
        """Ermittelt den Anzeigewert für ein Feld über den Data-Manager."""
        if not self.data_manager:
            return str(record.get(field_name, ''))
        
        # Rohwert aus Datensatz holen
        raw_value = record.get(field_name)
        # Mit korrekter Parameter-Reihenfolge aufrufen
        return self.data_manager.get_display_value(field_name, raw_value)
    
    def _update_status(self):
        """Aktualisiert die Status-Anzeige über den Data-Manager."""
        if not self.data_manager:
            self.row_count_label.setText("Keine Daten")
            self.status_label.setText("Kein Data-Manager")
            return
        
        total_count = len(self.table_data) if self.table_data else 0
        filtered_count = len(self.filtered_data) if self.filtered_data else 0
        
        if filtered_count == total_count:
            self.row_count_label.setText(f"{total_count} Datensätze")
        else:
            self.row_count_label.setText(f"{filtered_count} von {total_count} Datensätzen")
        
        self.status_label.setText("Bereit")
    
    def _get_table_display_name(self):
        """Holt den Anzeigenamen der Tabelle über den Data-Manager."""
        if self.data_manager and self.data_manager.view_config:
            root_config = self.data_manager.view_config.get("ROOT", {})
            return root_config.get("view_table", "Unbekannte Tabelle")
        return "Datenansicht"
    
    # Event Handlers
    def _on_search_changed(self):
        """Wird aufgerufen wenn sich ein Suchfilter ändert"""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Suche wird ignoriert.")
            return
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms Verzögerung
    
    def _on_header_clicked(self, logical_index):
        """Wird aufgerufen wenn ein Spalten-Header geklickt wird"""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Header-Klick wird ignoriert.")
            return
        if self.current_sort_column == logical_index:
            # Umschalten zwischen Auf-/Absteigend
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.AscendingOrder
        
        self._apply_filters()

    def _on_row_selected(self):
        """Wird aufgerufen wenn eine Zeile ausgewählt wird"""
        if self.dummy_mode:
            logger.info("[ModernViewWidget] Dummy-Modus: Zeilenauswahl wird ignoriert.")
            return
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                record = item.data(Qt.UserRole)
                if record:
                    self.rowSelected.emit(record)
    
    def _clear_filters(self):
        """Löscht alle Filter - Text-Filter und Dropdown-Filter KOMPLETT"""
        logger.info("🗑️ Filter-Reset gestartet...")
        
        # 1. Standard Text-Filter zurücksetzen
        for field_name, widget in self.search_widgets.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
                logger.debug(f"  ✅ Text-Filter zurückgesetzt: {field_name}")
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)  # "-- Alle --"
                logger.debug(f"  ✅ ComboBox-Filter zurückgesetzt: {field_name}")
            elif isinstance(widget, QPushButton):
                # Das ist ein Dropdown-Filter-Button - Text zurücksetzen
                field_config = self.data_manager.get_field_config(field_name)
                if field_config:
                    field_display = field_config.get("name", field_name)
                    widget.setText(f"🔽 {field_display} (Alle)")
                    widget.setStyleSheet("QPushButton { text-align: left; padding: 5px; }")
                    logger.debug(f"  ✅ Dropdown-Button zurückgesetzt: {field_name}")
        
        # 2. Dropdown-Filter-Status KOMPLETT zurücksetzen
        if hasattr(self, '_dropdown_filters') and self._dropdown_filters:
            for field_name in list(self._dropdown_filters.keys()):
                try:
                    # Feld-Konfiguration holen
                    field_config = self.data_manager.get_field_config(field_name)
                    if not field_config:
                        logger.debug(f"  ⚠️ Keine Konfiguration für {field_name}")
                        continue
                    
                    field_type = field_config.get("type", "string")
                    ui_config = field_config.get("ui", {})
                    filter_type = ui_config.get("filterType", "text")
                    
                    # Prüfe ob es ein Dropdown-Filter ist
                    if field_type == "dropdown" or filter_type == "dropdown":
                        # Dropdown-Optionen holen
                        dropdown_options = self.data_manager.get_dropdown_options(field_name)
                        
                        if dropdown_options:
                            # KOMPLETT ZURÜCKSETZEN: Alle Optionen auswählen (= kein Filter aktiv)
                            self._dropdown_filters[field_name] = {
                                "selected_keys": set(dropdown_options.keys()),
                                "show_empty": True
                            }
                            logger.debug(f"  ✅ Dropdown-Filter-Status KOMPLETT zurückgesetzt: {field_name}")
                        else:
                            logger.debug(f"  ⚠️ Keine Dropdown-Optionen für {field_name}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Fehler beim Zurücksetzen von {field_name}: {e}")
            
            # WICHTIG: Dropdown-Filter-Dictionary komplett leeren für sauberen Zustand
            logger.debug(f"  🧹 Dropdown-Filter vor Reset: {len(self._dropdown_filters)} aktive Filter")
            self._dropdown_filters.clear()
            logger.debug(f"  🧹 Dropdown-Filter nach Reset: {len(self._dropdown_filters)} aktive Filter")
        
        # 3. Preview-Filter löschen (falls vorhanden)
        if hasattr(self, '_dropdown_filter_previews'):
            self._dropdown_filter_previews.clear()
        
        # 4. Filter anwenden (zeigt wieder alle Daten)
        self._apply_filters()
        
        logger.info("🗑️ ✅ Alle Filter KOMPLETT zurückgesetzt - sowohl Text-Filter als auch Dropdown-Filter")
    
    def _refresh_data(self):
        """Lädt die Daten neu"""
        self.status_label.setText("Lade Daten...")
        self._load_data_from_manager()
    
    def _export_data(self):
        """Exportiert die aktuellen Daten"""
        # TODO: Export-Funktionalität implementieren
        QMessageBox.information(self, "Export", "Export-Funktionalität wird implementiert...")
    
    def _show_error(self, message):
        """Zeigt eine Fehlermeldung an"""
        QMessageBox.critical(self, "Fehler", message)
    
    def resizeEvent(self, event):
        """Wird aufgerufen wenn das Widget die Größe ändert"""
        super().resizeEvent(event)
        # Spaltenbreiten nach Größenänderung anpassen
        if hasattr(self, 'setup_timer'):
            self.setup_timer.stop()
            self.setup_timer.start(100)
        
    # Public Methods
    def get_selected_record(self):
        """Gibt den aktuell ausgewählten Datensatz zurück"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, 0)
            if item:
                return item.data(Qt.UserRole)
        return None
    
    def refresh(self):
        """Öffentliche Methode zum Neuladen der Daten"""
        self._refresh_data()
    
    def set_filter(self, field_name, value):
        """Setzt einen Filter programmatisch"""
        if field_name in self.search_widgets:
            widget = self.search_widgets[field_name]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
            
            self._apply_filters()
    
    def get_selected_record(self):
        """Gibt den aktuell ausgewählten Datensatz zurück"""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.filtered_data):
            return self.filtered_data[current_row]
        return None
    
    def get_selected_guid(self):
        """Gibt die GUID des ausgewählten Datensatzes zurück"""
        record = self.get_selected_record()
        return record.get('_guid') if record else None
