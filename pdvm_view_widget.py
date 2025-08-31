# pdvm_view_widget.py
"""
PDVM View Widget - Zentrale Lösung
==================================

Zentrale Stichtag-Architektur implementiert.
Alle Widgets verwenden jetzt reload() ohne Parameter.
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
                           QHeaderView, QPushButton, QMenuBar, QLabel, QMenu, QAction)
from PyQt5.QtCore import Qt

# GLOBALE IMPORTS: Einfacher Zugriff auf zentrale Funktionen

# Globale Instanz direkt importieren
import pdvm_central_systemsteuerung_global
gcs = pdvm_central_systemsteuerung_global.central_systemsteuerung

logger = logging.getLogger(__name__)

class PdvmViewWidget(QWidget):
    def __init__(self, call_daten, parent=None, reload_callback=None):
        super().__init__(parent)
        self.call_daten = call_daten
        self.view_manager = None
        self.reload_callback = reload_callback  # Parent-Callback für echten Reload

        # ExpertMode-Status: 🎯 SUPER EINFACH mit neuer CentralSystemsteuerung

        self.header_label = None  # Referenz auf Header-Label für Updates

        # UI Setup
        self.setup_ui()

        # Daten laden
        self.load_data()

    def setup_ui(self):
        """UI Komponenten erstellen"""
        layout = QVBoxLayout(self)
        
        # Header-Label hinzufügen
        from PyQt5.QtWidgets import QLabel
        
    # Stichtag aus zentraler Systemsteuerung holen
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
        Erstellt den Header-Text basierend auf view_header und ExpertMode
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
        Aktualisiert den Header-Text nach ExpertMode-Änderung
        """
        # BEREINIGT: ExpertMode ist bereits verfügbar - kein Lazy Loading nötig!
        
        # Header-Text neu erstellen und setzen
        if self.header_label:
            new_text = self.get_header_text()
            self.header_label.setText(new_text)
            logger.info(f"✅ Header-Text aktualisiert: '{new_text}'")
    
    def create_settings_menu(self):
        """
        Erstellt das Einstellungs-Menü in der Kopfzeile
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
        """Spalten verwalten: Öffnet den Matrix-Spaltendialog und übernimmt Änderungen."""
#        try:
        from pdvm_view_column_settings_dialog import ColumnSettingsDialog
        # Hole die aktuelle Spaltenprojektion und den Modus direkt aus dem Datenmanager
        display_columns = self.view_manager.get_table_data_for_display()
        columns = [col for col in self.view_manager.basis_columns if col['name'] in display_columns]
        # Dialog bestimmt Modus selbst aus Systemsteuerung
        dlg = ColumnSettingsDialog(columns, self)
        logger.info(f"🔧 Öffne Spaltendialog mit {len(columns)} Spalten (ExpertMode: {gcs.global_expert_mode})")
        if dlg.exec_() and dlg.result_controls is not None:
            # Schreibe die neuen Controls in die Systemsteuerung
            persist_map = {col['name']: {
                'show': col['show'],
                'expertOrder': col['expertOrder'],
                'displayOrder': col['displayOrder']
            } for col in dlg.result_controls}
            gcs.set_value(gruppe=self.view_manager.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
            gcs.save_values()
            # Nur Controls und Projektion neu laden, Datenbasis bleibt erhalten
            self.view_manager.refresh_controls_and_projection()
            logger.info("✅ Spalteneinstellungen übernommen und Projektion neu geladen (ohne Datenbasis-Neuladen)")
            self.reload()
#        except Exception as e:
#            logger.error(f"❌ Fehler beim Öffnen des Spaltendialogs: {e}")
        
    def on_expert_modus_toggle(self):
        """Moduswechsel zwischen ExpertMode (all) und NormalMode (show) mit Persistenz in Systemsteuerung"""
        try:
            new_mode = not gcs.global_expert_mode
            # Wert persistent in Systemsteuerung speichern
            try:
                gcs.set_value(gruppe=gcs.user_guid, feld="ExpertMode", wert=new_mode, ab_zeit=1001.0)
                gcs.save_values()
                logger.info(f"� ExpertMode in Systemsteuerung gespeichert: {new_mode}")
            except Exception as e2:
                logger.warning(f"⚠️ Fehler beim Speichern von ExpertMode in Systemsteuerung: {e2}")
            # Wert aus Systemsteuerung holen (immer synchronisieren)
            self.reload()
        except Exception as e:
            logger.error(f"❌ Fehler beim Moduswechsel: {e}")

    def on_filter_toggle(self):
        """Filter ein/aus - noch ohne Funktion"""
        logger.info("🔍 Filter Toggle geklickt (noch ohne Funktion)")
        
    def load_data(self):
        """
        BEREINIGT: Daten vom ViewManager laden mit zentralem Stichtag
        - Kein ViewManager ODER first_call=True → Neuen ViewManager erstellen  
        - ViewManager vorhanden UND first_call=False → Bestehenden verwenden
        """
        # BEREINIGT: ExpertMode ist bereits beim Widget-Init geladen - kein Lazy Loading nötig!
        
        try:
            first_call = self.call_daten.get('first_call', True)
            logger.info(f"🔧 first_call={first_call}")
            
            # EINFACHE ENTSCHEIDUNG:
            if not hasattr(self, 'view_manager') or self.view_manager is None or first_call:
                # Fall 1: Neuen ViewManager erstellen (erstes Laden oder Tabellenwechsel)
                logger.info("🔧 Erstelle neuen ViewManager (kein Manager vorhanden oder first_call=True)")
                
                # BEREINIGT: Call-Daten ohne 'stichtag' - ViewManager holt zentral
                initial_call_data = dict(self.call_daten)
                initial_call_data['first_call'] = True
                # BEREINIGT: 'stichtag' aus call_daten entfernen
                initial_call_data.pop('stichtag', None)
                
                from pdvm_view_daten_manager import PdvmViewDatenManager
                self.view_manager = PdvmViewDatenManager(initial_call_data)
            else:
                # Fall 2: Bestehenden ViewManager für Stichtag-Refresh verwenden
                logger.info("🔄 Verwende bestehenden ViewManager (first_call=False - nur Refresh)")
                
                # BEREINIGT: Stichtag-Update nicht nötig - ViewManager holt zentral
                logger.info("✅ ViewManager verwendet zentralen Stichtag")
            
            # Daten holen und Tabelle füllen
            self._load_table_data()
            
            # 🔄 Header nach ExpertMode-Laden aktualisieren
            self.update_header_text()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # FALLBACK: Zeige wenigstens eine leere Tabelle mit Grundstruktur
            self._create_fallback_table()
            
    def _load_table_data(self):
        """
        Lädt Daten vom ViewManager und füllt die Tabelle (Matrix-Logik wie im Prototyp)
        """
        logger.info("📊 Lade Tabelle mit Matrix-Logik und ColumnControls (Prototyp)")
        try:
            if self.view_manager:
                # Hole Daten und Spaltenprojektion ausschließlich aus get_table_data_for_display
                data, display_columns = self.view_manager.get_table_data_for_display()
                columns = [col for col in self.view_manager.basis_columns if col['name'] in display_columns]
                headers = [col.get('spaltenueberschrift', col.get('name', '')) for col in columns]
                col_names = [col['name'] for col in columns]
                abdatum_matrix = None
                if hasattr(self.view_manager, 'get_abdatum_matrix'):
                    abdatum_matrix = self.view_manager.get_abdatum_matrix(show_only=(not gcs.global_expert_mode))
                if data and len(data) > 0 and headers:
                    self.table.setRowCount(len(data))
                    self.table.setColumnCount(len(col_names))
                    self.table.setHorizontalHeaderLabels([str(h) for h in headers])
                    for row_idx, row_data in enumerate(data):
                        for col_idx, cell_value in enumerate(row_data):
                            item = QTableWidgetItem(str(cell_value))
                            # Tooltip für Abdatum anzeigen, falls vorhanden
                            if abdatum_matrix is not None:
                                try:
                                    ab_value = abdatum_matrix[row_idx][col_idx]
                                    if ab_value is not None:
                                        item.setToolTip(f"abdatum: {ab_value}")
                                except Exception:
                                    pass
                            self.table.setItem(row_idx, col_idx, item)
                    self.table.resizeColumnsToContents()
                    logger.info(f"📊 Tabelle geladen: {len(data)} Zeilen mit Matrix-Logik (Datenmanager-Projektion)")
                else:
                    logger.warning(f"📊 Keine Daten oder keine Spaltennamen erhalten: data={len(data)}, headers={headers}")
                    self._create_fallback_table()
            else:
                logger.warning("⚠️ ViewManager nicht verfügbar für Matrix-Datenladen")
                self._create_fallback_table()
        except Exception as e:
            logger.error(f"❌ Fehler beim Matrix-Tabelle-Laden: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            self._create_fallback_table()
            
    def _create_fallback_table(self):
        """Erstellt eine Fallback-Tabelle wenn ViewManager nicht funktioniert"""
        logger.info("🔧 Erstelle Fallback-Tabelle...")
        
        # Grundlegende Tabelle mit Standard-Spalten
        headers = ["GUID", "Vorname", "Nachname", "Geburtsdatum", "Status"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Test-Daten einfügen
        test_data = [
            ["54073c2c", "Test", "Person", "01.01.1980", "Aktiv"],
            ["test-guid", "Fallback", "Modus", "ViewManager Error", "Debug"]
        ]
        
        self.table.setRowCount(len(test_data))
        for row_idx, row_data in enumerate(test_data):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                self.table.setItem(row_idx, col_idx, item)
        
        # Spaltenbreite anpassen
        self.table.resizeColumnsToContents()
        
        logger.info(f"✅ Fallback-Tabelle erstellt mit {len(test_data)} Test-Zeilen")
        
    def reload(self):
        """
        PARENT-BASIERTE RELOAD-ARCHITEKTUR:
        
        Das Widget kann sich nicht selbst komplett neu aufbauen.
        Stattdessen:
        1. Prüfen ob reload_callback verfügbar ist
        2. Falls ja: Parent informieren dass neues Widget erstellt werden soll
        3. Falls nein: Fallback mit einfacher Datenaktualisierung
        """
        logger.info("🔄 === PARENT-BASIERTE RELOAD-ARCHITEKTUR ===")
        
        try:
            # SCHRITT 1: Parent-Callback verwenden (bevorzugte Lösung)
            if self.reload_callback and callable(self.reload_callback):
                logger.info("🔄 Verwende Parent-Callback für echten Widget-Reload")
                
                # BEREINIGT: call_daten für Refresh ohne 'stichtag' 
                reload_call_daten = dict(self.call_daten)
                reload_call_daten['first_call'] = False
                # BEREINIGT: Entferne schädlichen 'stichtag' aus call_daten
                reload_call_daten.pop('stichtag', None)
                
                # Parent über Reload informieren - Parent erstellt neues Widget
                self.reload_callback(reload_call_daten)
                logger.info("✅ Parent-Callback für Widget-Reload ausgeführt")
                return
                
            # SCHRITT 2: Fallback - einfache Datenaktualisierung (falls kein Parent-Callback)
            logger.info("⚠️ Kein Parent-Callback - verwende Fallback-Reload")
            
            # first_call auf False setzen damit kein DB-Reload stattfindet
            if hasattr(self, 'call_daten') and self.call_daten:
                self.call_daten['first_call'] = False
                logger.info("✅ first_call = False gesetzt")
            
            # Einfach load_data() aufrufen - Rest regelt die first_call Logic
            self.load_data()
            logger.info("✅ Fallback-reload() mit first_call=False abgeschlossen")
                
        except Exception as e:
            logger.error(f"❌ Reload fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def reload_with_stichtag(self, new_stichtag):
        """
        KOMPATIBILITÄTS-METHODE: Ruft einfache reload() auf
        
        WICHTIGER HINWEIS:
        Diese Methode ist nur noch für Kompatibilität da!
        Neue Architektur: Verwende reload() ohne Parameter!
        
        Args:
            new_stichtag (float): Wird ignoriert - verwende einfach reload()
        """
        logger.warning("⚠️ reload_with_stichtag() ist deprecated! Verwende einfache reload()")
        logger.info(f"📍 Übergebener Stichtag {new_stichtag} wird ignoriert")
        
        # Einfache Reload-Methode aufrufen
        self.reload()
            
    def close_view(self):
        """View schließen"""
        logger.info("🚪 Schließe PDVM View")
        self.close()
