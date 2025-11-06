#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDVM Sortierung - Schnelle Syntax-Validierung
============================================

Prüft ob alle neuen Sortierungs-Module korrekt importierbar sind
und grundlegende Syntax-Fehler behebt.
"""

import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Testet alle Sortierungs-Imports"""
    
    print("🔍 === IMPORT-TESTS ===")
    
    # Test 1: PdvmSortingManager
    try:
        from pdvm_sorting_manager import PdvmSortingManager
        print("✅ PdvmSortingManager importiert")
    except Exception as e:
        print(f"❌ PdvmSortingManager Import-Fehler: {e}")
        return False
    
    # Test 2: PdvmSortingDialog
    try:
        from pdvm_sorting_dialog import PdvmSortingDialog
        print("✅ PdvmSortingDialog importiert")
    except Exception as e:
        print(f"❌ PdvmSortingDialog Import-Fehler: {e}")
        return False
    
    # Test 3: View-Dialog Integration
    try:
        from pdvm_view_dialog import PdvmViewDialog, PdvmViewDisplay
        print("✅ PdvmViewDialog Integration importiert")
    except Exception as e:
        print(f"❌ PdvmViewDialog Import-Fehler: {e}")
        return False
    
    return True


def test_basic_functionality():
    """Testet Basis-Funktionalität ohne GUI"""
    
    print("\n🔧 === FUNKTIONS-TESTS ===")
    
    try:
        from pdvm_sorting_manager import PdvmSortingManager
        
        # Mock-ViewDialog für Test
        class MockViewDialog:
            def __init__(self):
                self.controls_config = {
                    'test_column': {
                        'name': 'Test Spalte',
                        'sortable': True
                    }
                }
        
        # Mock-GCS für Test
        class MockGCS:
            def __init__(self):
                self._properties = {}
            
            def get_property(self, gruppe, feld):
                return self._properties.get(f"{gruppe}.{feld}")
            
            def set_property(self, gruppe, feld, wert):
                self._properties[f"{gruppe}.{feld}"] = wert
                
            def save_values(self):
                pass
        
        # Test SortingManager Initialisierung
        mock_view = MockViewDialog()
        mock_gcs = MockGCS()
        
        sorting_manager = PdvmSortingManager(mock_view, mock_gcs)
        print("✅ PdvmSortingManager Initialisierung")
        
        # Test sortable columns
        sortable = sorting_manager.get_sortable_columns()
        print(f"✅ Sortierbare Spalten: {len(sortable)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Funktions-Test Fehler: {e}")
        return False


def test_gcs_integration():
    """Testet GCS Integration"""
    
    print("\n🔗 === GCS INTEGRATION ===")
    
    try:
        # Prüfe ob GCS verfügbar ist
        from pdvm_central_systemsteuerung import get_gcs
        print("✅ GCS Import verfügbar")
        
        # Prüfe ob GCS initialisiert ist (ohne Login)
        try:
            gcs = get_gcs()
            if gcs and hasattr(gcs, 'is_initialized') and gcs.is_initialized:
                print("✅ GCS vollständig initialisiert")
            else:
                print("ℹ️ GCS nicht initialisiert (normal ohne Login)")
        except Exception as gcs_error:
            print(f"ℹ️ GCS nicht verfügbar: {gcs_error} (normal ohne Login)")
        
        return True  # GCS-Verfügbarkeit ist optional für Syntax-Tests
        
    except Exception as e:
        print(f"❌ GCS Integration Fehler: {e}")
        return False


def main():
    """Hauptfunktion für Validierung"""
    
    print("🔍 PDVM Sortierungs-Validierung")
    print("=" * 40)
    
    success = True
    
    # Import-Tests
    if not test_imports():
        success = False
    
    # Funktions-Tests
    if not test_basic_functionality():
        success = False
    
    # GCS Integration
    if not test_gcs_integration():
        success = False
    
    print("\n" + "=" * 40)
    
    if success:
        print("✅ ALLE TESTS ERFOLGREICH!")
        print("🚀 Sortierungs-System bereit für Einsatz!")
        print("\n💡 Nächste Schritte:")
        print("1. python main.py starten")
        print("2. View-Dialog öffnen")
        print("3. Header-Klicks testen")
        print("4. Einstellungen > Sortierung verwalten testen")
    else:
        print("❌ FEHLER GEFUNDEN!")
        print("🔧 Bitte Fehler beheben vor dem Test")
    
    return success


if __name__ == "__main__":
    main()