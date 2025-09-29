#!/usr/bin/env python3
"""
INTEGRATION BEISPIEL: Linear Filter Manager
==========================================

Zeigt wie der LinearFilterExecutionManager in bestehende Filter-Dialoge integriert wird
um das nicht-lineare Filter-Pipeline Problem zu lösen.

VERWENDUNG:
1. Statt direkte Filter-Anwendung -> LinearFilterExecutionManager verwenden
2. Automatischer kompletter Reset vor jeder Filterung
3. Einheitliche Pipeline für alle Filter-Types
"""

import logging
import sys
import os

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path setup für Imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from linear_filter_execution_manager import get_linear_filter_manager
except ImportError:
    logger.error("❌ linear_filter_execution_manager.py nicht gefunden!")
    sys.exit(1)


class SearchParameterDialogIntegration:
    """
    Beispiel: Integration des LinearFilterExecutionManager in Search Parameter Dialog
    
    VORHER: Direkte Filter-Anwendung mit inkonsistenten Ergebnissen
    NACHHER: Lineare Pipeline mit konsistenten Ergebnissen
    """
    
    def __init__(self, view_guid: str):
        self.view_guid = view_guid
        
        # KRITISCH: Verwende LinearFilterExecutionManager statt direkter Filter-Anwendung
        self.linear_filter_manager = get_linear_filter_manager(view_guid)
        
        logger.info(f"🎯 SearchParameterDialog Integration für View: {view_guid}")
    
    def apply_simple_search_LINEAR(self, field_name: str, search_value: str, operator: str = "enthält"):
        """
        NEUE METHODE: Einfache Suche über LinearFilterExecutionManager
        
        LÖST DAS PROBLEM:
        - Komplexer Filter -> 3 Ergebnisse
        - Einfacher Filter "Lau" -> wird auf bereits gefilterte Daten angewendet -> FALSCH: 2 Treffer
        
        MIT DIESER METHODE:  
        - Komplexer Filter -> 3 Ergebnisse
        - Einfacher Filter "Lau" -> KOMPLETTER RESET + Anwendung auf ALLE Daten -> KORREKT: 3 Treffer
        """
        logger.info("🎯 LINEARE EINFACHE SUCHE")
        logger.info(f"📂 View: {self.view_guid}")
        logger.info(f"🔍 Feld: {field_name}, Wert: '{search_value}', Operator: {operator}")
        
        # Konfiguration für parametrischen Filter
        filter_config = {
            'field_name': field_name,
            'search_value': search_value,
            'operator': operator
        }
        
        # KRITISCH: Verwende LinearFilterExecutionManager
        # Dies führt automatisch kompletten Reset durch und wendet Filter auf komplette Datenbasis an
        success = self.linear_filter_manager.execute_filter_linear('parametric', filter_config)
        
        if success:
            logger.info("✅ Lineare einfache Suche erfolgreich")
        else:
            logger.error("❌ Lineare einfache Suche fehlgeschlagen")
            
        return success
    
    def apply_gesamtfilter_LINEAR(self, filter_text: str):
        """
        NEUE METHODE: Gesamtfilter über LinearFilterExecutionManager
        """
        logger.info("🎯 LINEARER GESAMTFILTER")
        logger.info(f"📂 View: {self.view_guid}")  
        logger.info(f"🔍 Filter-Text: '{filter_text}'")
        
        # Konfiguration für Gesamtfilter
        filter_config = {
            'filter_text': filter_text
        }
        
        # KRITISCH: Verwende LinearFilterExecutionManager
        success = self.linear_filter_manager.execute_filter_linear('gesamtfilter', filter_config)
        
        if success:
            logger.info("✅ Linearer Gesamtfilter erfolgreich")
        else:
            logger.error("❌ Linearer Gesamtfilter fehlgeschlagen")
            
        return success
    
    def apply_extended_filter_LINEAR(self, field_name: str, conditions: list):
        """
        NEUE METHODE: Erweiterter Filter (4-Positionen) über LinearFilterExecutionManager
        """
        logger.info("🎯 LINEARER ERWEITERTER FILTER")
        logger.info(f"📂 View: {self.view_guid}")
        logger.info(f"🔧 Feld: {field_name}, Bedingungen: {len(conditions)}")
        
        # Konfiguration für erweiterten Filter
        filter_config = {
            'field_name': field_name,
            'conditions': conditions
        }
        
        # KRITISCH: Verwende LinearFilterExecutionManager
        success = self.linear_filter_manager.execute_filter_linear('extended', filter_config)
        
        if success:
            logger.info("✅ Linearer erweiterter Filter erfolgreich")
        else:
            logger.error("❌ Linearer erweiterter Filter fehlgeschlagen")
            
        return success
    
    def clear_all_filters_LINEAR(self):
        """
        NEUE METHODE: Alle Filter löschen über LinearFilterExecutionManager
        
        Stellt sicher, dass nach dem Löschen der ursprüngliche Zustand 
        (alle Daten sichtbar) wiederhergestellt wird.
        """
        logger.info("🧹 LÖSCHE ALLE FILTER LINEAR")
        logger.info(f"📂 View: {self.view_guid}")
        
        success = self.linear_filter_manager.clear_all_filters()
        
        if success:
            logger.info("✅ Alle Filter erfolgreich gelöscht - ursprünglicher Zustand wiederhergestellt")
        else:
            logger.error("❌ Fehler beim Löschen aller Filter")
            
        return success
    
    def get_current_filter_status_LINEAR(self):
        """
        NEUE METHODE: Status des aktuellen Filters abrufen
        """
        filter_info = self.linear_filter_manager.get_current_filter_info()
        
        logger.info(f"📋 Aktueller Filter Status:")
        logger.info(f"  Aktiv: {filter_info['active']}")
        if filter_info['active']:
            logger.info(f"  Type: {filter_info['type']}")
            logger.info(f"  Konfiguration: {filter_info['config']}")
        
        return filter_info


