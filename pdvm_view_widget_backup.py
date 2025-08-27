# pdvm_view_widget.py
"""
PDVM View Widget - Zentrale Lösung
==================================

Einfacher Aufruf: pdvm_modern_view(frame_guid)
- call_daten: {view_guid, user_guid, stichtag}
- parent: als separater Parameter
- ViewManager wird mit Widget initialisiert
- Oberfläche: Basistabelle + Menü rechts oben
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QMenu, QAction, QSplitter, QFrame, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from pdvm_spalten_parameter_dialog import PdvmSpaltenParameterDialog
from pdvm_view_daten_manager import PdvmViewDatenManager

logger = logging.getLogger(__name__)

class PdvmViewWidget(QWidget):
    """
    Zentrale PDVM View Lösung
    
    Aufruf: widget = PdvmViewWidget(call_daten, parent)
    call_daten = {
        "view_guid": "...",
        "user_guid": "...", 
        "stichtag": float
    }
    """
    
    # Signals
    settings_requested = pyqtSignal()
    expert_mode_toggled = pyqtSignal(bool)
    filter_toggled = pyqtSignal(bool)
    
    def __init__(self, call_daten, parent=None):
        super().__init__(parent)
        
        self.call_daten = call_daten 
        self.view_guid = call_daten.get("view_guid")
        self.user_guid = call_daten.get("user_guid") 
        self.stichtag = call_daten.get("stichtag")
        
        # Status-Variablen
        self.expert_mode_active = False
        self.is_expert_mode = False  # Alias für Kompatibilität
        self.filter_panel_visible = False
        
        # ViewManager wird mit Widget initialisiert
        self.view_manager = None
        self._init_view_manager()
        
        # UI aufbauen
        self.setup_ui()
        
        # Daten laden
        self.load_data()
    
    def _init_view_manager(self):
        """ViewManager mit Widget initialisieren"""
        try:
            
            self.view_manager = PdvmViewDatenManager(
                call_daten=self.call_daten,
                widget=self
            )
            
            logger.info(f"✅ ViewManager initialisiert für View: {self.view_guid}")
            
        except Exception as e:
            logger.error(f"❌ ViewManager Initialisierung fehlgeschlagen: {e}")
            self.view_manager = None
    
    def setup_ui(self):
        """UI aufbauen: Tabelle + Menü rechts oben + Filter-Panel links"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header mit Menü rechts
        header_layout = QHBoxLayout()
        
        # Überschrift links
        view_header = self.call_daten.get("view_header", "PDVM Ansicht")
        self.header_label = QLabel(view_header)
        self.header_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        header_layout.addWidget(self.header_label)
        
        # Spacer zwischen Überschrift und Menü
        header_layout.addStretch()
        
        # Einstellungen-Menü rechts
        self.settings_button = QPushButton("⚙️ Einstellungen")
        self.settings_button.setMaximumWidth(150)
        
        # Menü erstellen
        self.menu = QMenu(self)
        
        # 1. Spalten-Parameter
        spalten_action = QAction("📋 Spalten-Parameter", self)
        spalten_action.triggered.connect(self._open_spalten_parameter)
        self.menu.addAction(spalten_action)
        
        # 2. Expert-Mode ein/aus (nur bei mode='admin')
        mode = self.call_daten.get("mode", "user")
        if mode == "admin":
            self.expert_action = QAction("👥 Expert-Mode EIN", self)
            self.expert_action.triggered.connect(self._toggle_expert_mode)
            self.menu.addAction(self.expert_action)
            logger.info("🔧 Expert-Mode Menüpunkt hinzugefügt (Admin-Modus)")
        else:
            self.expert_action = None
            logger.info("🔧 Expert-Mode Menüpunkt nicht verfügbar (User-Modus)")
        
        # 3. Filter ein/aus
        self.filter_action = QAction("🔍 Filter EIN", self)
        self.filter_action.triggered.connect(self._toggle_filter)
        self.menu.addAction(self.filter_action)
        
        self.settings_button.setMenu(self.menu)
        header_layout.addWidget(self.settings_button)
        
        main_layout.addLayout(header_layout)
        
        # Content-Bereich mit Splitter
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Filter-Panel (links, initial versteckt)
        self.filter_panel = self._create_filter_panel()
        self.content_splitter.addWidget(self.filter_panel)
        self.filter_panel.hide()  # Initial versteckt
        
        # Tabelle (rechts/hauptbereich)
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        
        # Header-Stil
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        
        self.content_splitter.addWidget(self.table)
        
        # Splitter-Verhältnis: Filter 25%, Tabelle 75%
        self.content_splitter.setSizes([250, 750])
        
        main_layout.addWidget(self.content_splitter)
        
        # Widget-Stil
        self.setStyleSheet("""
            PdvmViewWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #adb5bd;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                selection-background-color: #cce5ff;
                alternate-background-color: #f8f9fa;
                font-size: 10pt;
            }
        """)
    
    def _create_filter_panel(self):
        """Filter-Panel erstellen"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Filter-Titel
        title = QPushButton("🔍 Filter-Bereich")
        title.setEnabled(False)
        title.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                font-weight: bold;
                padding: 8px;
            }
        """)
        layout.addWidget(title)
        
        # Platz für Filter-Erweiterungen
        layout.addStretch()
        
        return panel
    
    def _toggle_expert_mode(self):
        """Expert-Mode umschalten (nur bei Admin-Modus)"""
        try:
            # Prüfen ob Expert-Mode verfügbar ist
            if not self.expert_action:
                logger.warning("⚠️ Expert-Mode nicht verfügbar (kein Admin-Modus)")
                return
            
            # Neuen Mode bestimmen
            new_mode = "expert" if not self.expert_mode_active else "normal"
            
            # Mode im DatenManager wechseln
            if hasattr(self.view_manager, 'switch_view_mode'):
                success = self.view_manager.switch_view_mode(new_mode)
                if not success:
                    logger.warning(f"⚠️ Mode-Wechsel zu {new_mode} fehlgeschlagen")
                    return
                
                self.expert_mode_active = (new_mode == "expert")
                self.is_expert_mode = self.expert_mode_active  # Alias synchron halten
            else:
                # Fallback für alte Implementierung
                self.expert_mode_active = not self.expert_mode_active
                self.is_expert_mode = self.expert_mode_active  # Alias synchron halten
            
            # Menü-Text aktualisieren
            mode_text = "AUS" if self.expert_mode_active else "EIN"
            self.expert_action.setText(f"👥 Expert-Mode {mode_text}")
            
            # Signal senden
            self.expert_mode_toggled.emit(self.expert_mode_active)
            
            # Daten neu laden
            self.load_data()
            
            logger.info(f"🔧 Expert-Mode {'EIN' if self.expert_mode_active else 'AUS'}")
            
        except Exception as e:
            logger.error(f"❌ Expert-Mode Toggle Fehler: {e}")
    
    def _toggle_filter(self):
        """Filter-Panel ein/ausblenden"""
        try:
            self.filter_panel_visible = not self.filter_panel_visible
            
            # Panel anzeigen/verstecken
            if self.filter_panel_visible:
                self.filter_panel.show()
                filter_text = "AUS"
            else:
                self.filter_panel.hide()
                filter_text = "EIN"
            
            # Menü-Text aktualisieren
            self.filter_action.setText(f"🔍 Filter {filter_text}")
            
            # Signal senden
            self.filter_toggled.emit(self.filter_panel_visible)
            
            logger.info(f"🔍 Filter-Panel {'angezeigt' if self.filter_panel_visible else 'ausgeblendet'}")
            
        except Exception as e:
            logger.error(f"❌ Filter Toggle Fehler: {e}")
    
    def load_data(self):
        """Daten laden und Tabelle füllen - NEUE LINEARE LÖSUNG mit PdvmSpaltenManager"""
        try:
            if not self.view_manager:
                logger.warning("⚠️ Kein ViewManager verfügbar")
                return
            
            # Prüfe ob ColumnControl verfügbar ist
            if not hasattr(self.view_manager, 'column_control') or not self.view_manager.column_control:
                logger.warning("⚠️ Kein ColumnControl im ViewManager verfügbar")
                return
            
            # DATEN LADEN: Stelle sicher, dass echte Daten im ColumnControl sind
            logger.info("🔄 Lade Datensätze in ColumnControl...")
            loaded_records = self.view_manager.load_records_data(limit=100)
            logger.info(f"📊 {loaded_records} Datensätze geladen")
            
            # NEUER LINEARER ANSATZ: PdvmSpaltenManager verwenden
            logger.info("🔄 Verwende neue lineare PdvmSpaltenManager Lösung...")
            
            from pdvm_spalten_manager import PdvmSpaltenManager
            
            # SpaltenManager mit ColumnControl aus ViewManager erstellen
            spalten_manager = PdvmSpaltenManager(self.view_manager.column_control)
            
            # Widget-fertige Tabellendaten abrufen (returns tuple: rows, headers)
            rows, headers = spalten_manager.get_widget_ready_table()
            
            if not headers:
                logger.warning("⚠️ Keine Headers von SpaltenManager erhalten")
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                return
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(headers))
            
            # Header setzen
            self.table.setHorizontalHeaderLabels(headers)
            
            # Daten einfügen - rows ist jetzt List[Dict]
            for row_idx, row_dict in enumerate(rows):
                for col_idx, header in enumerate(headers):
                    value = row_dict.get(header, '')
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
                    self.table.setItem(row_idx, col_idx, item)
            
            # Auto-Resize Spalten
            self.table.resizeColumnsToContents()
            
            # Alternating row colors
            self.table.setAlternatingRowColors(True)
            
            logger.info(f"✅ LINEARE TABELLE geladen: {len(rows)} Zeilen, {len(headers)} Spalten")
            logger.info(f"📊 Headers: {headers[:3]}{'...' if len(headers) > 3 else ''}")
            
            # Zeige Beispieldaten im Log
            if rows and len(rows[0]) > 0:
                sample_row = rows[0]
                sample_values = [str(sample_row.get(h, ''))[:20] for h in headers[:3]]
                logger.info(f"📋 Erste Zeile Beispiel: {sample_values}")
            
        except Exception as e:
            logger.error(f"❌ Daten laden fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Fallback: Leere Tabelle
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
    
    def _open_spalten_parameter(self):
        """Öffnet den Spaltenparameter-Dialog"""
        try:
            if not self.view_manager:
                logger.error("❌ ViewManager nicht verfügbar für Spaltenparameter")
                return
            
            # Aktuellen Mode bestimmen
            current_mode = "expert" if self.is_expert_mode else "normal"
            
            # DatenManager aus ViewManager holen - OHNE PROVIDER!
            daten_manager = self.view_manager  # view_manager IST der DatenManager
            
            # Dialog öffnen - EINFACHE LÖSUNG nur 3 Parameter
            dialog = PdvmSpaltenParameterDialog(
                parent=self,
                mode=current_mode,
                daten_manager=daten_manager
            )
            
            # Dialog ausführen
            if dialog.exec_() == dialog.Accepted:
                # Änderungen wurden übernommen
                logger.info(f"✅ Spaltenparameter übernommen - Mode: {current_mode}")
                
                # Tabelle neu laden
                self.reload_table()
            else:
                logger.info(f"🔄 Spaltenparameter-Dialog abgebrochen - Mode: {current_mode}")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen der Spaltenparameter: {e}")
            self.show_message(f"Fehler beim Öffnen der Spaltenparameter: {e}")
    
    def reload_data(self):
        """Lädt die Tabelle neu (nach Änderungen an Spaltenparametern)"""
        try:
            logger.info("🔄 Tabelle wird neu geladen...")
            self.load_data()
        except Exception as e:
            logger.error(f"❌ Fehler beim Neuladen der Tabelle: {e}")
    
    def reload(self):
        """
        ZENTRALE STICHTAG-ARCHITEKTUR: View mit zentralem Stichtag refreshen
        
        NEUE ARCHITEKTUR:
        - Kein Stichtag als Parameter mehr!
        - Stichtag wird zentral aus StichtagManager abgerufen
        - Eliminiert Synchronisationsfehler
        - Vereinfacht Code (keine Parameter-Weitergabe)
        
        Der einheitliche Refresh-Weg:
        1. Zentralen Stichtag aus PdvmCentralStichtagManager abrufen
        2. Call-Daten damit synchronisieren  
        3. View komplett neu aufbauen (wie Neustart ohne DB-Reload)
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            # Import der globalen Instanz aus pdvm_systemstart
            import sys
            import os
            
            # pdvm_systemstart Modul importieren für globalen StichtagManager
            # Fallback falls Import nicht funktioniert
            try:
                # Versuch 1: Direkter Import (falls im gleichen Verzeichnis)
                import importlib.util
                spec = importlib.util.spec_from_file_location("pdvm_systemstart", 
                    os.path.join(os.path.dirname(__file__), "PDVM-Systemstart.py"))
                if spec and spec.loader:
                    pdvm_systemstart = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(pdvm_systemstart)
                    central_manager = pdvm_systemstart.get_global_stichtag_manager()
                else:
                    raise ImportError("Spec nicht gefunden")
            except Exception as import_error:
                logger.warning(f"⚠️ Globaler StichtagManager nicht verfügbar: {import_error}")
                # FALLBACK: Verwende lokalen Stichtag ohne zentrale Abfrage
                new_stichtag = self.stichtag if hasattr(self, 'stichtag') else self.call_daten.get('stichtag', 2025216.0)
                logger.info(f"📍 FALLBACK: Verwende aktuellen Widget-Stichtag: {new_stichtag}")
                central_manager = None
            
            # Stichtag abrufen (zentral oder fallback)
            if central_manager:
                new_stichtag = central_manager.get_stichtag_float()
                logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - Refresh mit zentralem Stichtag: {new_stichtag}")
            else:
                logger.info(f"🔄 FALLBACK RELOAD - Refresh mit aktuellem Stichtag: {new_stichtag}")
            
            logger.info(f"📍 Alter Widget-Stichtag: {getattr(self, 'stichtag', 'N/A')}")
            
            # SYNCHRONISATION mit Stichtag (zentral oder fallback)
            old_stichtag = getattr(self, 'stichtag', None)
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            logger.info(f"✅ Stichtag synchronisiert: Widget={self.stichtag}, CallDaten={self.call_daten['stichtag']}")
            
            # VIEW NEU AUFBAUEN (einheitlicher Code, ohne DB-Reload)
            logger.info("🏗️ Baue View neu auf")
            
            # ViewManager refreshen
            if self.view_manager:
                logger.info(f"🔄 ViewManager-Refresh mit Stichtag: {new_stichtag}")
                
                # Prüfe welche Refresh-Methode verfügbar ist
                if hasattr(self.view_manager, 'refresh_with_central_stichtag'):
                    # NEUE ZENTRALE METHODE
                    refreshed_count = self.view_manager.refresh_with_central_stichtag()
                    logger.info(f"📊 {refreshed_count} Datensätze mit zentraler Methode refresht")
                elif hasattr(self.view_manager, 'refresh_with_stichtag'):
                    # FALLBACK: Alte Methode
                    refreshed_count = self.view_manager.refresh_with_stichtag(new_stichtag)
                    logger.info(f"📊 {refreshed_count} Datensätze mit alter Methode refresht")
                else:
                    logger.warning("⚠️ Keine refresh-Methode im ViewManager verfügbar")
                    refreshed_count = 0
                
                # Tabelle komplett neu laden
                if refreshed_count > 0:
                    self._reload_table_completely()
                    logger.info(f"✅ REFRESH erfolgreich: View neu aufgebaut")
                else:
                    logger.info("🔄 Fallback: load_data() wegen fehlendem refresh")
                    self.load_data()
            else:
                # Fallback: Kompletter Neuaufbau
                logger.info("🔄 Fallback: Kompletter View-Neuaufbau")
                self.load_data()
                
        except Exception as e:
            logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Bei Fehler: Stichtag zurücksetzen falls möglich
            if 'old_stichtag' in locals() and old_stichtag is not None:
                logger.warning(f"🔄 Setze Stichtag zurück: {new_stichtag} → {old_stichtag}")
                self.stichtag = old_stichtag
                self.call_daten['stichtag'] = old_stichtag

    def reload_with_stichtag(self, new_stichtag):
        """
        KOMPATIBILITÄTS-METHODE: Ruft zentrale reload() auf
        
        WICHTIGER HINWEIS:
        Diese Methode ist nur noch für Kompatibilität da!
        Neue Architektur: Verwende reload() ohne Parameter!
        
        Args:
            new_stichtag (float): Wird ignoriert - zentraler Stichtag wird verwendet
        """
        logger.warning("⚠️ reload_with_stichtag() ist deprecated! Verwende reload() mit zentralem Stichtag")
        logger.info(f"📍 Übergebener Stichtag {new_stichtag} wird ignoriert - verwende zentralen Stichtag")
        
        # Zentrale Reload-Methode aufrufen
        self.reload()
    
    def _reload_table_completely(self):
        """
        EINHEITLICHES TABELLE-NEULADEN
        
        Identisch mit load_data(), aber ohne ViewManager neu zu erstellen.
        Verwendet den einheitlichen PdvmSpaltenManager-Code.
        
        WICHTIG: Prüft Stichtag-Konsistenz vor Tabellen-Aufbau
        """
        try:
            logger.info("🔄 EINHEITLICHES TABELLE-NEULADEN (wie load_data)")
            
            if not self.view_manager:
                logger.warning("⚠️ Kein ViewManager für Tabelle-Neuladen")
                return
            
            # WICHTIGE KONSISTENZ-PRÜFUNG: Stichtage synchron?
            widget_stichtag = self.stichtag
            viewmanager_stichtag = getattr(self.view_manager, 'stichtag', None)
            calldata_stichtag = self.call_daten.get('stichtag', None)
            
            if widget_stichtag != viewmanager_stichtag or widget_stichtag != calldata_stichtag:
                logger.warning(f"⚠️ STICHTAG INKONSISTENZ erkannt:")
                logger.warning(f"   Widget: {widget_stichtag}")
                logger.warning(f"   ViewManager: {viewmanager_stichtag}")
                logger.warning(f"   CallDaten: {calldata_stichtag}")
                
                # Korrigiere die Inkonsistenz
                if viewmanager_stichtag != widget_stichtag:
                    logger.info(f"🔧 Korrigiere ViewManager-Stichtag: {viewmanager_stichtag} → {widget_stichtag}")
                    self.view_manager.stichtag = widget_stichtag
                    if hasattr(self.view_manager, 'call_daten') and self.view_manager.call_daten:
                        self.view_manager.call_daten['stichtag'] = widget_stichtag
            else:
                logger.info(f"✅ Stichtag-Konsistenz OK: {widget_stichtag}")
            
            # EINHEITLICHER CODE: Exakt wie in load_data()
            from pdvm_spalten_manager import PdvmSpaltenManager
            
            # SpaltenManager erstellen
            spalten_manager = PdvmSpaltenManager(self.view_manager.column_control)
            
            # Widget-fertige Tabelle abrufen (EINHEITLICH)
            rows, headers = spalten_manager.get_widget_ready_table()
            
            logger.info(f"📊 Tabelle neu geladen: {len(rows)} Zeilen × {len(headers)} Spalten")
            
            # DEBUGGING: Erste paar Zeilen zur Kontrolle
            if len(rows) > 0:
                for i, row_dict in enumerate(rows[:2]):  # Erste 2 Zeilen
                    guid = str(row_dict.get('ID', 'N/A'))[:12]
                    familienname = row_dict.get('Familienname', '')
                    logger.info(f"   Refreshte Zeile {i+1}: GUID={guid}..., Familienname='{familienname}' {'(LEER)' if not familienname else '(GEFÜLLT)'}")
            
            # Tabelle komplett neu aufbauen (EINHEITLICH)
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            
            # Daten einfügen (EINHEITLICH)
            for row_idx, row_dict in enumerate(rows):
                for col_idx, header in enumerate(headers):
                    value = row_dict.get(header, '')
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, item)
            
            # Formatierung (EINHEITLICH)
            self.table.resizeColumnsToContents()
            self.table.setAlternatingRowColors(True)
            
            logger.info("✅ EINHEITLICHES TABELLE-NEULADEN abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim einheitlichen Tabelle-Neuladen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    def reload_table(self):
        """Lädt die Tabelle neu (nach Änderungen an Spaltenparametern)"""
        try:
            logger.info("🔄 Tabelle wird neu geladen...")
            self.load_data()
        except Exception as e:
            logger.error(f"❌ Fehler beim Neuladen der Tabelle: {e}")
    
    def show_message(self, message):
        """Zeigt eine einfache Nachricht an"""
        from PyQt5.QtWidgets import QMessageBox
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Information")
        msg_box.setText(str(message))
        msg_box.exec_()
