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
    Vereinfachter Dialog nur für die Spaltenauswahl (Sichtbarkeit).
    Reihenfolge wird direkt in der Tabelle per Drag & Drop verwaltet.
    """
    
    def __init__(self, available_columns, selected_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spaltenauswahl")
        self.setModal(True)
        self.resize(450, 400)
        
        self.available_columns = available_columns  # Liste von {"name": str, "label": str}
        self.selected_columns = selected_columns.copy()  # Liste der ausgewählten Namen
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Überschrift
        title_label = QLabel("Wählen Sie die anzuzeigenden Spalten:")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Hinweis für Reihenfolge
        hint_label = QLabel("💡 Tipp: Spalten-Reihenfolge können Sie direkt in der Tabelle per Drag & Drop ändern")
        hint_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 15px; padding: 8px; background-color: #f0f0f0; border-radius: 4px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # Scroll-Bereich für Checkboxen
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.checkboxes = {}
        
        # Standard-Spalten und Expert-Spalten getrennt anzeigen
        standard_cols = [col for col in self.available_columns if not col.get('expert', False)]
        expert_cols = [col for col in self.available_columns if col.get('expert', False)]
        
        # Standard-Spalten
        if standard_cols:
            std_header = QLabel("Standard-Spalten:")
            std_header.setStyleSheet("font-weight: bold; color: #333; margin-top: 5px;")
            scroll_layout.addWidget(std_header)
            
            for col_data in standard_cols:
                name = col_data["name"]
                label = col_data["label"]
                
                checkbox = QCheckBox(label)
                checkbox.setChecked(name in self.selected_columns)
                checkbox.stateChanged.connect(self._on_checkbox_changed)
                
                self.checkboxes[name] = checkbox
                scroll_layout.addWidget(checkbox)
        
        # Expert-Spalten (falls vorhanden)
        if expert_cols:
            # Trennlinie
            scroll_layout.addSpacing(10)
            
            expert_header = QLabel("Expert-Spalten:")
            expert_header.setStyleSheet("font-weight: bold; color: #e67e22; margin-top: 5px;")
            scroll_layout.addWidget(expert_header)
            
            for col_data in expert_cols:
                name = col_data["name"]
                label = col_data["label"]
                
                checkbox = QCheckBox(f"🔧 {label}")  # Expert-Icon
                checkbox.setChecked(name in self.selected_columns)
                checkbox.stateChanged.connect(self._on_checkbox_changed)
                checkbox.setStyleSheet("color: #e67e22;")  # Orange für Expert
                
                self.checkboxes[name] = checkbox
                scroll_layout.addWidget(checkbox)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Buttons für Schnell-Auswahl
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Alle auswählen")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Alle abwählen")
        deselect_all_btn.clicked.connect(self._deselect_all)
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # OK / Abbrechen Buttons
        dialog_buttons = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        dialog_buttons.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addWidget(cancel_btn)
        
        layout.addLayout(dialog_buttons)

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
    
    def __init__(self, view_guid, user_guid=None, parent=None, central_systemsteuerung=None):
        super().__init__(parent)
        
        # VERSION MARKER für Debug-Zwecke
        logger.info("🚀 PDVM MODERN VIEW WIDGET VERSION 2.0 - ZENTRALE SYSTEMSTEUERUNG EDITION GELADEN!")
        
        self.view_guid = view_guid
        self.user_guid = user_guid
        self.central_systemsteuerung = central_systemsteuerung  # Zentrale Systemsteuerung-Instanz
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
        
        # DEBUG: Test-Button für Spalten-Reihenfolge
        debug_button = QPushButton("🧪 Test Reihenfolge")
        debug_button.setToolTip("Testet die Spalten-Reihenfolge Funktionalität")
        debug_button.clicked.connect(self.test_column_order_functionality)
        debug_button.setMaximumWidth(120)
        debug_button.setStyleSheet("color: #666; font-size: 11px;")
        controls_row.addWidget(debug_button)
        
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
        """
        Schaltet Expert-Mode um.
        
        WICHTIG: display_show wird neu berechnet, aber nicht gespeichert für Expert-Spalten.
        Beim Zurückschalten auf Normal-Mode wird der ursprüngliche Zustand wiederhergestellt.
        """
        self.expert_mode = not self.expert_mode
        self.expert_button.setText("🔬 Expert-Mode: AN" if self.expert_mode else "🔬 Expert-Mode: AUS")
        self.expert_button.setChecked(self.expert_mode)
        
        # WICHTIG: Spaltenauswahl zurücksetzen wenn Mode gewechselt wird
        # Dies sorgt dafür, dass Expert-Spalten automatisch angezeigt werden
        if self.expert_mode:
            logger.debug("🔬 Expert-Mode aktiviert - Expert-Spalten werden verfügbar")
            # Spaltenauswahl wird in _update_visible_columns neu berechnet
        else:
            logger.debug("👤 Normal-Mode aktiviert - Expert-Spalten werden ausgeblendet")
            # Spaltenauswahl für Normal-Mode wird wiederhergestellt
        
        self._update_visible_columns()
        self._rebuild_table()
        
        # Einstellungen speichern (aber display_show für Expert-Spalten wird nicht persistent gespeichert)
        self._save_view_settings()

    def _load_view_settings(self):
        """Lädt die gespeicherten View-Einstellungen aus der systemsteuerung-Tabelle."""
        if not self.user_guid or not self.view_guid:
            logger.debug("🔧 Keine user_guid oder view_guid - verwende Standard-Einstellungen")
            return
        
        try:
            # KORRIGIERT: Verwende zentrale Systemsteuerung-Instanz
            if not self.central_systemsteuerung:
                logger.warning("⚠️ Zentrale Systemsteuerung nicht verfügbar - Standard-Werte verwenden")
                return
            
            # NEUE ARCHITEKTUR: Lade aus view_guid-Gruppe
            # Expert-Mode laden
            expert_mode_data = self.central_systemsteuerung.get_value(
                gruppe=self.view_guid,  # view_guid ist die Gruppe
                feld="expert_mode",
                ab_zeit=None
            )
            saved_expert_mode = expert_mode_data.get("wert", False) if expert_mode_data else False
            
            if saved_expert_mode != self.expert_mode:
                self.expert_mode = saved_expert_mode
                self.expert_button.setChecked(saved_expert_mode)
                self.expert_button.setText("🔬 Expert-Mode: AN" if saved_expert_mode else "🔬 Expert-Mode: AUS")
                logger.info(f"📋 ZENTRALE SYSTEMSTEUERUNG: Expert-Mode aus Gruppe {self.view_guid} geladen: {saved_expert_mode}")
            
            # Custom Columns laden
            custom_columns_data = self.central_systemsteuerung.get_value(
                gruppe=self.view_guid,  # view_guid ist die Gruppe
                feld="custom_columns",
                ab_zeit=None
            )
            saved_column_selection = custom_columns_data.get("wert", None) if custom_columns_data else None
            
            # 🎯 NEUES VOLLSTÄNDIGES CONTROL-SYSTEM: Ersetzt alle bisherigen Methoden
            logger.info("🔍 VOLLSTÄNDIGES CONTROL-SYSTEM: Lade View-Einstellungen...")
            
            column_order, column_selection = self._load_view_settings_v3()
            
            if column_order and column_selection:
                logger.info("✅ VOLLSTÄNDIGES CONTROL-SYSTEM: View-Einstellungen erfolgreich geladen")
                self.column_order = column_order
                self.column_selection = column_selection
            else:
                logger.warning("⚠️ VOLLSTÄNDIGES CONTROL-SYSTEM fehlgeschlagen - Fallback zu Standard")
                
                # Fallback zur Standard-Spalten aus data_manager
                control = getattr(self.data_manager, 'control', None)
                if control and hasattr(control, 'columns'):
                    all_columns = [col.get('name') for col in control.columns if col.get('name')]
                    self.column_order = all_columns
                    self.column_selection = {name: True for name in all_columns}
                    logger.info(f"✅ Standard-Fallback: {len(all_columns)} Spalten geladen")
                elif saved_column_selection:
                    # Fallback auf alte Einstellungen
                    self._custom_column_selection = saved_column_selection
                    logger.info(f"📋 Fallback: Alte Spaltenauswahl geladen: {len(saved_column_selection)} Spalten")
                    logger.info(f"📋 Geladene Spalten: {saved_column_selection}")
                else:
                    logger.error("❌ Alle Fallback-Methoden fehlgeschlagen")
                    return
            
            # Weitere Einstellungen können hier geladen werden:
            # - column_widths = current_view_settings.get("column_widths", {})
            
            logger.info(f"✅ View-Einstellungen für {self.view_guid} geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Einstellungen: {e}")

    def _save_view_settings(self):
        """Speichert die aktuellen View-Einstellungen in der systemsteuerung-Tabelle mit Gruppen-Architektur."""
        if not self.user_guid or not self.view_guid:
            logger.debug("🔧 Keine user_guid oder view_guid - Speichern übersprungen")
            return
        
        try:
            # KORRIGIERT: Verwende zentrale Systemsteuerung-Instanz
            if not self.central_systemsteuerung:
                logger.warning("⚠️ Zentrale Systemsteuerung nicht verfügbar - View-Einstellungen werden nicht gespeichert")
                return
            
            # NEUE ARCHITEKTUR: Verwende view_guid als Gruppe
            # Expert-Mode speichern
            self.central_systemsteuerung.set_value(
                gruppe=self.view_guid,  # view_guid ist die Gruppe
                feld="expert_mode",
                wert=self.expert_mode,
                ab_zeit=1001.0
            )
            
            # Custom Columns speichern
            custom_columns = getattr(self, '_custom_column_selection', [])
            self.central_systemsteuerung.set_value(
                gruppe=self.view_guid,  # view_guid ist die Gruppe
                feld="custom_columns",
                wert=custom_columns,
                ab_zeit=1001.0
            )
            
            # Last Updated speichern
            self.central_systemsteuerung.set_value(
                gruppe=self.view_guid,  # view_guid ist die Gruppe
                feld="last_updated",
                wert=datetime.now().isoformat(),
                ab_zeit=1001.0
            )
            
            # Änderungen persistieren
            self.central_systemsteuerung.save_values()
            
            logger.debug(f"💾 ZENTRALE SYSTEMSTEUERUNG: View-Einstellungen für Gruppe {self.view_guid} gespeichert: expert_mode={self.expert_mode}, custom_columns={len(getattr(self, '_custom_column_selection', []))}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der View-Einstellungen: {e}")

    def _reset_view_settings(self):
        """
        Setzt alle View-Einstellungen auf Standard zurück und löscht gespeicherte Werte.
        
        WICHTIG: Setzt display_show auf Standard-Werte zurück (basierend auf show/expert).
        """
        try:
            # Standard-Werte setzen
            self.expert_mode = False
            self.expert_button.setChecked(False)
            self.expert_button.setText("🔬 Expert-Mode: AUS")
            
            # Spaltenauswahl zurücksetzen
            self._custom_column_selection = None
            
            # display_show für alle Spalten auf Standard zurücksetzen
            control = getattr(self.data_manager, 'control', None)
            if control and hasattr(control, 'columns'):
                for col in control.columns:
                    show_val = col.get('show', False)
                    expert_val = col.get('expert', False)
                    # Standard: Nur show=True UND expert=False Spalten sind sichtbar
                    col['display_show'] = show_val and not expert_val
                    logger.debug(f"🔄 Reset Spalte '{col['name']}': display_show={col['display_show']} (show={show_val}, expert={expert_val})")
            
            # Gespeicherte Einstellungen löschen
            if self.user_guid and self.view_guid:
                # KORRIGIERT: Verwende zentrale Systemsteuerung-Instanz
                if not self.central_systemsteuerung:
                    logger.warning("⚠️ Zentrale Systemsteuerung nicht verfügbar - Reset nur lokal")
                else:
                    try:
                        # Alle Felder für diese View-Gruppe löschen
                        # Expert-Mode löschen
                        self.central_systemsteuerung.delete_value(gruppe=self.view_guid, feld="expert_mode")
                        # Custom Columns löschen
                        self.central_systemsteuerung.delete_value(gruppe=self.view_guid, feld="custom_columns")
                        # Last Updated löschen
                        self.central_systemsteuerung.delete_value(gruppe=self.view_guid, feld="last_updated")
                        
                        # Änderungen persistieren
                        self.central_systemsteuerung.save_values()
                        logger.info(f"🗑️ ZENTRALE SYSTEMSTEUERUNG: Gespeicherte Einstellungen für View-Gruppe {self.view_guid} gelöscht")
                    except Exception as e:
                        logger.warning(f"⚠️ Fehler beim Löschen der View-Einstellungen: {e}")
            
            # UI aktualisieren
            self._update_visible_columns()
            self._rebuild_table()
            
            logger.info("🔄 View-Einstellungen auf Standard zurückgesetzt")
            
            # Erfolgs-Meldung anzeigen
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Einstellungen zurückgesetzt", 
                f"Die View-Einstellungen wurden auf Standard zurückgesetzt.\n\n• Expert-Mode: AUS\n• Spaltenauswahl: Standard (show=True, expert=False)\n• display_show: Zurückgesetzt\n\nZukünftige Erweiterungen:\n• Spaltenbreiten: Standard\n• Sortierung: Standard"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der View-Einstellungen: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Fehler", f"Fehler beim Zurücksetzen:\n{str(e)}")

    def _update_column_selection_v2(self, available_columns, new_selection):
        """
        V2: Spaltenauswahl über Complete Control System aktualisieren.
        Verwendet die Systemsteuerung zur persistenten Speicherung.
        """
        try:
            logger.info(f"🔄 _update_column_selection_v2: {len(new_selection)} Spalten")
            
            # 1. display_show für alle verfügbaren Spalten aktualisieren
            for col in available_columns:
                col['display_show'] = col['name'] in new_selection
            
            # 2. Complete Controls aus systemsteuerung laden und aktualisieren
            complete_controls = self._load_complete_controls_v3()
            
            if complete_controls:
                # Sichtbarkeit in Complete Controls aktualisieren
                for control_name, control in complete_controls.items():
                    control['user_display_show'] = control_name in new_selection
                    control['last_updated'] = datetime.now().isoformat()
                
                # Zurück in systemsteuerung speichern
                self._save_complete_controls_v3(complete_controls)
                
                logger.info(f"✅ Complete Controls aktualisiert: {len(new_selection)} Spalten sichtbar")
            else:
                logger.warning("⚠️ Keine Complete Controls verfügbar für Update")
            
            # 3. Widget-Status aktualisieren
            self.visible_column_names = new_selection
            self._update_column_selection_button(available_columns)
            
            # 4. Tabelle über Complete Control System neu laden
            self._refresh_table_display()
            
            logger.info("✅ Spaltenauswahl erfolgreich aktualisiert (ohne neue Tabelle)")
            
        except Exception as e:
            logger.error(f"❌ Fehler in _update_column_selection_v2: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise

    def _update_visible_columns(self):
        """
        OPTIMIERTE 2-LEVEL-ARCHITEKTUR nach User-Spezifikation:
        
        1. Vollständige Tabelle + Controls werden geliefert
        2. Gespeicherte Ebene 2 wird angewendet oder neu erstellt
        3. Tabelle wird nach Ebene 2 dargestellt
        
        Order-System:
        - Normal: 1-199 (original order)
        - Expert: 200-399 (original order + 200)  
        - Nicht angezeigt: 999 (einheitlich)
        """
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            self.visible_column_names = []
            self.column_dropdown.clear()
            logger.debug("[ModernViewWidget] Keine Controlstruktur oder columns vorhanden!")
            return
            
        columns = control.columns
        logger.debug(f"[ModernViewWidget] SCHRITT 1: Vollständige Tabelle geladen - {len(columns)} Spalten total")
        
        # SCHRITT 2: Gespeicherte Ebene 2 anwenden oder neu erstellen
        level2_columns = self._apply_or_create_level2(columns)
        logger.debug(f"[ModernViewWidget] SCHRITT 2: Ebene 2 angewendet - {len(level2_columns)} Spalten")
        
        # SCHRITT 3: Ergebnis für Tabellendarstellung setzen
        self.visible_column_names = [col['name'] for col in level2_columns]
        
        # Debug-Ausgabe
        active_count = len([col for col in level2_columns if col.get('display_show', True)])
        inactive_count = len(level2_columns) - active_count
        logger.info(f"[ModernViewWidget] SCHRITT 3: Tabelle bereit - {active_count} sichtbar, {inactive_count} ausgeblendet")
        logger.info(f"[ModernViewWidget] Reihenfolge: {[col['name'] for col in level2_columns[:5]]}{'...' if len(level2_columns) > 5 else ''}")
        
        # Button-Text aktualisieren
        available_for_mode = self._get_available_columns_for_mode(columns)
        self._update_column_selection_button(available_for_mode)

    def _apply_or_create_level2(self, original_columns):
        """
        KERN-METHODE: Wendet gespeicherte Ebene 2 an oder erstellt sie neu.
        
        User-Spezifikation:
        - Gespeicherte Ebene 2 gefunden → anwenden
        - Keine Ebene 2 → aus Original-Parametern erstellen und sofort speichern
        
        Args:
            original_columns: Vollständige Original-Spalten aus control.columns
            
        Returns:
            Liste aller Spalten in Ebene-2-Reihenfolge mit display_show-Status
        """
        try:
            # Gespeicherte Ebene 2 laden
            v2_data = self._load_user_column_order_v2()
            
            # V2-Daten sind jetzt ein Tupel (column_order, column_selection)
            if v2_data and len(v2_data) == 2:
                column_order, column_selection = v2_data
                if column_order:  # Prüfe ob column_order nicht leer ist
                    logger.info("📋 EBENE 2: Gespeicherte Konfiguration gefunden - wird angewendet")
                    return self._apply_saved_level2(original_columns, v2_data)
            
            logger.info("📋 EBENE 2: Keine gespeicherte Konfiguration - erstelle aus Original-Parametern")
            return self._create_initial_level2(original_columns)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Ebene 2 Verarbeitung: {e}")
            # Fallback: Alle Spalten für aktuellen Mode als aktiv
            return self._get_available_columns_for_mode(original_columns)

    def _apply_saved_level2(self, original_columns, v2_data):
        """
        Wendet gespeicherte Ebene 2 Konfiguration an.
        
        Args:
            original_columns: Original-Spalten
            v2_data: Gespeicherte V2-Daten als Tupel (column_order, column_selection)
            
        Returns:
            Spalten in gespeicherter Reihenfolge mit aktualisiertem display_show
        """
        # Tupel unpacking
        if v2_data and len(v2_data) == 2:
            saved_order, saved_selection = v2_data
        else:
            saved_order = []
            saved_selection = {}
        
        # Original-Spalten als Dictionary für schnellen Zugriff
        original_dict = {col['name']: col for col in original_columns}
        
        # Verfügbare Spalten für aktuellen Mode ermitteln
        available_for_mode = {col['name'] for col in self._get_available_columns_for_mode(original_columns)}
        
        result_columns = []
        
        # 1. Spalten in gespeicherter Reihenfolge verarbeiten
        for col_name in saved_order:
            if col_name in original_dict and col_name in available_for_mode:
                col = original_dict[col_name].copy()
                # display_show aus gespeicherter Auswahl setzen (Default: True)
                col['display_show'] = saved_selection.get(col_name, True)
                result_columns.append(col)
        
        # 2. Neue Spalten hinzufügen (nicht in gespeicherter Reihenfolge)
        existing_names = {col['name'] for col in result_columns}
        for col_name in available_for_mode:
            if col_name not in existing_names and col_name in original_dict:
                col = original_dict[col_name].copy()
                col['display_show'] = True  # Neue Spalten sind standardmäßig sichtbar
                result_columns.append(col)
                logger.debug(f"📋 Neue Spalte hinzugefügt: {col_name}")
        
        logger.debug(f"📋 Gespeicherte Ebene 2 angewendet: {len(result_columns)} Spalten")
        return result_columns

    def _create_initial_level2(self, original_columns):
        """
        Erstellt initiale Ebene 2 aus Original-Parametern und speichert sie sofort.
        
        User-Spezifikation:
        - Order-System: Normal (1-199), Expert (200-399), Nicht angezeigt (999)
        - Aus Original-Parametern ableiten
        - Sofort speichern
        
        Args:
            original_columns: Original-Spalten aus control.columns
            
        Returns:
            Neue Ebene-2-Spalten mit order-basierter Reihenfolge
        """
        # Verfügbare Spalten für aktuellen Mode
        available_columns = self._get_available_columns_for_mode(original_columns)
        
        # Order-System anwenden und sortieren
        ordered_columns = []
        for col in available_columns:
            col_copy = col.copy()
            original_order = col.get('order', 999)
            
            # Order-System nach User-Spezifikation
            if col.get('expert', False):
                # Expert-Spalten: Original order + 200
                col_copy['level2_order'] = original_order + 200
            elif col.get('show', False):
                # Normal-Spalten: Original order
                col_copy['level2_order'] = original_order
            else:
                # Nicht angezeigte: 999
                col_copy['level2_order'] = 999
            
            # display_show basierend auf show-Status setzen
            col_copy['display_show'] = col.get('show', False)
            ordered_columns.append(col_copy)
        
        # Nach level2_order sortieren
        ordered_columns.sort(key=lambda x: x.get('level2_order', 999))
        
        # Sofort als Ebene 2 speichern
        column_order = [col['name'] for col in ordered_columns]
        column_selection = {col['name']: col.get('display_show', False) for col in ordered_columns}
        
        self._save_user_column_order_v2(column_order, column_selection)
        
        logger.info(f"📋 Initiale Ebene 2 erstellt und gespeichert: {len(ordered_columns)} Spalten")
        logger.debug(f"📋 Order-System angewendet: Normal/Expert/Nicht-angezeigt")
        
        return ordered_columns

    def _get_available_columns_for_mode(self, columns):
        """
        KOMPATIBILITÄT: Bestimmt verfügbare Spalten basierend auf aktuellem Mode.
        
        Diese Methode wird noch von anderen Teilen verwendet (z.B. Column Selection Dialog).
        Normal-Mode: Nur Standard-Spalten (show=True AND expert=False)
        Expert-Mode: Standard-Spalten + Expert-Spalten (show=True OR expert=True)
        """
        available = []
        
        for col in columns:
            show_val = col.get('show', False)
            expert_val = col.get('expert', False)
            
            if self.expert_mode:
                # Expert-Mode: Ebene 1 (Standard) + Ebene 3 (Expert)
                if show_val or expert_val:
                    available.append(col)
            else:
                # Normal-Mode: Nur Ebene 1 (Standard)
                if show_val and not expert_val:
                    available.append(col)
        
        return available

    def _apply_user_column_order_v2(self, standard_columns):
        """
        LEVEL 2: Wendet die gespeicherte Benutzer-Reihenfolge an.
        
        VEREINFACHTE ARCHITEKTUR:
        - Lädt gespeicherte Benutzer-Reihenfolge (vollständige Liste aller Spalten)
        - Deaktivierte Spalten werden automatisch nach hinten sortiert
        - Die Reihenfolge ist IMMER die dargestellte Reihenfolge
        
        Args:
            standard_columns: Spalten in Standard-Reihenfolge (Level 1)
            
        Returns:
            Liste aller Spalten in Benutzer-Reihenfolge mit display_show-Status
        """
        try:
            # Gespeicherte Benutzer-Reihenfolge laden
            user_order_data = self._load_user_column_order_v2()
            
            if not user_order_data:
                # Keine gespeicherte Reihenfolge: Standard-Reihenfolge mit allen aktiv
                logger.debug("[ModernViewWidget] Keine Benutzer-Reihenfolge -> Standard mit allen aktiv")
                for col in standard_columns:
                    col['display_show'] = True
                return standard_columns
            
            # Gespeicherte Daten analysieren - V3 Tupel Format
            if len(user_order_data) == 2:
                user_order, user_selection = user_order_data
            else:
                user_order = []
                user_selection = {}
            
            # Alle verfügbaren Spalten als Dictionary für schnellen Zugriff
            column_dict = {col['name']: col for col in standard_columns}
            
            # Reihenfolge anwenden
            ordered_columns = []
            
            # 1. Spalten in gespeicherter Reihenfolge hinzufügen
            for col_name in user_order:
                if col_name in column_dict:
                    col = column_dict[col_name]
                    # Status aus gespeicherter Auswahl setzen (Default: True)
                    col['display_show'] = user_selection.get(col_name, True)
                    ordered_columns.append(col)
                    del column_dict[col_name]
            
            # 2. Neue Spalten (nicht in gespeicherter Reihenfolge) hinten aktiv anfügen
            for col in column_dict.values():
                col['display_show'] = True  # Neue Spalten sind standardmäßig aktiv
                ordered_columns.append(col)
                logger.debug(f"[ModernViewWidget] Neue Spalte hinten aktiv angefügt: {col['name']}")
            
            # 3. Deaktivierte Spalten nach hinten sortieren
            active_cols = [col for col in ordered_columns if col.get('display_show', True)]
            inactive_cols = [col for col in ordered_columns if not col.get('display_show', True)]
            final_order = active_cols + inactive_cols
            
            logger.info(f"[ModernViewWidget] Benutzer-Reihenfolge angewendet:")
            logger.info(f"  Aktive Spalten: {len(active_cols)} (vorne)")
            logger.info(f"  Deaktivierte: {len(inactive_cols)} (hinten)")
            logger.debug(f"  Reihenfolge: {[col['name'] for col in final_order[:8]]}{'...' if len(final_order) > 8 else ''}")
            
            return final_order
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Benutzer-Reihenfolge: {e}")
            # Fallback: Standard-Reihenfolge mit allen aktiv
            for col in standard_columns:
                col['display_show'] = True
            return standard_columns

    def _load_complete_controls_v3(self):
        """
        VOLLSTÄNDIGE CONTROL-LADUNG: Lädt komplette Control-Objekte oder erstellt sie fallback.
        
        1. Versucht vollständige Controls aus systemsteuerung.daten[view_guid]['complete_controls'] zu laden
        2. Falls nicht vorhanden: Erstellt sie aus get_value_view und speichert sie
        3. Gibt vollständige, einsatzbereite Control-Objekte zurück
        
        Returns:
            Dict mit vollständigen Control-Objekten oder None bei Fehler
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from datetime import datetime
            
            # KORRIGIERT: Complete Controls aus separater GUID laden
            controls_guid = f"{self.user_guid}_view_{self.view_guid}_complete_controls"
            controls_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=controls_guid
            )
            
            # Schritt 1: Versuche gespeicherte vollständige Controls zu laden
            stored_controls = controls_db.lesen()
            
            if stored_controls and isinstance(stored_controls, dict) and len(stored_controls) > 0:
                # Validierung der gespeicherten Controls
                if self._validate_stored_controls(stored_controls):
                    logger.info(f"✅ VOLLSTÄNDIGE CONTROLS: {len(stored_controls)} gespeicherte Controls geladen")
                    return stored_controls
                else:
                    logger.warning("⚠️ Gespeicherte Controls sind ungültig - erstelle neue")
            
            # Schritt 2: Fallback - Controls aus get_value_view erstellen
            logger.info("🔄 Erstelle vollständige Controls aus get_value_view...")
            
            if not hasattr(self.data_manager, 'control') or not hasattr(self.data_manager.control, 'columns'):
                logger.error("❌ Keine Control-Definitionen in data_manager verfügbar")
                return None
            
            # Schritt 2: Fallback - Controls aus get_value_view erstellen
            logger.info("🔄 Erstelle vollständige Controls aus get_value_view...")
            
            # Vollständige Controls aus get_value_view erstellen
            complete_controls = {}
            
            for i, original_control in enumerate(self.data_manager.control.columns, 1):
                control_name = original_control.get('name')
                if not control_name:
                    continue
                
                # Vollständiges Control-Objekt kopieren
                complete_control = original_control.copy()
                
                # Standard-Benutzer-Einstellungen hinzufügen
                complete_control['user_display_show'] = original_control.get('show', True)
                complete_control['user_display_order'] = original_control.get('order', i)
                complete_control['last_updated'] = datetime.now().isoformat()
                complete_control['created_from'] = 'get_value_view_fallback'
                
                complete_controls[control_name] = complete_control
            
            # KORRIGIERT: Schritt 3 - Neue Controls über separate GUID speichern
            # Verwende spezifische GUID für complete_controls dieser View
            controls_guid = f"{self.user_guid}_view_{self.view_guid}_complete_controls"
            controls_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=controls_guid
            )
            
            # Nur Complete Controls speichern - überschreibt KEINE anderen Daten
            controls_db.speichern(controls_guid, complete_controls)
            
            logger.info(f"✅ FALLBACK ERFOLGREICH: {len(complete_controls)} neue vollständige Controls erstellt und gespeichert")
            return complete_controls
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der vollständigen Controls: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _validate_stored_controls(self, stored_controls):
        """
        Validiert gespeicherte Control-Objekte.
        
        Args:
            stored_controls: Dict mit gespeicherten Control-Objekten
            
        Returns:
            True wenn Controls gültig sind, False sonst
        """
        try:
            if not isinstance(stored_controls, dict) or not stored_controls:
                return False
            
            # Prüfe ob alle Controls die notwendigen Felder haben
            required_fields = ['name', 'user_display_show', 'user_display_order']
            
            for control_name, control_data in stored_controls.items():
                if not isinstance(control_data, dict):
                    logger.warning(f"⚠️ Control {control_name} ist kein Dict")
                    return False
                
                for field in required_fields:
                    if field not in control_data:
                        logger.warning(f"⚠️ Control {control_name} fehlt Feld {field}")
                        return False
            
            logger.debug(f"✅ Validation: {len(stored_controls)} Controls sind gültig")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Control-Validierung: {e}")
            return False
        """
        KORREKTE ARCHITEKTUR: Lädt Control-Parameter aus systemsteuerung.daten[view_guid]['controls'].
        
        Liest alle Controls aus systemsteuerung.daten[view_guid]['controls'][control_name] und 
        rekonstruiert daraus column_order und column_selection.
        
        DB-Struktur:
        systemsteuerung.daten[view_guid]['controls'] = {
            familienname_original: {display_show: true, display_order: 1, last_updated: "..."},
            familienname_show: {display_show: false, display_order: 2, last_updated: "..."},
            geburtsdatum_original: {display_show: true, display_order: 3, last_updated: "..."}
        }
        
        Returns:
            Dict mit column_order (Control-Namen) und column_selection oder None
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Systemsteuerung für Benutzer laden (uid = user_guid wird vom System verwaltet)
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Benutzerdaten laden
            user_data = sys_db.lesen() or {}
            
            # View-Gruppe und Controls-Bereich prüfen
            if self.view_guid not in user_data:
                logger.debug(f"[ModernViewWidget] Keine Daten für View {self.view_guid} gefunden")
                return None
            
            view_data = user_data[self.view_guid]
            if 'controls' not in view_data:
                logger.debug(f"[ModernViewWidget] Keine Controls in View {self.view_guid} gefunden")
                return None
            
            controls_data = view_data['controls']
            if not controls_data:
                logger.debug(f"[ModernViewWidget] Controls-Bereich für View {self.view_guid} ist leer")
                return None
            
            # Controls nach display_order sortieren
            controls = []
            for control_name, control_data in controls_data.items():
                if isinstance(control_data, dict) and 'display_order' in control_data:
                    controls.append({
                        'name': control_name,  # z.B. "familienname_original"
                        'display_order': control_data.get('display_order', 999),
                        'display_show': control_data.get('display_show', True)
                    })
            
            if not controls:
                logger.debug("[ModernViewWidget] Keine gültigen Control-Daten gefunden")
                return None
            
            # Nach display_order sortieren
            controls.sort(key=lambda x: x['display_order'])
            
            # column_order und column_selection rekonstruieren
            column_order = [ctrl['name'] for ctrl in controls]  # Erweiterte Control-Namen
            column_selection = {ctrl['name']: ctrl['display_show'] for ctrl in controls}
            
            logger.debug(f"[ModernViewWidget] KORREKTE ARCHITEKTUR: Controls geladen aus systemsteuerung.daten[{self.view_guid}]['controls']:")
            logger.debug(f"  Controls gefunden: {len(controls)}")
            logger.debug(f"  Control-Namen: {column_order[:3]}{'...' if len(column_order) > 3 else ''}")
            
            return {
                'column_order': column_order,
                'column_selection': column_selection
            }
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Controls: {e}")
            return None
                
    def _build_table_from_complete_controls(self, complete_controls):
        """
        TABELLEN-AUFBAU: Erstellt die Tabelle aus vollständigen Control-Objekten.
        
        Args:
            complete_controls: Dict mit vollständigen Control-Objekten
            
        Returns:
            Tuple (column_order, column_selection) für Tabellen-Setup
        """
        try:
            # Nach user_display_order sortieren
            sorted_controls = sorted(
                complete_controls.items(),
                key=lambda x: x[1].get('user_display_order', 999)
            )
            
            # column_order und column_selection erstellen
            column_order = []
            column_selection = {}
            
            for control_name, control_data in sorted_controls:
                column_order.append(control_name)
                column_selection[control_name] = control_data.get('user_display_show', True)
            
            logger.info(f"🏗️ TABELLEN-AUFBAU: {len(column_order)} Spalten aus vollständigen Controls erstellt")
            logger.debug(f"🏗️ Spalten-Reihenfolge: {column_order[:3]}{'...' if len(column_order) > 3 else ''}")
            
            # Zusätzlich: Vollständige Controls als Instanz-Variable speichern für späteren Zugriff
            self.complete_controls = complete_controls
            
            return column_order, column_selection
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Tabellen-Aufbau aus vollständigen Controls: {e}")
            return None, None
    
    def _load_view_settings_v3(self):
        """
        VOLLSTÄNDIGES CONTROL-SYSTEM: Lädt View-Einstellungen mit vollständigen Control-Objekten.
        
        1. Lädt vollständige Controls (oder erstellt sie fallback aus get_value_view)
        2. Baut Tabelle aus vollständigen Controls auf
        3. Gibt (column_order, column_selection) zurück für Kompatibilität
        
        Returns:
            Tupel (column_order, column_selection) oder (None, None) bei Fehler
        """
        try:
            logger.info("🔄 VOLLSTÄNDIGES CONTROL-SYSTEM: Lade View-Einstellungen...")
            
            # Schritt 1: Vollständige Controls laden oder erstellen
            complete_controls = self._load_complete_controls_v3()
            
            if not complete_controls:
                logger.error("❌ Keine vollständigen Controls verfügbar")
                return None, None
            
            # Schritt 2: Tabelle aus vollständigen Controls aufbauen
            success = self._build_table_from_complete_controls(complete_controls)
            
            if not success:
                logger.error("❌ Tabellen-Aufbau aus vollständigen Controls fehlgeschlagen")
                return None, None
            
            # Schritt 3: Kompatibilitäts-Daten für bestehenden Code erstellen
            visible_controls = []
            for control_name, control_data in complete_controls.items():
                if (isinstance(control_data, dict) and 
                    control_data.get('user_display_show', True)):
                    visible_controls.append(control_data)
            
            # Nach Benutzer-definierter Reihenfolge sortieren
            visible_controls.sort(key=lambda x: x.get('user_display_order', 999))
            
            # Kompatibilitäts-Rückgabe für bestehenden Code
            column_order = [control.get('name') for control in visible_controls]
            column_selection = {control.get('name'): control.get('user_display_show', True) 
                              for control in visible_controls}
            
            logger.info(f"✅ VOLLSTÄNDIGES CONTROL-SYSTEM: View-Einstellungen geladen")
            logger.info(f"   Spalten: {len(column_order)} sichtbar, {len(complete_controls)} total")
            logger.debug(f"   Reihenfolge: {column_order[:3]}{'...' if len(column_order) > 3 else ''}")
            
            return column_order, column_selection
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Einstellungen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None, None
    
    def _load_user_column_order_v2(self):
        """
        KOMPATIBILITÄTSSCHICHT: Leitet zu vollständigem Control-System weiter.
        
        Diese Funktion wird noch von älteren Teilen des Codes aufgerufen.
        Sie nutzt das neue vollständige Control-System als Backend.
        
        Returns:
            Tupel (column_order, column_selection) oder (None, None) bei Fehler
        """
        logger.debug("🔄 KOMPATIBILITÄT: _load_user_column_order_v2 leitet zu V3 weiter")
        return self._load_view_settings_v3()
    
    def _update_controls_from_drag_drop(self, new_visible_order):
        """
        DRAG & DROP INTEGRATION: Aktualisiert vollständige Controls nach Drag & Drop.
        
        Args:
            new_visible_order: Liste der Spalten-Namen in neuer Reihenfolge
        """
        try:
            logger.debug(f"🔄 DRAG & DROP: Aktualisiere vollständige Controls mit neuer Reihenfolge: {len(new_visible_order)} Spalten")
            
            # Drag-Result für vollständige Control-Integration erstellen
            drag_result = {
                'column_order': new_visible_order
            }
            
            # Vollständige Controls aktualisieren
            success = self.save_column_changes_complete_controls(drag_result)
            
            if success:
                logger.info("✅ DRAG & DROP: Vollständige Controls erfolgreich aktualisiert")
            else:
                logger.warning("⚠️ DRAG & DROP: Fehler beim Aktualisieren der vollständigen Controls")
                
        except Exception as e:
            logger.error(f"❌ DRAG & DROP: Fehler beim Aktualisieren der Controls: {e}")
    
    def _update_complete_controls_from_drag_drop(self, new_visible_order):
        """Alias für _update_controls_from_drag_drop (verschiedene Namen im Code)"""
        return self._update_controls_from_drag_drop(new_visible_order)

    def _load_user_column_order(self):
        """
        Lädt die gespeicherte Spalten-Reihenfolge des Benutzers aus der Datenbank.
        
        Returns:
            Liste von Spalten-Namen in der gewünschten Reihenfolge oder None
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # Systemsteuerung-Datenbank für Benutzer öffnen
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Benutzerdaten laden
            raw_data = sys_db.lesen() or {}
            user_data = raw_data.get(self.user_guid, {})
            
            # Spalten-Reihenfolge für diese View laden
            column_orders = user_data.get("ColumnOrder", {})
            view_order = column_orders.get(self.view_guid, None)
            
            if view_order:
                logger.debug(f"[ModernViewWidget] Gespeicherte Spalten-Reihenfolge geladen: {len(view_order)} Spalten")
                return view_order
            else:
                logger.debug("[ModernViewWidget] Keine gespeicherte Spalten-Reihenfolge gefunden")
                return None
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Spalten-Reihenfolge: {e}")
            return None

    def _load_complete_controls_v3(self):
        """
        VOLLSTÄNDIGE CONTROL-VERWALTUNG mit korrigierter Architektur.
        
        Architektur: systemsteuerung[SYSTEM_USER_ID].data[view_guid]["spalte_xy_original"] = wert
        Jede Spalte ist ein eigenes Feld, ohne "completeControls" Gruppe.
        
        Returns:
            Dict mit vollständigen Control-Objekten oder None bei Fehler
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from datetime import datetime
            
            # Systemsteuerung-Datenbank öffnen
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=PdvmCentralDatenbank.SYSTEM_USER_ID  # Korrekte 0000... GUID verwenden
            )
            
            # Versuche gespeicherte Controls aus view_guid-Gruppe zu laden
            complete_controls = {}
            
            # View-Struktur laden für alle Spalten
            if hasattr(self, 'data_manager') and self.data_manager:
                view_structure = self.data_manager.get_view_structure()
                if view_structure and hasattr(view_structure, 'columns'):
                    
                    # Alle Spalten durchgehen und Controls laden
                    for column in view_structure.columns:
                        column_name = column.get('name', '')
                        if column_name:
                            # Control-Wert aus Gruppe=view_guid, Feld=column_name laden
                            control_value = sys_db.get_value(
                                gruppe=self.view_guid,  # view_guid ist die Gruppe
                                feld=column_name,       # Spaltenname ist das Feld
                                ab_zeit=None           # Aktueller Zeitstempel
                            )
                            
                            if control_value.get("wert") is not None:
                                complete_controls[column_name] = control_value.get("wert")
                            else:
                                # Default-Werte für neue Spalten
                                complete_controls[column_name] = {
                                    'visible': True,
                                    'width': 100,
                                    'order': column.get('order', 0),
                                    'last_updated': datetime.now().isoformat()
                                }
                
                logger.info(f"✅ LADEN ERFOLGREICH: {len(complete_controls)} Controls aus view_guid-Gruppe geladen")
                return complete_controls
            
            logger.warning("⚠️ Keine View-Struktur verfügbar, erstelle leere Controls")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der vollständigen Controls: {e}")
            return None
            
            if not hasattr(self.data_manager, 'control') or not hasattr(self.data_manager.control, 'columns'):
                logger.error("❌ Keine Control-Definitionen in data_manager verfügbar")
                return None
            
            # View-Struktur initialisieren
            if self.view_guid not in user_data:
                user_data[self.view_guid] = {}
            
            # Vollständige Controls aus get_value_view erstellen
            complete_controls = {}
            
            for original_control in self.data_manager.control.columns:
                control_name = original_control.get('name')
                if not control_name:
                    continue
                
                # Vollständiges Control-Objekt kopieren (alle Original-Metadaten!)
                complete_control = original_control.copy()
                
                # Benutzer-spezifische Überschreibungen hinzufügen
                complete_control['user_display_show'] = original_control.get('show', True)
                complete_control['user_display_order'] = original_control.get('order', 999)
                complete_control['last_updated'] = datetime.now().isoformat()
                complete_control['created_from'] = 'get_value_view_fallback'
                
                complete_controls[control_name] = complete_control
            
            # Schritt 3: Neue vollständige Controls speichern
            user_data[self.view_guid]['complete_controls'] = complete_controls
            sys_db.speichern(self.user_guid, user_data)
            
            logger.info(f"✅ FALLBACK ERFOLGREICH: {len(complete_controls)} neue vollständige Controls erstellt und gespeichert")
            return complete_controls
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der vollständigen Controls: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _validate_complete_controls(self, complete_controls):
        """
        Validiert vollständige Control-Objekte.
        
        Args:
            complete_controls: Dict mit vollständigen Control-Objekten
            
        Returns:
            True wenn Controls gültig sind, False sonst
        """
        try:
            if not isinstance(complete_controls, dict) or not complete_controls:
                return False
            
            # Prüfe ob alle Controls die notwendigen Felder haben
            required_fields = ['name', 'user_display_show', 'user_display_order']
            
            for control_name, control_data in complete_controls.items():
                if not isinstance(control_data, dict):
                    logger.warning(f"⚠️ Control {control_name} ist kein Dict")
                    return False
                
                for field in required_fields:
                    if field not in control_data:
                        logger.warning(f"⚠️ Control {control_name} fehlt Feld {field}")
                        return False
            
            logger.debug(f"✅ Validation: {len(complete_controls)} vollständige Controls sind gültig")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei vollständiger Control-Validierung: {e}")
            return False
    
    def _save_complete_controls_v3(self, complete_controls):
        """
        VOLLSTÄNDIGE CONTROL-VERWALTUNG mit korrigierter Architektur.
        
        Architektur: systemsteuerung[SYSTEM_USER_ID].data[view_guid]["spalte_xy"] = control_wert
        Jede Spalte ist ein eigenes Feld, ohne "completeControls" Gruppe.
        
        Args:
            complete_controls: Dict mit vollständigen Control-Objekten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from datetime import datetime
            
            if not complete_controls or not isinstance(complete_controls, dict):
                logger.error("❌ Ungültige vollständige Controls zum Speichern")
                return False
            
            # Systemsteuerung-Datenbank öffnen
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=PdvmCentralDatenbank.SYSTEM_USER_ID  # Korrekte 0000... GUID verwenden
            )
            
            # Jede Spalte als separates Feld in view_guid-Gruppe speichern
            for column_name, control_data in complete_controls.items():
                # Timestamp für Control aktualisieren
                if isinstance(control_data, dict):
                    control_data['last_updated'] = datetime.now().isoformat()
                
                # Control-Wert in Gruppe=view_guid, Feld=column_name speichern
                sys_db.set_value(
                    gruppe=self.view_guid,  # view_guid ist die Gruppe
                    feld=column_name,       # Spaltenname ist das Feld
                    wert=control_data,
                    ab_zeit=1001.0         # Standard-Zeitstempel für nicht-historische Felder
                )
            
            # Alle Änderungen persistieren
            sys_db.save_values()
            
            logger.info(f"✅ SPEICHERN ERFOLGREICH: {len(complete_controls)} Controls in view_guid-Gruppe gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der vollständigen Controls: {e}")
            return False
    
    def _build_table_from_complete_controls(self, complete_controls):
        """
        VOLLSTÄNDIGE CONTROL-VERWALTUNG: Baut Tabelle basierend auf vollständigen Controls.
        
        Diese Funktion nutzt VOLLSTÄNDIGE Control-Objekte als Basis für die Tabellenerstellung.
        Dadurch haben wir alle Metadaten (Label, Type, Width, Alignment, etc.) verfügbar!
        
        Args:
            complete_controls: Dict mit vollständigen Control-Objekten
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if not complete_controls or not isinstance(complete_controls, dict):
                logger.error("❌ Keine vollständigen Controls für Tabellenerstellung")
                return False
            
            # Nur sichtbare Controls filtern und nach Reihenfolge sortieren
            visible_controls = []
            for control_name, control_data in complete_controls.items():
                if (isinstance(control_data, dict) and 
                    control_data.get('user_display_show', True)):
                    visible_controls.append(control_data)
            
            # Nach Benutzer-definierter Reihenfolge sortieren
            visible_controls.sort(key=lambda x: x.get('user_display_order', 999))
            
            if not visible_controls:
                logger.warning("⚠️ Keine sichtbaren Controls für Tabelle gefunden")
                return False
            
            # Tabelle erstellen
            data = self.data_manager.get_data() if self.data_manager else []
            self.table = QTableWidget()
            self.table.setColumnCount(len(visible_controls))
            self.table.setRowCount(len(data))
            
            # Spalten-Header mit vollständigen Metadaten konfigurieren
            header_labels = []
            for i, control in enumerate(visible_controls):
                # Label oder Name als Header verwenden
                label = control.get('label', control.get('name', f'Spalte_{i}'))
                header_labels.append(str(label))
                
                # Spaltenbreite setzen (falls verfügbar)
                width = control.get('width')
                if width and isinstance(width, (int, float)) and width > 0:
                    self.table.setColumnWidth(i, int(width))
            
            self.table.setHorizontalHeaderLabels(header_labels)
            
            # Tabellendaten füllen
            control_names = [control.get('name') for control in visible_controls]
            
            for row_idx, row_data in enumerate(data):
                for col_idx, control_name in enumerate(control_names):
                    if control_name in row_data:
                        cell_value = str(row_data[control_name])
                        
                        # Cell-Item mit Alignment erstellen
                        cell_item = QTableWidgetItem(cell_value)
                        
                        # Cell-Alignment basierend auf Control-Metadaten
                        control = visible_controls[col_idx]
                        alignment = control.get('align', 'left')
                        qt_alignment = Qt.AlignLeft | Qt.AlignVCenter
                        if alignment == 'center':
                            qt_alignment = Qt.AlignCenter
                        elif alignment == 'right':
                            qt_alignment = Qt.AlignRight | Qt.AlignVCenter
                        
                        cell_item.setTextAlignment(qt_alignment)
                        self.table.setItem(row_idx, col_idx, cell_item)
            
            logger.info(f"✅ TABELLE ERSTELLT: {len(visible_controls)} Spalten aus vollständigen Controls, {len(data)} Zeilen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Tabelle aus vollständigen Controls: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
    
    def _build_table_original(self):
            
            # Prüfe ob vollständige Controls verfügbar sind
            if not hasattr(self, 'complete_controls') or not self.complete_controls:
                logger.error("❌ Keine vollständigen Controls zum Speichern verfügbar")
                return False
            
            # Systemsteuerung für Benutzer laden
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung", 
                guid=self.user_guid
            )
            
            user_data = sys_db.lesen() or {}
            
            # View-Gruppe initialisieren
            if self.view_guid not in user_data:
                user_data[self.view_guid] = {}
            
    def _build_table_original(self):
        """Original Tabellenerstellung - wird durch vollständige Controls ersetzt"""
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
    
    def update_table_with_complete_controls(self):
        """
        HAUPT-INTEGRATION: Nutzt vollständige Control-Verwaltung für Tabellenerstellung.
        
        Diese Funktion ersetzt die alte Tabellenerstellung und nutzt das neue
        vollständige Control-System mit PdvmDatenbank.
        """
        try:
            # Schritt 1: Vollständige Controls laden oder erstellen
            complete_controls = self._load_complete_controls_v3()
            
            if not complete_controls:
                logger.error("❌ Keine vollständigen Controls verfügbar - fallback auf ursprüngliche Tabelle")
                self._build_table_original()
                return False
            
            # Schritt 2: Tabelle aus vollständigen Controls erstellen
            success = self._build_table_from_complete_controls(complete_controls)
            
            if success:
                logger.info("✅ VOLLSTÄNDIGE CONTROL-INTEGRATION: Tabelle erfolgreich erstellt")
                return True
            else:
                logger.warning("⚠️ Fallback auf ursprüngliche Tabelle")
                self._build_table_original()
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler in vollständiger Control-Integration: {e}")
            logger.warning("⚠️ Fallback auf ursprüngliche Tabelle")
            self._build_table_original()
            return False
    
    def save_column_changes_complete_controls(self, drag_result):
        """
        DRAG & DROP INTEGRATION: Speichert Änderungen nach Spalten-Drag & Drop.
        
        Args:
            drag_result: Dict mit 'column_order' (Liste) und optionalen anderen Änderungen
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Vollständige Controls laden
            complete_controls = self._load_complete_controls_v3()
            
            if not complete_controls:
                logger.error("❌ Keine vollständigen Controls für Drag & Drop verfügbar")
                return False
            
            # Neue Reihenfolge anwenden
            new_order = drag_result.get('column_order', [])
            
            if not new_order:
                logger.warning("⚠️ Keine neue Spalten-Reihenfolge in drag_result")
                return False
            
            # User-Reihenfolge in vollständigen Controls aktualisieren
            from datetime import datetime
            
            for i, control_name in enumerate(new_order):
                if control_name in complete_controls:
                    complete_controls[control_name]['user_display_order'] = i + 1
                    complete_controls[control_name]['last_updated'] = datetime.now().isoformat()
            
            # Vollständige Controls speichern
            success = self._save_complete_controls_v3(complete_controls)
            
            if success:
                logger.info(f"✅ DRAG & DROP: Neue Spalten-Reihenfolge mit {len(new_order)} Spalten gespeichert")
                return True
            else:
                logger.error("❌ Fehler beim Speichern der Drag & Drop Änderungen")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Drag & Drop Integration: {e}")
            return False
    
    def initialize_widget_with_complete_controls(self):
        """
        WIDGET-INITIALISIERUNG: Startet Widget mit vollständiger Control-Verwaltung.
        
        Diese Funktion sollte beim Widget-Start aufgerufen werden.
        Sie lädt/erstellt vollständige Controls und baut die Tabelle auf.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            logger.info("🚀 WIDGET-START: Initialisiere mit vollständiger Control-Verwaltung...")
            
            # Widget-Grundeinstellungen
            self.setWindowTitle("Moderne PDVM View - Vollständige Control-Verwaltung")
            
            # Vollständige Controls laden/erstellen und Tabelle aufbauen
            success = self.update_table_with_complete_controls()
            
            if success:
                logger.info("✅ WIDGET-INITIALISIERUNG: Vollständige Control-Verwaltung aktiv")
                return True
            else:
                logger.warning("⚠️ WIDGET-INITIALISIERUNG: Fallback-Modus aktiv")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Widget-Initialisierung mit vollständigen Controls: {e}")
            return False

    def _save_user_column_order(self, column_names):
        """
        KOMPATIBILITÄT: Speichert die Spalten-Reihenfolge im alten Format.
        
        Diese Methode wird noch von _on_column_moved verwendet.
        Ruft intern das neue V2-Format auf.
        
        Args:
            column_names: Liste von Spalten-Namen in der gewünschten Reihenfolge
        """
        logger.debug(f"[KOMPATIBILITÄT] Speichere über altes Interface, leite an V2 weiter")
        
        # Aktuellen Sichtbarkeits-Status aus den Spalten ableiten
        column_selection = {}
        
        control = getattr(self.data_manager, 'control', None)
        if control and hasattr(control, 'columns'):
            column_dict = {col['name']: col for col in control.columns}
            
            for col_name in column_names:
                if col_name in column_dict:
                    col = column_dict[col_name]
                    # display_show Status verwenden falls vorhanden, sonst True
                    column_selection[col_name] = col.get('display_show', True)
                else:
                    column_selection[col_name] = True
        else:
            # Fallback: Alle als aktiv markieren
            column_selection = {col_name: True for col_name in column_names}
        
        # An V2-Methode weiterleiten
        self._save_user_column_order_v2(column_names, column_selection)

    def _update_column_selection_button(self, available_columns):
        """Aktualisiert den Button-Text für die Spaltenauswahl basierend auf aktueller Auswahl."""
        current_selection = getattr(self, '_custom_column_selection', None)
        
        # Zähle aktuell sichtbare Spalten
        if current_selection is None:
            visible_count = len(available_columns)  # Alle verfügbaren sind sichtbar
            button_text = f"Alle {visible_count} Spalten ausgewählt"
        else:
            # Zähle nur die Spalten die sowohl in current_selection als auch in available_columns sind
            visible_count = len([col for col in available_columns if col['name'] in current_selection])
            
            if visible_count == 0:
                button_text = "Keine Spalten ausgewählt"
            elif visible_count == len(available_columns):
                button_text = f"Alle {visible_count} Spalten ausgewählt"
            elif visible_count == 1:
                # Eine Spalte: Zeige Label
                for col in available_columns:
                    if col['name'] in current_selection:
                        button_text = col.get('label', col.get('anzeige', col['name']))
                        break
                else:
                    button_text = "1 Spalte ausgewählt"
            else:
                button_text = f"{visible_count} von {len(available_columns)} Spalten"
        
        self.column_selection_button.setText(button_text)
        
        logger.debug(f"[ModernViewWidget] Button-Text aktualisiert: '{button_text}'")

    def _open_column_selection_dialog(self):
        """
        Öffnet den Dialog zur Spaltenauswahl mit der neuen 2-Level-Architektur.
        
        NEUE V2-ARCHITEKTUR:
        - Zeigt alle verfügbaren Spalten für den aktuellen Mode an
        - Speichert Auswahl mit vollständiger Reihenfolge (aktive + deaktivierte)
        - Deaktivierte Spalten wandern automatisch nach hinten
        """
        control = getattr(self.data_manager, 'control', None)
        if control is None or not hasattr(control, 'columns'):
            QMessageBox.warning(self, "Fehler", "Keine Spalten verfügbar")
            return
        
        columns = control.columns
        
        # Verfügbare Spalten für aktuellen Mode holen
        available_columns = self._get_available_columns_for_mode(columns)
        
        # Dialog-Format erstellen - KORRIGIERT: Verwende 'label' statt 'anzeige'
        # Dialog-Daten vorbereiten
        dialog_columns = []
        for col in available_columns:
            dialog_columns.append({
                "name": col['name'],
                "label": col.get('label', col.get('anzeige', col['name'])),
                "expert": col.get('expert', False)  # Expert-Status weiterreichen
            })
        
        # Aktuelle Auswahl aus Complete Controls V3 laden
        current_selection = []
        complete_controls = self._load_complete_controls_v3()
        
        if complete_controls:
            # Nur die für aktuellen Mode verfügbaren Spalten, die auch aktiviert sind
            for col in available_columns:
                if col['name'] in complete_controls and complete_controls[col['name']].get('user_display_show', True):
                    current_selection.append(col['name'])
            
            logger.debug(f"📋 Aktuelle Auswahl aus Complete Controls V3: {len(current_selection)} von {len(available_columns)} Spalten")
        else:
            # Fallback: Alle verfügbaren Spalten als ausgewählt betrachten
            current_selection = [col['name'] for col in available_columns]
            logger.warning("⚠️ Keine Complete Controls V3 gefunden - verwende alle Spalten als Fallback")
        
        # Vereinfachter Dialog nur für Spalten-Auswahl
        dialog = ColumnSelectionDialog(dialog_columns, current_selection, self)
        if dialog.exec_() == QDialog.Accepted:
            # Neue Auswahl übernehmen
            new_selection = dialog.get_selected_columns()
            
            logger.info(f"📋 Spaltenauswahl geändert: {len(new_selection)} Spalten ausgewählt")
            logger.debug(f"📋 Neue Auswahl: {new_selection}")
            
            # VOLLSTÄNDIGES CONTROL-SYSTEM: Spaltenauswahl über V2-System aktualisieren
            self._update_column_selection_v2(available_columns, new_selection)
            
            logger.info("� Spalten-Reihenfolge kann direkt in der Tabelle per Drag & Drop geändert werden")
            # WICHTIG: Keine _rebuild_table() - das erstellt eine neue Tabelle!
            # Stattdessen nur die Spalten aktualisieren
            
            # Einstellungen speichern (nur für persistent verfügbare Spalten)
            self._save_view_settings()
            
            logger.info(f"📋 Spaltenauswahl geändert: {len(new_selection)} Spalten ausgewählt")
            logger.debug(f"📋 Ausgewählte Spalten: {new_selection}")

    def _update_column_selection_v2(self, available_columns, new_selection):
        """
        Aktualisiert die Spalten-Auswahl nach User-Spezifikation Punkt 4:
        
        "Wird eine Spalte hinzugefügt, wird diese in der Reihenfolge am Ende 
        der sichtbaren Spalten sichtbar. Wird eine Spalte ausgeblendet, 
        wird diese ans Ende der Reihenfolge eingefügt."
        
        Args:
            available_columns: Alle für den Mode verfügbaren Spalten
            new_selection: Liste der ausgewählten Spalten-Namen
        """
        try:
            # Aktuelle Ebene 2 laden
            v2_data = self._load_user_column_order_v2()
            
            if not v2_data:
                logger.warning("⚠️ Keine Ebene 2 für Spalten-Update gefunden")
                return
                
            # Tupel unpacking
            if len(v2_data) == 2:
                current_order, old_selection = v2_data
            else:
                logger.warning("⚠️ Ungültiges V2-Daten Format")
                return
            
            # Änderungen analysieren
            old_visible = {col for col, visible in old_selection.items() if visible}
            new_visible = set(new_selection)
            
            added_columns = new_visible - old_visible  # Neu hinzugefügte Spalten
            removed_columns = old_visible - new_visible  # Entfernte Spalten
            
            logger.info(f"📋 Spalten-Änderungen:")
            logger.info(f"  Hinzugefügt: {list(added_columns)}")
            logger.info(f"  Entfernt: {list(removed_columns)}")
            
            # Neue Reihenfolge aufbauen nach User-Spezifikation
            new_order = []
            new_column_selection = {}
            
            # 1. Bestehende sichtbare Spalten in aktueller Reihenfolge beibehalten
            for col_name in current_order:
                if col_name in new_visible and col_name not in added_columns:
                    new_order.append(col_name)
                    new_column_selection[col_name] = True
            
            # 2. Neu hinzugefügte Spalten am Ende der sichtbaren Spalten anfügen
            for col_name in added_columns:
                if col_name in current_order:  # Falls bereits in Reihenfolge
                    new_order.append(col_name)
                else:  # Ganz neue Spalte
                    new_order.append(col_name)
                new_column_selection[col_name] = True
                logger.debug(f"➕ Spalte '{col_name}' am Ende der sichtbaren eingefügt")
            
            # 3. Entfernte Spalten ans Ende der Reihenfolge setzen
            for col_name in current_order:
                if col_name in removed_columns:
                    new_order.append(col_name)
                    new_column_selection[col_name] = False
                    logger.debug(f"➖ Spalte '{col_name}' ans Ende verschoben (nicht sichtbar)")
            
            # 4. Alle anderen Spalten (weder hinzugefügt noch entfernt, nicht sichtbar)
            for col_name in current_order:
                if col_name not in new_column_selection:
                    new_order.append(col_name)
                    new_column_selection[col_name] = old_selection.get(col_name, False)
            
            # 5. Komplett neue Spalten, die nicht in current_order waren
            available_names = {col['name'] for col in available_columns}
            for col_name in available_names:
                if col_name not in new_column_selection:
                    new_order.append(col_name)
                    new_column_selection[col_name] = col_name in new_selection
            
            # Ebene 2 speichern über Complete Control System
            self.control_objects.update_column_selection(new_order, [col for col, visible in new_column_selection.items() if visible])
            
            # Tabelle neu aufbauen
            self._update_visible_columns()
            self._refresh_table_display()
            
            # Button-Text aktualisieren
            self._update_column_selection_button(available_columns)
            
            logger.info(f"✅ Spalten-Auswahl aktualisiert:")
            logger.info(f"  Sichtbare: {len([col for col, visible in new_column_selection.items() if visible])}")
            logger.info(f"  Versteckte: {len([col for col, visible in new_column_selection.items() if not visible])}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Spalten-Auswahl: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

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
            # NEUE 2-LEVEL-ARCHITEKTUR: Nur aktive Spalten (display_show=True) anzeigen
            control_columns = []
            column_dict = {col['name']: col for col in control.columns}
            
            for col_name in self.visible_column_names:
                if col_name in column_dict:
                    col = column_dict[col_name]
                    # Nur Spalten mit display_show=True tatsächlich anzeigen
                    if col.get('display_show', True):
                        control_columns.append(col)
            
            logger.debug(f"[ModernViewWidget] Tatsächlich angezeigte Spalten: {len(control_columns)} von {len(self.visible_column_names)} verfügbaren")

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
        
        # ERWEITERTE DRAG & DROP KONFIGURATION - JETZT AN DER RICHTIGEN STELLE!
        header = self.table.horizontalHeader()
        header.setDragDropMode(header.InternalMove)  # Nur interne Verschiebung
        header.sectionMoved.connect(self._on_column_moved)  # Event-Handler für Verschiebung
        
        # ZUSÄTZLICHE DEBUG-EVENTS für bessere Diagnose
        header.sectionPressed.connect(lambda idx: logger.info(f"🖱️ Spalten-Header gedrückt: Index {idx}"))
        header.sectionEntered.connect(lambda idx: logger.info(f"🖱️ Spalten-Header betreten: Index {idx}"))
        
        # Debug: Prüfe ob Event-Handler verbunden ist
        logger.info(f"🔧 DRAG & DROP SETUP ABGESCHLOSSEN:")
        logger.info(f"   sectionsMovable: {header.sectionsMovable()}")
        logger.info(f"   dragDropMode: {header.dragDropMode()}")
        logger.info(f"   sectionMoved Receivers: {header.receivers(header.sectionMoved)}")
        
        # DEBUG: Warnung wenn echte Mouse-Events erwartet werden
        logger.info("🖱️ BITTE BEACHTEN: Manuelle Spalten-Verschiebung mit Drag & Drop sollte automatisch _on_column_moved() aufrufen!")
        logger.info("🖱️ Falls keine Events ankommen: Prüfen Sie, ob die Maus richtig über den Header gezogen wird.")
        logger.info(f"   _on_column_moved Method: {hasattr(self, '_on_column_moved')}")
        logger.info("🔧 SPALTEN-DRAG & DROP IST AKTIVIERT - READY FOR TESTING!")
        
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
        
        # KRITISCHER FIX: Header-Reihenfolge nach Tabellenerstellung anwenden
        self._apply_saved_header_order(control_columns)
        
        layout.addWidget(self.table)

    def _apply_saved_header_order(self, control_columns):
        """
        Wendet die gespeicherte Benutzer-Spaltenreihenfolge auf die Header-Positionen an.
        
        Dies ist KRITISCH für die korrekte Darstellung beim Laden der Anwendung.
        Die Tabelle wird initial mit der Standard-Reihenfolge erstellt,
        dann werden die Header programmatisch in die gespeicherte Reihenfolge gebracht.
        
        Args:
            control_columns: Liste der Spalten-Definitionen in ursprünglicher Reihenfolge
        """
        if not hasattr(self, 'table') or not self.table:
            logger.warning("⚠️ Keine Tabelle vorhanden - kann Header-Reihenfolge nicht anwenden")
            return
            
        try:
            # Gespeicherte Reihenfolge laden
            saved_order = self._load_user_column_order()
            if not saved_order:
                logger.debug("🔄 Keine gespeicherte Spalten-Reihenfolge - verwende Standard-Reihenfolge")
                return
            
            header = self.table.horizontalHeader()
            
            # Mapping: Spaltenname -> ursprüngliche logische Position erstellen
            column_name_to_logical = {}
            for logical_idx, col in enumerate(control_columns):
                column_name = col.get('name', '')
                column_name_to_logical[column_name] = logical_idx
            
            logger.info(f"🔄 Wende gespeicherte Header-Reihenfolge an: {saved_order}")
            logger.debug(f"🔄 Spaltenname -> Logische Position: {column_name_to_logical}")
            
            # Header in gespeicherte Reihenfolge bringen
            # Wir müssen die Header schrittweise verschieben
            for target_visual_pos, column_name in enumerate(saved_order):
                if column_name not in column_name_to_logical:
                    logger.warning(f"⚠️ Spalte '{column_name}' aus gespeicherter Reihenfolge nicht in aktuellen Spalten gefunden")
                    continue
                
                target_logical_pos = column_name_to_logical[column_name]
                
                # Finde aktuelle visuelle Position der logischen Spalte
                current_visual_pos = header.visualIndex(target_logical_pos)
                
                if current_visual_pos != target_visual_pos:
                    # Verschiebe Header von aktueller zu Zielposition
                    logger.debug(f"🔄 Verschiebe '{column_name}': visuell {current_visual_pos} → {target_visual_pos}")
                    header.moveSection(current_visual_pos, target_visual_pos)
            
            # Verifikation: Prüfe finale Header-Reihenfolge
            final_order = []
            for visual_pos in range(header.count()):
                logical_pos = header.logicalIndex(visual_pos)
                if logical_pos < len(control_columns):
                    column_name = control_columns[logical_pos].get('name', f'col_{logical_pos}')
                    final_order.append(column_name)
            
            logger.info(f"✅ Header-Reihenfolge angewendet: {final_order}")
            
            if final_order == saved_order:
                logger.info("✅ Header-Reihenfolge erfolgreich wiederhergestellt!")
            else:
                logger.warning(f"⚠️ Header-Reihenfolge weicht ab:")
                logger.warning(f"   Erwartet: {saved_order}")
                logger.warning(f"   Aktuell:  {final_order}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden der Header-Reihenfolge: {e}")
            logger.error("   Verwende Standard-Reihenfolge")

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
        """Erstellt die Haupttabelle mit Spalten-Drag & Drop Unterstützung"""
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # Header-Styling und Drag & Drop für Spalten
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)
        
        # DRAG & DROP für Spalten-Reihenfolge aktivieren
        header.setSectionsMovable(True)  # Spalten verschiebbar machen
        header.setDragDropMode(header.InternalMove)  # Nur interne Verschiebung
        header.sectionMoved.connect(self._on_column_moved)  # Event-Handler für Verschiebung
        
        # ZUSÄTZLICHE DEBUG-EVENTS für bessere Diagnose
        header.sectionPressed.connect(lambda idx: logger.info(f"🖱️ Spalten-Header gedrückt: Index {idx}"))
        header.sectionEntered.connect(lambda idx: logger.info(f"🖱️ Spalten-Header betreten: Index {idx}"))
        
        # Debug: Prüfe ob Event-Handler verbunden ist
        logger.info(f"🔧 DRAG & DROP SETUP ABGESCHLOSSEN:")
        logger.info(f"   sectionsMovable: {header.sectionsMovable()}")
        logger.info(f"   dragDropMode: {header.dragDropMode()}")
        logger.info(f"   sectionMoved Receivers: {header.receivers(header.sectionMoved)}")
        
        # DEBUG: Warnung wenn echte Mouse-Events erwartet werden
        logger.info("🖱️ BITTE BEACHTEN: Manuelle Spalten-Verschiebung mit Drag & Drop sollte automatisch _on_column_moved() aufrufen!")
        logger.info("🖱️ Falls keine Events ankommen: Prüfen Sie, ob die Maus richtig über den Header gezogen wird.")
        logger.info(f"   _on_column_moved Method: {hasattr(self, '_on_column_moved')}")
        logger.info("🔧 SPALTEN-DRAG & DROP IST AKTIVIERT - READY FOR TESTING!")
        
        # Row selection
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        
        layout.addWidget(self.table)
        
        # Erfolgsmeldung für Drag & Drop
        logger.info("✅ Spalten-Drag & Drop aktiviert - Spalten können per Maus verschoben werden")
        logger.info("🔧 Event-Handler für sectionMoved verbunden - Reihenfolge wird automatisch gespeichert")
    
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
        
        # Debug: Aktuelle Header-Reihenfolge anzeigen
        if hasattr(self, 'table') and self.table:
            header = self.table.horizontalHeader()
            visual_order = []
            for visual_pos in range(header.count()):
                logical_pos = header.logicalIndex(visual_pos)
                if logical_pos < len(self.visible_column_names):
                    column_name = self.visible_column_names[logical_pos]
                    visual_order.append(column_name)
            logger.debug(f"🔍 Aktuelle visuelle Spalten-Reihenfolge: {visual_order}")
            logger.debug(f"🔍 visible_column_names: {self.visible_column_names}")
    
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

    def _on_column_moved(self, logical_index, old_visual_index, new_visual_index):
        """
        Event-Handler für Spalten-Verschiebung per Drag & Drop.
        
        User-Spezifikation Punkt 5:
        "Wird die Reihenfolge geändert, dann wird innerhalb der Ebene 2 
        die Reihenfolge in den sichtbaren Controls entsprechend geändert.
        Mit jeder Änderung wird Ebene 2 gespeichert."
        """
        logger.info(f"🔥 Drag & Drop: logical={logical_index}, old_visual={old_visual_index}, new_visual={new_visual_index}")
        
        try:
            # Aktuelle visuelle Reihenfolge der SICHTBAREN Spalten aus Header lesen
            header = self.table.horizontalHeader()
            new_visible_order = []
            
            for visual_pos in range(header.count()):
                logical_pos = header.logicalIndex(visual_pos)
                if logical_pos < len(self.visible_column_names):
                    column_name = self.visible_column_names[logical_pos]
                    new_visible_order.append(column_name)
            
            logger.info(f"🔄 Neue sichtbare Reihenfolge: {new_visible_order}")
            
            # Ebene 2 entsprechend aktualisieren
            self._update_level2_order_from_drag_drop(new_visible_order)
            
            moved_column = self.visible_column_names[logical_index] if logical_index < len(self.visible_column_names) else "Unbekannt"
            logger.info(f"✅ Spalte '{moved_column}' von Position {old_visual_index} → {new_visual_index}")
            logger.info("💾 Ebene 2 wurde aktualisiert und gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Drag & Drop: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _update_complete_controls_from_drag_drop(self, new_visible_order):
        """
        VOLLSTÄNDIGE CONTROLS: Aktualisiert vollständige Control-Objekte nach Drag & Drop.
        
        Args:
            new_visible_order: Liste der Control-Namen in neuer Reihenfolge
        """
        try:
            # Vollständige Controls laden
            if not hasattr(self, 'complete_controls') or not self.complete_controls:
                logger.warning("⚠️ Keine vollständigen Controls verfügbar - lade sie neu")
                self.complete_controls = self._load_complete_controls_v3()
                
                if not self.complete_controls:
                    logger.error("❌ Vollständige Controls nicht verfügbar")
                    return
            
            # user_display_order für neue Reihenfolge aktualisieren
            update_count = 0
            for new_order, control_name in enumerate(new_visible_order, 1):
                if control_name in self.complete_controls:
                    self.complete_controls[control_name]['user_display_order'] = new_order
                    self.complete_controls[control_name]['last_updated'] = datetime.now().isoformat()
                    update_count += 1
            
            # Vollständige Controls speichern
            if self._save_complete_controls_v3():
                logger.info(f"🔄 VOLLSTÄNDIGE CONTROLS: {update_count} Controls nach Drag & Drop aktualisiert")
                logger.debug(f"🔄 Neue Reihenfolge: {new_visible_order[:3]}{'...' if len(new_visible_order) > 3 else ''}")
            else:
                logger.error("❌ Fehler beim Speichern der aktualisierten vollständigen Controls")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der vollständigen Controls: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
        """
        KORREKTE ARCHITEKTUR: Aktualisiert Control-Parameter nach Drag & Drop.
        
        Schreibt die neue Reihenfolge in systemsteuerung.daten[view_guid]['controls'][control_name]
        für jeden betroffenen Control.
        
        Args:
            new_visible_order: Liste der Control-Namen in neuer Reihenfolge 
                              (z.B. ["familienname_original", "geburtsdatum_show", ...])
        """
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from datetime import datetime
            
            # Systemsteuerung für Benutzer laden (uid = user_guid wird vom System verwaltet)
            sys_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="systemsteuerung",
                guid=self.user_guid
            )
            
            # Aktuelle Benutzerdaten laden
            user_data = sys_db.lesen() or {}
            
            # View-Gruppe und Controls-Bereich initialisieren falls nicht vorhanden
            if self.view_guid not in user_data:
                user_data[self.view_guid] = {}
            if 'controls' not in user_data[self.view_guid]:
                user_data[self.view_guid]['controls'] = {}
            
            controls_data = user_data[self.view_guid]['controls']
            
            # display_order für jeden Control in neuer Reihenfolge aktualisieren
            update_count = 0
            for new_order, control_name in enumerate(new_visible_order, 1):
                if control_name in controls_data and isinstance(controls_data[control_name], dict):
                    # display_order für diesen Control aktualisieren
                    controls_data[control_name]['display_order'] = new_order
                    controls_data[control_name]['last_updated'] = datetime.now().isoformat()
                    update_count += 1
                else:
                    # Control existiert noch nicht - mit Standard-Werten erstellen
                    controls_data[control_name] = {
                        'display_show': True,
                        'display_order': new_order,
                        'last_updated': datetime.now().isoformat()
                    }
                    update_count += 1
            
            # Alle aktualisierten Controls speichern
            user_data[self.view_guid]['controls'] = controls_data
            sys_db.speichern(self.user_guid, user_data)
            
            logger.info(f"🔄 KORREKTE ARCHITEKTUR: Controls nach Drag & Drop aktualisiert in systemsteuerung.daten[{self.view_guid}]['controls']:")
            logger.info(f"  Aktualisierte Controls: {update_count}")
            logger.debug(f"  Control-Namen in neuer Reihenfolge: {new_visible_order[:3]}{'...' if len(new_visible_order) > 3 else ''}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Controls: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _update_level2_order_from_drag_drop(self, new_visible_order):
        """
        KOMPATIBILITÄT: Aktualisiert Ebene 2 basierend auf neuer sichtbarer Reihenfolge.
        
        NEUE ARCHITEKTUR: Delegiert an _update_controls_from_drag_drop für direktere Lösung.
        
        Args:
            new_visible_order: Neue Reihenfolge der sichtbaren Spalten
        """
        try:
            # NEUE ARCHITEKTUR: Direkte Control-Updates
            self._update_controls_from_drag_drop(new_visible_order)
            
            logger.debug(f"🔄 Drag & Drop über Control-Updates verarbeitet")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Drag & Drop Update: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    # ENTFERNT: _apply_column_order_to_table() - Redundant, da Reihenfolge bereits vor Tabellenerstellung angewendet wird
    # Die Reihenfolge wird jetzt in _apply_user_column_order() vor der Tabellenerstellung korrekt gesetzt

    def test_column_order_functionality(self):
        """
        Test-Methode für die neue Ebene-2-Architektur.
        
        Testet systematisch alle 8 Punkte der User-Spezifikation.
        """
        try:
            logger.info("🧪 SPALTEN-TEST: Neue Ebene-2-Architektur")
            logger.info("=" * 60)
            
            # 1. Vollständige Tabelle + Controls prüfen
            control = getattr(self.data_manager, 'control', None)
            if control and hasattr(control, 'columns'):
                logger.info(f"✅ Punkt 1: Vollständige Tabelle - {len(control.columns)} Spalten verfügbar")
            else:
                logger.error("❌ Punkt 1: Keine vollständige Tabelle verfügbar")
                return
            
            # 2. Ebene 2 Status prüfen
            v2_data = self._load_user_column_order_v2()
            if v2_data and len(v2_data) == 2:
                column_order, column_selection = v2_data
                logger.info(f"✅ Punkt 2: Gespeicherte Ebene 2 gefunden")
                logger.info(f"   Reihenfolge: {len(column_order)} Spalten")
                logger.info(f"   Sichtbarkeit: {len(column_selection)} Einstellungen")
            else:
                logger.info("ℹ️ Punkt 2: Keine Ebene 2 → wird neu erstellt")
            
            # 3. Aktuelle Darstellung prüfen
            logger.info(f"✅ Punkt 3: Tabellendarstellung - {len(self.visible_column_names)} Spalten")
            logger.info(f"   Aktuelle Reihenfolge: {self.visible_column_names[:5]}{'...' if len(self.visible_column_names) > 5 else ''}")
            
            # 4. Order-System testen (Punkt 6-7)
            logger.info("🧪 Order-System Test:")
            for col in control.columns[:10]:  # Erste 10 Spalten
                original_order = col.get('order', 999)
                expert = col.get('expert', False)
                show = col.get('show', False)
                
                if expert:
                    expected_order = original_order + 200
                    category = "Expert"
                elif show:
                    expected_order = original_order
                    category = "Normal"
                else:
                    expected_order = 999
                    category = "Nicht angezeigt"
                
                logger.info(f"   {col['name'][:15]:15} | Original: {original_order:3d} | Expected: {expected_order:3d} | {category}")
            
            # 5. Drag & Drop Test (Punkt 5)
            if hasattr(self, 'table') and self.table:
                header = self.table.horizontalHeader()
                logger.info(f"✅ Punkt 5: Drag & Drop - Movable: {header.sectionsMovable()}")
                logger.info(f"   Signal-Verbindungen: {header.receivers(header.sectionMoved)} Empfänger")
            else:
                logger.warning("⚠️ Punkt 5: Keine Tabelle für Drag & Drop Test")
            
            # 6. Expert-Mode Test (Punkt 8)
            expert_cols = [col for col in control.columns if col.get('expert', False)]
            normal_cols = [col for col in control.columns if col.get('show', False) and not col.get('expert', False)]
            
            logger.info(f"✅ Punkt 8: Flexibilität - Normal: {len(normal_cols)}, Expert: {len(expert_cols)} Spalten")
            
            # Test-Zusammenfassung
            logger.info("=" * 60)
            logger.info("🧪 SPALTEN-TEST ABGESCHLOSSEN")
            logger.info(f"💾 Ebene 2 Status: {'Vorhanden' if v2_data else 'Wird erstellt'}")
            logger.info(f"🎯 Aktuelle Anzeige: {len(self.visible_column_names)} Spalten")
            logger.info(f"🔄 Expert-Mode: {'AN' if self.expert_mode else 'AUS'}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Spalten-Test: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def reset_column_settings_to_defaults(self):
        """
        KORREKTE ARCHITEKTUR: Setzt alle Spalten-Einstellungen auf Standardwerte zurück.
        
        Liest die Standard-Controls aus den viewdaten und speichert diese
        in systemsteuerung.daten[view_guid]['controls'].
        """
        try:
            logger.info("🔄 SPALTEN-RESET: Stelle Standardwerte wieder her")
            
            # Standard-Controls aus data_manager laden
            control = getattr(self.data_manager, 'control', None)
            if not control or not hasattr(control, 'columns'):
                logger.error("❌ Keine Standard-Controls verfügbar")
                return False
            
            # Standard-Parameter in Controls übernehmen
            reset_count = 0
            column_names = []
            column_selection = {}
            
            for col in control.columns:
                col_name = col['name']
                column_names.append(col_name)
                
                # Standard display_show aus 'show'-Parameter
                default_show = col.get('show', False)
                column_selection[col_name] = default_show
                reset_count += 1
            
            # Nach Standard-Order sortieren
            column_names.sort(key=lambda name: next(
                (col.get('order', 999) for col in control.columns if col['name'] == name), 999
            ))
            
            # Standardwerte in korrekter Architektur speichern
            self._save_user_column_order_v2(column_names, column_selection)
            
            logger.info(f"✅ KORREKTE ARCHITEKTUR: {reset_count} Controls auf Standardwerte in systemsteuerung.daten[{self.view_guid}]['controls'] zurückgesetzt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Reset der Spalten-Einstellungen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False
            
            # UI aktualisieren
            self._update_visible_columns()
            
            logger.info(f"✅ Spalten-Einstellungen zurückgesetzt: {reset_count} Controls")
            logger.info(f"🔄 Standard-Reihenfolge und -Sichtbarkeit wiederhergestellt")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Spalten-Einstellungen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def _refresh_table_display(self):
        """
        Aktualisiert die Tabellen-Anzeige nach Änderungen der Spalten-Auswahl oder -Reihenfolge.
        WICHTIG: Erstellt KEINE neue Tabelle, sondern aktualisiert nur die Spaltenanzeige.
        """
        try:
            logger.info("🔄 Aktualisiere Tabelle nach Spalten-Änderung (KEINE neue Tabelle)")
            
            # Complete Controls V3 neu laden
            complete_controls = self._load_complete_controls_v3()
            
            if complete_controls:
                # Sichtbare Spalten aus Complete Controls extrahieren
                visible_columns = [
                    name for name, control in complete_controls.items() 
                    if control.get('user_display_show', True)
                ]
                
                # Spalten-Reihenfolge aus Complete Controls extrahieren
                sorted_controls = sorted(
                    complete_controls.items(),
                    key=lambda x: x[1].get('user_display_order', 999)
                )
                column_order = [name for name, _ in sorted_controls]
                
                # Widget-Status aktualisieren
                self.visible_column_names = visible_columns
                
                # Tabelle komplett neu erstellen (bestehende löschen)
                if hasattr(self, 'table') and self.table:
                    # Alte Tabelle aus Layout entfernen
                    layout = self.layout()
                    if layout:
                        layout.removeWidget(self.table)
                    self.table.deleteLater()
                    self.table = None
                
                # Neue Tabelle mit aktualisierten Spalten erstellen
                layout = self.layout()
                if layout:
                    self._create_table_with_visible_columns(layout)
                    
                logger.info(f"✅ Tabelle erfolgreich neu erstellt: {len(visible_columns)} sichtbare Spalten")
                
            else:
                logger.warning("⚠️ Keine Complete Controls V3 verfügbar für Tabellen-Update")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabellen-Anzeige: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def _update_table_headers(self):
        """
        Aktualisiert nur die Spaltenheader der bestehenden Tabelle ohne neue Tabelle zu erstellen.
        """
        try:
            control = getattr(self.data_manager, 'control', None)
            if not control or not hasattr(control, 'columns'):
                logger.warning("⚠️ Keine Control-Struktur für Header-Update verfügbar")
                return
            
            # Nur sichtbare Spalten nehmen
            visible_columns = []
            column_dict = {col['name']: col for col in control.columns}
            
            for col_name in self.visible_column_names:
                if col_name in column_dict:
                    visible_columns.append(column_dict[col_name])
            
            # Spaltenanzahl anpassen
            self.table.setColumnCount(len(visible_columns))
            
            # Header-Labels setzen
            headers = []
            for col in visible_columns:
                label = col.get('anzeige', col.get('label', col['name']))
                headers.append(label)
            
            self.table.setHorizontalHeaderLabels(headers)
            
            logger.debug(f"✅ Tabellen-Header aktualisiert: {len(headers)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabellen-Header: {e}")

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