class MigrationHelper:
    """
    Hilfsklasse für Migration bestehender Filter-Aufrufe zum LinearFilterExecutionManager
    """
    
    @staticmethod
    def show_migration_examples():
        """Zeigt Migrationsbeispiele für bestehenden Code"""
        print("=" * 80)
        print("🔄 MIGRATION VON ALTEN FILTER-AUFRUFEN")
        print("=" * 80)
        print()
        print("VORHER (Problematisch):")
        print("----------------------")
        print("# Direkter Filter-Aufruf")
        print("self.apply_search_filter('familienname', 'Lau')")
        print("# Problem: Filter wird auf bereits gefilterte Daten angewendet!")
        print()
        print("NACHHER (Linear & Korrekt):")
        print("---------------------------")
        print("# Via LinearFilterExecutionManager")
        print("dialog = SearchParameterDialogIntegration(view_guid)")
        print("dialog.apply_simple_search_LINEAR('familienname', 'Lau', 'enthält')")
        print("# Lösung: Automatischer kompletter Reset + Anwendung auf alle Daten")
        print()
        print("=" * 80)
        print("WEITERE BEISPIELE:")
        print("=" * 80)
        print()
        print("1. GESAMTFILTER:")
        print("   dialog.apply_gesamtfilter_LINEAR('Suchtext hier')")
        print()
        print("2. ERWEITERTE FILTER:")
        print("   conditions = [...]  # 4-Positionen Struktur")
        print("   dialog.apply_extended_filter_LINEAR('feldname', conditions)")
        print()
        print("3. ALLE FILTER LÖSCHEN:")
        print("   dialog.clear_all_filters_LINEAR()")
        print()
        print("4. FILTER-STATUS PRÜFEN:")
        print("   status = dialog.get_current_filter_status_LINEAR()")
        print()
        print("=" * 80)


def test_linear_filter_integration():
    """Test der Integration"""
    logger.info("🧪 TESTE LINEAR FILTER INTEGRATION")
    
    test_view_guid = "integration-test-view"
    
    # Erstelle Integration-Instanz
    dialog = SearchParameterDialogIntegration(test_view_guid)
    
    # Test 1: Einfache Suche
    logger.info("\n📝 Test 1: Einfache Suche 'Lau'")
    success1 = dialog.apply_simple_search_LINEAR('familienname', 'Lau', 'enthält')
    
    # Test 2: Status prüfen
    logger.info("\n📋 Test 2: Filter-Status prüfen")
    status = dialog.get_current_filter_status_LINEAR()
    
    # Test 3: Alle Filter löschen
    logger.info("\n🧹 Test 3: Alle Filter löschen")
    success3 = dialog.clear_all_filters_LINEAR()
    
    # Zusammenfassung
    logger.info("\n📊 TEST ZUSAMMENFASSUNG:")
    logger.info(f"  Einfache Suche: {'✅' if success1 else '❌'}")
    logger.info(f"  Filter Status: {'✅' if status else '❌'}")
    logger.info(f"  Filter löschen: {'✅' if success3 else '❌'}")
    
    return all([success1, status, success3])


if __name__ == "__main__":
    # Zeige Migration-Beispiele
    MigrationHelper.show_migration_examples()
    
    # Teste Integration
    test_success = test_linear_filter_integration()
    
    print(f"\n🎯 INTEGRATION TEST: {'✅ ERFOLGREICH' if test_success else '❌ FEHLGESCHLAGEN'}")
    
    print("\n" + "=" * 80)
    print("✅ LINEARER FILTER-EXECUTION-MANAGER BEREIT FÜR INTEGRATION!")
    print("=" * 80)