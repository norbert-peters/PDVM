# pdvm_view_widget.py
"""
PDVM View Widget - Zentrale Lösung
==================================

Zentrale Stichtag-Architektur implementiert.
Alle Widgets verwenden jetzt reload() ohne Parameter.
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMenuBar
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

class PdvmViewWidget(QWidget):
    def __init__(self, call_daten, parent=None):
        super().__init__(parent)
        self.call_daten = call_daten
        self.stichtag = call_daten.get('stichtag', 2025216.0)
        self.view_manager = None
        
        # UI Setup
        self.setup_ui()
        
        # Daten laden
        self.load_data()
        
    def setup_ui(self):
        """UI Komponenten erstellen"""
        layout = QVBoxLayout(self)
        
        # Table Widget
        self.table = QTableWidget(self)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
    def load_data(self):
        """Daten vom ViewManager laden"""
        logger.info(f"📊 Load data mit Stichtag: {self.stichtag}")
        
        # ViewManager Logik hier (vereinfacht)
        if not hasattr(self, 'view_manager') or self.view_manager is None:
            # ViewManager erstellen (vereinfacht)
            logger.info("🔧 Erstelle neuen ViewManager")
            from pdvm_view_daten_manager import PdvmViewDatenManager
            self.view_manager = PdvmViewDatenManager(self.call_daten)
        
        # Daten holen und Tabelle füllen
        self._reload_table_completely()
        
    def reload(self):
        """
        ZENTRALE STICHTAG-ARCHITEKTUR: Reload ohne Parameter
        
        NEUE ARCHITEKTUR (Schritt 1 umgesetzt):
        1. Zentralen Stichtag aus PdvmCentralStichtagManager abrufen
        2. Call-Daten damit synchronisieren  
        3. View komplett neu aufbauen (wie Neustart ohne DB-Reload)
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            # Import der globalen Instanz aus PDVM-Systemstart
            import sys
            import os
            
            # PDVM-Systemstart Modul importieren für globalen StichtagManager
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
        """
        logger.info("🔄 Lade Tabelle komplett neu")
        
        if self.view_manager and hasattr(self.view_manager, 'get_filtered_data'):
            # Daten vom ViewManager holen
            data = self.view_manager.get_filtered_data()
            
            # Tabelle neu aufbauen
            if data and len(data) > 0:
                self.table.setRowCount(len(data))
                self.table.setColumnCount(len(data[0]) if data[0] else 0)
                
                # Daten einfügen (vereinfacht)
                for row_idx, row_data in enumerate(data):
                    for col_idx, cell_value in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_value))
                        self.table.setItem(row_idx, col_idx, item)
                        
                logger.info(f"📊 Tabelle neu geladen: {len(data)} Zeilen")
            else:
                self.table.setRowCount(0)
                logger.info("📊 Tabelle geleert (keine Daten)")
        else:
            logger.warning("⚠️ ViewManager nicht verfügbar für Tabelle-Reload")
            
    def close_view(self):
        """View schließen"""
        logger.info("🚪 Schließe PDVM View")
        self.close()
