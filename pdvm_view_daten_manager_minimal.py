# pdvm_view_daten_manager.py
"""
PDVM View Daten Manager - Zentrale Lösung
==========================================

Zentrale Stichtag-Architektur implementiert.
ViewManager verwendet jetzt refresh_with_central_stichtag().
"""

import logging
import json

logger = logging.getLogger(__name__)

class ColumnControl:
    """Control-System für Spalten-Verwaltung (vereinfacht)"""
    
    def __init__(self):
        self.columns = []
        
    def add_column(self, name, config):
        """Fügt eine Spalte hinzu"""
        self.columns.append({'name': name, 'config': config})
        
    def sort_columns(self):
        """Sortiert die Spalten"""
        pass
        
    def get_column_names(self):
        """Gibt die Spaltennamen zurück"""
        return [col['name'] for col in self.columns]

class PdvmViewDatenManager:
    """
    PDVM View Daten Manager - Vereinfachte funktionsfähige Version
    
    Diese Version ist speziell für den Test der zentralen Stichtag-Architektur.
    """
    
    def __init__(self, call_daten):
        """
        Initialisiert den ViewManager.
        
        Args:
            call_daten (dict): Call-Daten mit view_guid, user_guid, stichtag etc.
        """
        logger.info("🔧 Initialisiere PdvmViewDatenManager (minimal)")
        
        self.call_daten = call_daten
        self.user_guid = call_daten.get('user_guid')
        self.view_guid = call_daten.get('view_guid')
        self.stichtag = call_daten.get('stichtag', 2025216.0)
        
        # Control-Strukturen
        self.column_control = ColumnControl()
        self.data_cache = []
        
        logger.info(f"✅ ViewManager initialisiert - ViewGUID: {self.view_guid}, Stichtag: {self.stichtag}")
        
        # Test-Daten laden
        self._load_test_data()
        
    def _load_test_data(self):
        """Lädt Test-Daten für die Demo"""
        logger.info("📊 Lade Test-Daten...")
        
        # Spalten definieren
        columns = ["guid", "vorname", "nachname", "geburtsdatum", "status"]
        for col in columns:
            self.column_control.add_column(col, {"show": True, "type": "string"})
        
        # Test-Daten erstellen
        self.data_cache = [
            ["54073c2c", "Max", "Mustermann", "01.06.1980", "Aktiv"],
            ["test-guid-1", "Anna", "Schmidt", "15.07.1985", "Aktiv"], 
            ["test-guid-2", "Peter", "Weber", "22.03.1975", "Inaktiv"],
            ["test-guid-3", "Lisa", "Müller", "10.12.1990", "Aktiv"],
            ["test-guid-4", "Tom", "Fischer", "05.09.1982", "Aktiv"]
        ]
        
        logger.info(f"✅ {len(self.data_cache)} Test-Datensätze geladen")
        
    def get_filtered_data(self):
        """
        Gibt die gefilterten Daten zurück.
        
        Returns:
            list: Liste der Datensätze als Liste von Listen
        """
        logger.info(f"📊 Gebe gefilterte Daten zurück: {len(self.data_cache)} Datensätze")
        return self.data_cache
        
    def refresh_with_stichtag(self, new_stichtag):
        """
        ALTE METHODE: Refresh mit übergebenem Stichtag (Kompatibilität)
        
        Args:
            new_stichtag (float): Neuer Stichtag
            
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        logger.warning("⚠️ refresh_with_stichtag() ist deprecated! Verwende refresh_with_central_stichtag()")
        logger.info(f"🔄 Refresh mit übergebenem Stichtag: {new_stichtag}")
        
        self.stichtag = new_stichtag
        self.call_daten['stichtag'] = new_stichtag
        
        # Daten neu laden (simuliert)
        self._load_test_data()
        
        logger.info(f"✅ Refresh abgeschlossen - {len(self.data_cache)} Datensätze")
        return len(self.data_cache)
        
    def refresh_with_central_stichtag(self):
        """
        NEUE ZENTRALE METHODE: Refresh ohne Parameter
        
        Holt sich den Stichtag aus dem globalen Manager und aktualisiert die Daten.
        
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        try:
            logger.info("🎯 ZENTRALE STICHTAG-ARCHITEKTUR - ViewManager Refresh")
            
            # ZENTRALE STICHTAG-ABFRAGE
            import sys
            import os
            
            try:
                # Import der globalen Instanz aus PDVM-Systemstart
                import importlib.util
                spec = importlib.util.spec_from_file_location("pdvm_systemstart", 
                    os.path.join(os.path.dirname(__file__), "PDVM-Systemstart.py"))
                if spec and spec.loader:
                    pdvm_systemstart = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(pdvm_systemstart)
                    central_manager = pdvm_systemstart.get_global_stichtag_manager()
                    new_stichtag = central_manager.get_stichtag_float()
                    logger.info(f"🎯 Zentraler Stichtag abgerufen: {new_stichtag}")
                else:
                    # Fallback: Aktuellen Stichtag verwenden
                    new_stichtag = self.stichtag
                    logger.warning(f"⚠️ Fallback: Verwende aktuellen Stichtag: {new_stichtag}")
            except Exception as import_error:
                logger.warning(f"⚠️ Globaler StichtagManager nicht verfügbar: {import_error}")
                new_stichtag = self.stichtag
                
            # SYNCHRONISATION
            old_stichtag = self.stichtag
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            logger.info(f"✅ Stichtag-Sync im ViewManager: {old_stichtag} → {new_stichtag}")
            
            # DATEN REFRESH (simuliert mit neuen Test-Daten)
            if new_stichtag != old_stichtag:
                logger.info(f"🔄 Stichtag geändert - lade neue Daten")
                self._load_test_data()
                
                # Simuliere stichtagsabhängige Daten
                for i, row in enumerate(self.data_cache):
                    if row[0] == "54073c2c":
                        # Familienname ändert sich je nach Stichtag
                        if new_stichtag >= 2025200.0:  # Nach Juli 2025
                            row[2] = "Mustermann-Updated"
                        else:
                            row[2] = "Mustermann"
                        self.data_cache[i] = row
            
            logger.info(f"✅ ZENTRALE ViewManager-Refresh erfolgreich: {len(self.data_cache)} Datensätze")
            return len(self.data_cache)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim zentralen ViewManager-Refresh: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return 0
    
    def get_column_names(self):
        """Gibt die Spaltennamen zurück"""
        return self.column_control.get_column_names()
        
    def get_metadata(self):
        """Gibt Metadaten zurück"""
        return {
            "view_guid": self.view_guid,
            "user_guid": self.user_guid, 
            "stichtag": self.stichtag,
            "columns": len(self.column_control.columns),
            "rows": len(self.data_cache)
        }
