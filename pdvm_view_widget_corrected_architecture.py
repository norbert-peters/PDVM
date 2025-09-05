# pdvm_view_widget_corrected_architecture.py
"""
KORREKTE ARCHITEKTUR-ANPASSUNG
==============================

Nimmt das bewährte, funktionierende pdvm_view_widget.py und passt nur die Architektur an:
- Von: Widget erstellt DatenManager  
- Zu: DatenManager (persistent) erstellt Widget (disposable)

ALLE bestehenden UI-Features und -Logik bleiben erhalten!
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                           QHeaderView, QPushButton, QMenuBar, QLabel, QMenu, QAction, QMessageBox)
from PyQt5.QtCore import Qt

# GLOBALE IMPORTS: Einfacher Zugriff auf zentrale Funktionen
import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung

logger = logging.getLogger(__name__)

class PdvmViewWidget(QWidget):
    def __init__(self, call_daten, persistent_view_manager, parent=None, reload_callback=None):
        """
        NEUE ARCHITEKTUR: Widget bekommt den persistenten ViewManager übergeben
        statt ihn selbst zu erstellen.
        
        Args:
            call_daten: Aufruf-Daten wie gehabt
            persistent_view_manager: Persistenter DatenManager (erstellt vom Registry)  
            parent: Parent Widget
            reload_callback: Callback für echten Reload
        """
        super().__init__(parent)
        self.call_daten = call_daten
        self.view_manager = persistent_view_manager  # NEUE ARCHITEKTUR: Übernehmen statt erstellen
        self.reload_callback = reload_callback

        self.header_label = None  # Referenz auf Header-Label für Updates

        # UI Setup (1:1 wie original)
        self.setup_ui()

        # Daten laden (angepasst für persistenten Manager)
        self.load_data_from_persistent_manager()

    def setup_ui(self):
        """UI Komponenten erstellen - 1:1 ÜBERNOMMEN vom original Widget"""
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
        
        # Layout Eigenschaften setzen
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        self.setLayout(layout)
        
        # Widget-Eigenschaften
        self.setMinimumSize(400, 350)  # Mindestgröße
        
        logger.info("✅ UI Setup mit Header und Debug-Info abgeschlossen")
    
    def get_header_text(self):
        """
        Erstellt den Header-Text basierend auf view_header und ExpertMode - 1:1 ÜBERNOMMEN
        """
        # Basis: view_header aus call_daten
        view_header = self.call_daten.get('view_header', 'PDVM View')
        
        if gcs.global_expert_mode:
            # ExpertMode: view_header + zentraler Stichtag
            header_text = f"{view_header} - Stichtag: {gcs.global_stichtag}"
        else:
            # NormalMode: nur view_header
            header_text = view_header
            
        logger.debug(f"🔤 Header-Text erstellt: '{header_text}' (ExpertMode: {gcs.global_expert_mode})")
        return header_text
    
    def update_header_text(self):
        """
        Aktualisiert den Header-Text nach ExpertMode-Änderung - 1:1 ÜBERNOMMEN
        """
        if self.header_label:
            new_text = self.get_header_text()
            self.header_label.setText(new_text)
            logger.info(f"✅ Header-Text aktualisiert: '{new_text}'")
    
    def create_settings_menu(self):
        """
        Erstellt das Einstellungs-Menü in der Kopfzeile - 1:1 ÜBERNOMMEN
        """
        # Einstellungs-Button erstellen
        settings_button = QPushButton("⚙️ Einstellungen", self)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # Dynamisches Menü - wird bei jedem Klick neu erstellt
        def show_dynamic_menu():
            """Zeigt aktualisiertes Menü basierend auf aktuellem Status"""
            # Menü erstellen
            settings_menu = QMenu(self)

            # Menüpunkte hinzufügen
            # 1. Spalten verwalten
            action_spalten = QAction("📊 Spalten verwalten", self)
            action_spalten.triggered.connect(self.on_spalten_verwalten)
            settings_menu.addAction(action_spalten)

            # 2. Experten Modus ein/aus (nur bei mode='admin')
            logger.debug(f"🔧 Experten Modus: '{gcs.global_mode}' (aktuell: {gcs.global_expert_mode})")
            if gcs.global_mode == 'admin':
                # Status-abhängiger Menütext - AKTUELLER Status
                expert_status = "ausschalten" if gcs.global_expert_mode else "einschalten"
                action_expert = QAction(f"🔧 Experten Modus {expert_status}", self)
                action_expert.triggered.connect(self.on_expert_modus_toggle)
                settings_menu.addAction(action_expert)
                logger.debug(f"🔧 Experten Modus: '{expert_status}' (aktuell: {gcs.global_expert_mode})")

            # 3. Filter ein/aus
            action_filter = QAction("🔍 Filter ein/aus", self)
            action_filter.triggered.connect(self.on_filter_toggle)
            settings_menu.addAction(action_filter)

            # Menü anzeigen
            settings_menu.exec_(settings_button.mapToGlobal(settings_button.rect().bottomLeft()))
        
        # Button-Click verbinden
        settings_button.clicked.connect(show_dynamic_menu)
        
        logger.info("✅ Dynamisches Einstellungs-Menü erstellt")
        return settings_button
    
    def on_spalten_verwalten(self):
        """Spalten verwalten - 1:1 ÜBERNOMMEN aber für persistenten Manager angepasst"""
        try:
            from pdvm_view_column_settings_dialog import ColumnSettingsDialog
            
            # Alle basis_columns vom persistenten Manager verwenden
            columns = []
            for col in self.view_manager.basis_columns:
                col_copy = col.copy()
                col_copy['show'] = col_copy.get('show', False)
                col_copy['expertOrder'] = col_copy.get('expertOrder', 999)
                col_copy['displayOrder'] = col_copy.get('displayOrder', 999)
                columns.append(col_copy)
                
            # Dialog bestimmt Modus selbst aus Systemsteuerung
            dlg = ColumnSettingsDialog(columns, self)
            logger.info(f"🔧 Öffne Spaltendialog mit {len(columns)} Spalten (ExpertMode: {gcs.global_expert_mode})")
            
            if dlg.exec_() and dlg.result_controls is not None:
                logger.info(f"✅ Dialog akzeptiert, übertrage {len(dlg.result_controls)} Spalteneinstellungen")
                
                # Änderungen über persistenten DatenManager speichern
                logger.info("🔄 Speichere Änderungen über persistenten view_manager.save_column_configuration")
                success = self.view_manager.save_column_configuration(dlg.result_controls)
                
                if success:
                    logger.info("💾 Neue Controls erfolgreich in Systemsteuerung gespeichert")
                    
                    # basis_columns aus persistentem DatenManager neu laden
                    self.view_manager.refresh_controls_and_projection()
                    logger.info("🔄 Controls und Projection aus Systemsteuerung neu geladen")
                    
                    # Tabelle neu laden
                    self._load_table_data()
                    logger.info("✅ Tabelle mit neuen Controls aktualisiert")
                else:
                    logger.error("❌ Fehler beim Speichern der Spalten-Konfiguration")
                    QMessageBox.warning(self, "Fehler", "Die Spalten-Konfiguration konnte nicht gespeichert werden.")
                    
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Spaltendialogs: {e}")
        
    def on_expert_modus_toggle(self):
        """Moduswechsel zwischen ExpertMode - 1:1 ÜBERNOMMEN"""
        try:
            new_mode = not gcs.global_expert_mode
            # Wert persistent in Systemsteuerung speichern
            try:
                gcs.set_value(gruppe=gcs.user_guid, feld="ExpertMode", wert=new_mode, ab_zeit=1001.0)
                gcs.save_values()
                logger.info(f"💾 ExpertMode in Systemsteuerung gespeichert: {new_mode}")
            except Exception as e2:
                logger.warning(f"⚠️ Fehler beim Speichern von ExpertMode in Systemsteuerung: {e2}")
            
            # Nur Tabelle neu laden, keine komplette Widget-Neuinitialisierung
            logger.info(f"🔄 Moduswechsel: ExpertMode={new_mode}")
            self._load_table_data()
            self.update_header_text()  # Header mit neuem ExpertMode aktualisieren
            logger.info("✅ Tabelle nach Moduswechsel aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Moduswechsel: {e}")

    def on_filter_toggle(self):
        """Filter ein/aus - 1:1 ÜBERNOMMEN"""
        logger.info("🔍 Filter Toggle geklickt (noch ohne Funktion)")
        
    def load_data_from_persistent_manager(self):
        """
        NEUE ARCHITEKTUR: Lädt Daten vom bereits initialisierten persistenten Manager
        Ersetzt das alte load_data() das einen neuen Manager erstellt hat
        """
        try:
            logger.info("🔧 NEUE ARCHITEKTUR: Verwende übergebenen persistenten ViewManager")
            
            if not self.view_manager:
                logger.error("❌ Kein persistenter ViewManager übergeben!")
                self._create_fallback_table()
                return
            
            # Persistenter Manager ist bereits vollständig initialisiert
            logger.info("✅ Persistenter ViewManager verfügbar - lade Tabellendaten")
            self._load_table_data()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden vom persistenten Manager: {e}")
            self._create_fallback_table()
    
    def _load_table_data(self):
        """
        Lädt und zeigt Tabellendaten - ANGEPASST für persistenten Manager
        """
        try:
            logger.info("📊 Lade Tabelle vom persistenten ViewManager")
            
            # Tabellendaten vom persistenten Manager holen
            table_data = self.view_manager.get_table_data_for_display()
            
            if not table_data:
                logger.error("❌ Keine Tabellen-Daten vom persistenten ViewManager erhalten")
                self._create_fallback_table()
                return
            
            # Original-Logik für Tabellen-Befüllung verwenden
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            logger.info(f"📊 Befülle Tabelle: {len(headers)} Spalten, {len(rows)} Zeilen")
            
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            
            # VERBESSERTE HEADER: Schöne, gestylete Spaltenüberschriften erstellen
            self._set_beautiful_headers(headers)
            
            # Zeilen befüllen
            for row_idx, row_data in enumerate(rows):
                for col_idx, cell_value in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                    self.table.setItem(row_idx, col_idx, item)
            
            # Spalten anpassen
            self.table.resizeColumnsToContents()
            logger.info("✅ Tabelle erfolgreich befüllt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Tabellen-Daten: {e}")
            import traceback
            traceback.print_exc()
            self._create_fallback_table()

    def _set_beautiful_headers(self, headers):
        """
        Erstellt schöne, gestylete Spaltenüberschriften mit Modus-abhängigem Design.
        
        Args:
            headers: Liste der Spalten-Anzeigenamen
        """
        try:
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QFont
            
            # Im ExpertMode die technischen Namen vom persistenten Manager holen
            if gcs.global_expert_mode and self.view_manager and hasattr(self.view_manager, 'basis_columns'):
                enhanced_headers = self._create_expert_headers(headers)
            else:
                enhanced_headers = headers
            
            # Header setzen
            self.table.setHorizontalHeaderLabels(enhanced_headers)
            
            # Header-Styling anwenden
            header = self.table.horizontalHeader()
            
            # Font: Größer und fetter (für den Fall dass HTML nicht funktioniert)
            font = QFont()
            font.setPointSize(10)  # Etwas größer
            font.setBold(True)     # Fetter
            header.setFont(font)
            
            # Text-Alignment für HTML-Inhalte setzen
            header.setDefaultAlignment(Qt.AlignCenter)
            
            # Modus-abhängiger Hintergrund - BEWÄHRTES DESIGN
            if gcs.global_expert_mode:
                # ExpertMode: Sanftes Blau wie in der bewährten Version
                header_style = """
                    QHeaderView::section {
                        font-weight: bold;
                        font-size: 10pt;
                        padding: 6px 4px;
                        border: 1px solid #ddd;
                        background-color: #e8f4fd;
                        color: #2c3e50;
                        text-align: center;
                    }
                    QHeaderView::section:hover {
                        background-color: #d4edda;
                    }
                """
            else:
                # NormalMode: Einfaches graues Design wie bewährt
                header_style = """
                    QHeaderView::section {
                        font-weight: bold;
                        font-size: 11pt;
                        padding: 6px;
                        border: 1px solid #ddd;
                        background-color: #f5f5f5;
                        color: #2c3e50;
                    }
                """
            
            header.setStyleSheet(header_style)
            
            # Header-Höhe entsprechend anpassen 
            if gcs.global_expert_mode:
                header.setMinimumHeight(55)  # Höher für zweizeilige Header mit \n
            else:
                header.setMinimumHeight(35)  # Standard-Höhe
                
            logger.info(f"✅ Schöne Header erstellt - ExpertMode: {gcs.global_expert_mode}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der schönen Header: {e}")
            # Fallback: Normale Header setzen
            self.table.setHorizontalHeaderLabels(headers)

    def _create_expert_headers(self, display_headers):
        """
        Erstellt ExpertMode-Header mit Anzeigename + technischem Namen.
        BEWÄHRTE LÖSUNG: Einfache zweizeilige Darstellung mit () für technische Namen.
        
        Args:
            display_headers: Liste der schönen Anzeigenamen
            
        Returns:
            Liste der erweiterten Header mit technischen Namen
        """
        try:
            enhanced_headers = []
            
            # Basis-Spalten vom persistenten Manager holen
            basis_columns = self.view_manager.basis_columns
            
            # Projektion holen um die Reihenfolge zu bekommen
            from column_projection_helper import get_projected_columns
            projected_columns = get_projected_columns(basis_columns)
            
            # Für jede projizierte Spalte den erweiterten Header erstellen
            for i, col in enumerate(projected_columns):
                if i < len(display_headers):
                    # BEWÄHRTE LÖSUNG: Schöner Name + (technischer_name)
                    display_name = display_headers[i]
                    technical_name = col['name']
                    enhanced_header = f"{display_name}\n({technical_name})"
                    enhanced_headers.append(enhanced_header)
                else:
                    enhanced_headers.append(display_headers[i] if i < len(display_headers) else "")
            
            logger.info(f"✅ {len(enhanced_headers)} ExpertMode-Header mit technischen Namen (bewährt) erstellt")
            return enhanced_headers
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der ExpertMode-Header: {e}")
            return display_headers
    
    def _load_table_data(self):
        """
        Lädt und zeigt Tabellendaten - ANGEPASST für persistenten Manager
        """
        try:
            logger.info("📊 Lade Tabelle vom persistenten ViewManager")
            
            # Tabellendaten vom persistenten Manager holen
            table_data = self.view_manager.get_table_data_for_display()
            
            if not table_data:
                logger.error("❌ Keine Tabellen-Daten vom persistenten ViewManager erhalten")
                self._create_fallback_table()
                return
            
            # Original-Logik für Tabellen-Befüllung verwenden
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            logger.info(f"📊 Befülle Tabelle: {len(headers)} Spalten, {len(rows)} Zeilen")
            
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            
            # ✅ SCHÖNE HEADER mit Modus-abhängigem Design setzen
            self._set_beautiful_headers(headers)
            
            # Tabellendaten befüllen - MIT TOOLTIPS für Abdatum (3. Dimension)
            abdatum_matrix = table_data.get('abdatum_matrix')  # Die 3. Dimension!
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, cell_value in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                    
                    # ✅ TOOLTIP für Abdatum anzeigen (3. Dimension der Basis-Matrix)
                    if abdatum_matrix is not None:
                        try:
                            ab_value = abdatum_matrix[row_idx][col_idx]
                            if ab_value is not None:
                                item.setToolTip(f"abdatum: {ab_value}")
                        except (IndexError, TypeError):
                            pass  # Kein Abdatum für diese Zelle
                    
                    self.table.setItem(row_idx, col_idx, item)
            
            # Spaltenbreiten anpassen
            self.table.resizeColumnsToContents()
            
            logger.info(f"✅ Tabelle erfolgreich befüllt: {len(rows)} Einträge")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Tabellen-Daten: {e}")
            import traceback
            traceback.print_exc()
            self._create_fallback_table()
    
    def _create_fallback_table(self):
        """Fallback-Tabelle wenn persistenter Manager nicht verfügbar - 1:1 ÜBERNOMMEN"""
        logger.warning("⚠️ Erstelle Fallback-Tabelle (persistenter ViewManager nicht verfügbar)")
        
        fallback_headers = ["Info", "Status"]
        fallback_data = [
            ["Persistenter DatenManager", "Nicht verfügbar"],
            ["Architektur", "KORREKT: DatenManager -> Widget"],
            ["Problem", "DatenManager-Registry oder Manager fehlt"]
        ]
        
        self.table.setColumnCount(len(fallback_headers))
        self.table.setRowCount(len(fallback_data))
        self.table.setHorizontalHeaderLabels(fallback_headers)
        
        for row_idx, row_data in enumerate(fallback_data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                self.table.setItem(row_idx, col_idx, item)
        
        self.table.resizeColumnsToContents()

    def reload(self):
        """
        PUBLIC RELOAD API - 1:1 ÜBERNOMMEN
        Zentrale reload() Methode ohne Parameter (Stichtag kommt aus zentraler Systemsteuerung)
        """
        try:
            logger.info("🔄 Widget reload() aufgerufen")
            
            # NEUE ARCHITEKTUR: Refresh über persistenten Manager
            if hasattr(self.view_manager, 'refresh_data'):
                logger.info("🔄 Refresh über persistenten ViewManager")
                self.view_manager.refresh_data()
            
            # Tabelle neu laden
            self._load_table_data()
            
            # Header aktualisieren (für Stichtag-Anzeige im ExpertMode)
            self.update_header_text()
            
            logger.info("✅ Widget reload abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Widget reload: {e}")
            import traceback
            traceback.print_exc()

    # WEITERE ORIGINAL-METHODEN können hier 1:1 übernommen werden...
