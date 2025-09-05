#!/usr/bin/env python3
"""
PdvmViewWidget - NEUE ARCHITEKTUR
Widget wird von persistentem DatenManager kontrolliert und befüllt.

ARCHITEKTUR-ÄNDERUNG:
ALT: Widget erstellt DatenManager -> DatenManager wird bei Widget-Refresh zerstört
NEU: DatenManager erstellt Widget -> DatenManager bleibt persistent, Widget ist disposable
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QLabel, QPushButton, QMenu, QMessageBox
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PdvmViewWidget(QWidget):
    def __init__(self, call_daten, parent=None, reload_callback=None):
        super().__init__(parent)
        self.call_daten = call_daten
        self.view_manager = None  # Wird vom persistenten DatenManager gesetzt!
        self.reload_callback = reload_callback  # Parent-Callback für echten Reload

        # Header-Label für Updates
        self.header_label = None

        # UI Setup
        self.setup_ui()

        # WICHTIG: Daten werden NICHT hier geladen! 
        # Das macht der persistente DatenManager über _populate_widget()

    def setup_ui(self):
        """UI Komponenten erstellen"""
        layout = QVBoxLayout(self)
        
        # Header-Zeile mit Titel und Einstellungs-Menü
        header_layout = QHBoxLayout()
        
        # Titel-Label (links) - mit view_header aus call_daten
        header_text = self.get_header_text()
        self.header_label = QLabel(header_text, self)
        self.header_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        header_layout.addWidget(self.header_label)
        
        # Platz zwischen Titel und Menü
        header_layout.addStretch()
        
        # Einstellungs-Menü (rechts)
        self.settings_button = self.create_settings_menu()
        header_layout.addWidget(self.settings_button)
        
        # Header-Container Widget
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background: lightblue; padding: 2px;")
        layout.addWidget(header_widget)
        
        # Table Widget
        self.table = QTableWidget(self)
        self.table.setMinimumHeight(300)  # Mindesthöhe sicherstellen
        layout.addWidget(self.table)
        
        # Debug-Info Label
        debug_label = QLabel(f"CallDaten: {len(self.call_daten)} Items | ViewGUID: {self.call_daten.get('view_guid', 'N/A')}", self)
        debug_label.setStyleSheet("font-size: 10px; color: gray; padding: 2px;")
        layout.addWidget(debug_label)
        
        logger.info("✅ Widget UI erstellt (warte auf DatenManager-Befüllung)")

    def get_header_text(self):
        """Header-Text aus call_daten generieren"""
        try:
            # 1. Basis-Text aus view_header
            view_header = self.call_daten.get('view_header', 'PDVM View')
            
            # 2. Zentralen Stichtag holen
            import pdvm_central_systemsteuerung_global
            gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung
            
            # Fix: Verwende get_value ohne 'standard' Parameter
            stichtag_data = gcs.get_value(gruppe="GLOBAL", feld="stichtag")
            if stichtag_data and isinstance(stichtag_data, dict) and "wert" in stichtag_data:
                stichtag_str = stichtag_data["wert"]
            else:
                stichtag_str = "Kein Stichtag"
            
            # 3. ExpertMode-Status holen  
            expert_data = gcs.get_value(gruppe="GLOBAL", feld="expert_mode")
            if expert_data and isinstance(expert_data, dict) and "wert" in expert_data:
                expert_mode = expert_data["wert"]
            else:
                expert_mode = False
            
            expert_indicator = " [EXPERT]" if expert_mode else ""
            
            return f"{view_header} (Stichtag: {stichtag_str}){expert_indicator}"
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Header-Text generieren: {e}")
            return "PDVM View"

    def update_header_text(self):
        """Aktualisiert den Header-Text (wird vom DatenManager aufgerufen)"""
        try:
            if self.header_label:
                new_text = self.get_header_text()
                self.header_label.setText(new_text)
                logger.info(f"🔄 Header aktualisiert: {new_text}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Header-Update: {e}")

    def create_settings_menu(self):
        """Erstellt das Einstellungs-Menü"""
        settings_button = QPushButton("⚙️ Einstellungen", self)
        settings_button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        menu = QMenu(self)
        
        # Spalten-Einstellungen
        spalten_action = menu.addAction("📊 Spalten konfigurieren")
        spalten_action.triggered.connect(self.open_column_settings)
        
        menu.addSeparator()
        
        # Expert Mode Toggle
        expert_action = menu.addAction("🎯 Expert Mode")
        expert_action.setCheckable(True)
        
        # Aktuellen Expert Mode Status laden und anzeigen
        try:
            from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung
            gcs = PdvmCentralSystemsteuerung()
            expert_data = gcs.get_value(gruppe="GLOBAL", feld="expert_mode")
            if expert_data and isinstance(expert_data, dict) and "wert" in expert_data:
                expert_action.setChecked(expert_data["wert"])
        except:
            pass  # Bei Fehler bleibt unchecked
            
        expert_action.triggered.connect(self.toggle_expert_mode)
        
        # Reload
        reload_action = menu.addAction("🔄 Neu laden")
        reload_action.triggered.connect(self.handle_reload)
        
        settings_button.setMenu(menu)
        return settings_button

    def open_column_settings(self):
        """Öffnet den Spalten-Einstellungen Dialog"""
        try:
            if not self.view_manager or not hasattr(self.view_manager, 'basis_columns'):
                QMessageBox.warning(self, "Warnung", "Keine Spalten-Daten verfügbar")
                return
                
            from pdvm_view_column_settings_dialog import ColumnSettingsDialog
            
            dialog = ColumnSettingsDialog(self.view_manager.basis_columns, self)
            if dialog.exec_() == dialog.Accepted:
                # Änderungen vom persistenten DatenManager speichern lassen
                if hasattr(self.view_manager, 'save_column_settings'):
                    # ColumnSettingsDialog verwendet result_controls nach accept()
                    self.view_manager.save_column_settings(dialog.result_controls)
                
                # Widget über DatenManager refreshen (DatenManager bleibt erhalten!)
                from pdvm_view_manager_registry import PdvmViewManagerRegistry
                PdvmViewManagerRegistry.refresh_widget_for_manager(self.call_daten.get('view_guid'))
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen der Spalten-Einstellungen: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Fehler", f"Fehler: {e}")

    def toggle_expert_mode(self):
        """Togglet Expert Mode über zentrale Systemsteuerung"""
        try:
            import pdvm_central_systemsteuerung_global
            gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung
            
            # Fix: get_value ohne 'standard' Parameter verwenden
            current_data = gcs.get_value(gruppe="GLOBAL", feld="expert_mode")
            if current_data and isinstance(current_data, dict) and "wert" in current_data:
                current = current_data["wert"]
            else:
                current = False
                
            new_value = not current
            # Fix: ab_zeit Parameter hinzufügen (verwende aktuelle Zeit)
            from central_systemsteuerung_global import central_systemsteuerung
            ab_zeit = central_systemsteuerung.pdvm_datetime.get_float_value()
            gcs.set_value(gruppe="GLOBAL", feld="expert_mode", wert=new_value, ab_zeit=ab_zeit)
            
            # Header aktualisieren
            self.update_header_text()
            
            # Tabelle über persistenten DatenManager neu laden
            if self.view_manager:
                self._load_table_data()
                
            logger.info(f"🎯 Expert Mode: {current} -> {new_value}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Expert Mode Toggle: {e}")
            import traceback
            traceback.print_exc()

    def handle_reload(self):
        """Behandelt Reload über den persistenten DatenManager"""
        try:
            if self.reload_callback:
                # NEUE ARCHITEKTUR: Callback braucht reload_call_daten
                reload_call_daten = dict(self.call_daten)
                reload_call_daten['first_call'] = False  # Wichtig für Refresh
                self.reload_callback(reload_call_daten)
            else:
                # Widget über persistenten DatenManager refreshen
                from pdvm_view_manager_registry import PdvmViewManagerRegistry
                refreshed_widget = PdvmViewManagerRegistry.refresh_widget_for_manager(self.call_daten.get('view_guid'))
                
                if refreshed_widget and hasattr(self.parent(), 'refresh_view'):
                    self.parent().refresh_view(refreshed_widget)
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Reload: {e}")
            import traceback
            traceback.print_exc()

    def _load_table_data(self):
        """
        Lädt Daten vom persistenten ViewManager und füllt die Tabelle
        WICHTIG: ViewManager ist persistent und hat alle Daten/Controls!
        """
        logger.info("📊 Lade Tabelle vom persistenten DatenManager")
        try:
            if not self.view_manager:
                logger.error("❌ Kein ViewManager verfügbar (persistente Architektur fehlt)")
                self._create_fallback_table()
                return
                
            # Hole Daten und Spaltenprojektion ausschließlich vom persistenten DatenManager
            table_data = self.view_manager.get_table_data_for_display()
            
            if not table_data:
                logger.error("❌ Keine Tabellen-Daten vom persistenten DatenManager erhalten")
                self._create_fallback_table()
                return
            
            # Tabelle mit Daten vom persistenten DatenManager befüllen
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            logger.info(f"📊 Befülle Tabelle: {len(headers)} Spalten, {len(rows)} Zeilen (vom persistenten DatenManager)")
            
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            self.table.setHorizontalHeaderLabels(headers)
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, cell_value in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, self._create_table_item(cell_value))
            
            # Spaltenbreiten anpassen
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Tabellen-Daten vom persistenten DatenManager: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self._create_fallback_table()
    
    def _create_table_item(self, value):
        """Erstellt ein QTableWidgetItem für den gegebenen Wert"""
        from PyQt5.QtWidgets import QTableWidgetItem
        
        if value is None:
            return QTableWidgetItem("")
        return QTableWidgetItem(str(value))
    
    def _create_fallback_table(self):
        """Erstellt eine Fallback-Tabelle wenn keine Daten verfügbar sind"""
        logger.warning("⚠️ Erstelle Fallback-Tabelle (persistenter DatenManager nicht verfügbar)")
        
        fallback_headers = ["Info", "Status"]
        fallback_data = [
            ["Persistenter DatenManager", "Nicht verfügbar"],
            ["Architektur", "NEUE: DatenManager -> Widget"],
            ["Problem", "DatenManager-Registry fehlt"]
        ]
        
        self.table.setColumnCount(len(fallback_headers))
        self.table.setRowCount(len(fallback_data))
        self.table.setHorizontalHeaderLabels(fallback_headers)
        
        for row_idx, row_data in enumerate(fallback_data):
            for col_idx, cell_value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, self._create_table_item(cell_value))
        
        self.table.resizeColumnsToContents()
