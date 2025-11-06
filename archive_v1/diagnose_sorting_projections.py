#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Direkter Test der Sortier-Projektions-Tabellen Problem-Diagnose
PDVM-System v0.9 - Warum sind keine Spalten verfügbar?

Testet:
1. GCS Verfügbarkeit  
2. view_guid Existenz
3. Projektions-Tabellen Inhalt
4. get_columns_for_view Verhalten
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

# Logging Setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockSortingManager:
    """Mock Sorting Manager"""
    def __init__(self):
        self.current_sort_column = None
        self.current_sort_direction = 'asc'
        self.view_dialog = MockViewDialog()

class MockViewDialog:
    """Mock View Dialog"""
    def __init__(self):
        self.view_guid = "test-view-guid-12345"
        self.controls_config = {
            'familienname': {'name': 'Familienname', 'original': 'Familienname'},
            'vorname': {'name': 'Vorname', 'original': 'Vorname'},
            'geburtsdatum': {'name': 'Geburtsdatum', 'original': 'Geburtsdatum'},
            'email': {'name': 'E-Mail', 'original': 'E-Mail'},
            'telefon': {'name': 'Telefon', 'original': 'Telefon'}
        }

class DiagnoseWindow(QMainWindow):
    """Diagnose-Fenster"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Sortier-Projektions-Diagnose")
        self.setGeometry(100, 100, 600, 400)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test-Button
        test_button = QPushButton("🔍 Diagnose Sortier-Projektions-Tabellen")
        test_button.clicked.connect(self.diagnose_sorting_projections)
        layout.addWidget(test_button)
        
        # Dialog-Test Button
        dialog_test_button = QPushButton("📊 Teste Sortier-Dialog direkt")
        dialog_test_button.clicked.connect(self.test_sorting_dialog)
        layout.addWidget(dialog_test_button)
    
    def diagnose_sorting_projections(self):
        """Diagnose der Sortier-Projektions-Tabellen"""
        print("\n🔍 === SORTIER-PROJEKTIONS-DIAGNOSE ===")
        
        try:
            # 1. GCS verfügbar?
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                print("❌ GCS nicht verfügbar!")
                return
            
            print(f"✅ GCS verfügbar: {type(gcs).__name__}")
            print(f"   Expert Mode: {gcs.expert_mode}")
            print(f"   User GUID: {gcs.user_guid}")
            
            # 2. Test view_guid
            test_view_guid = "test-view-guid-12345"
            print(f"\n📋 Teste view_guid: {test_view_guid}")
            
            # 3. Prüfe _projection_tables
            print(f"\n📊 _projection_tables verfügbar: {hasattr(gcs, '_projection_tables')}")
            if hasattr(gcs, '_projection_tables'):
                print(f"   Anzahl Views in _projection_tables: {len(gcs._projection_tables)}")
                print(f"   Keys: {list(gcs._projection_tables.keys())}")
                
                if test_view_guid in gcs._projection_tables:
                    projections = gcs._projection_tables[test_view_guid]
                    print(f"   Projektionen für {test_view_guid}: {list(projections.keys())}")
                    
                    for proj_name, proj_content in projections.items():
                        print(f"     {proj_name}: {len(proj_content)} Spalten - {proj_content[:3] if proj_content else 'LEER'}")
                else:
                    print(f"   ❌ {test_view_guid} nicht in _projection_tables gefunden")
            
            # 4. Teste get_columns_for_view direkt
            print(f"\n🧪 Teste get_columns_for_view direkt:")
            
            for projection_type in ['sort_standard', 'sort_expert', 'view_standard', 'view_expert']:
                try:
                    columns = gcs.get_columns_for_view(test_view_guid, projection_type)
                    print(f"   {projection_type}: {len(columns)} Spalten - {columns[:3] if columns else 'LEER'}")
                except Exception as e:
                    print(f"   {projection_type}: ❌ FEHLER - {e}")
            
            # 5. Baue Projektions-Tabellen neu auf
            print(f"\n🔧 Baue Projektions-Tabellen neu auf...")
            try:
                gcs._build_projection_tables(test_view_guid)
                print("✅ Projektions-Tabellen neu aufgebaut")
                
                # Teste erneut
                print("\n🔄 Teste nach Rebuild:")
                for projection_type in ['sort_standard', 'sort_expert']:
                    columns = gcs.get_columns_for_view(test_view_guid, projection_type)
                    print(f"   {projection_type}: {len(columns)} Spalten - {columns[:3] if columns else 'LEER'}")
                    
            except Exception as e:
                print(f"❌ Fehler beim Rebuild: {e}")
            
        except Exception as e:
            print(f"❌ Diagnose-Fehler: {e}")
            import traceback
            traceback.print_exc()
    
    def test_sorting_dialog(self):
        """Teste Sortier-Dialog direkt"""
        print("\n📊 === DIREKTER SORTIER-DIALOG TEST ===")
        
        try:
            # Mock Manager erstellen
            mock_manager = MockSortingManager()
            
            # Dialog importieren und öffnen
            from pdvm_sorting_dialog import PdvmSortingDialog
            dialog = PdvmSortingDialog(mock_manager, self)
            
            print("✅ Sortier-Dialog erstellt")
            print(f"   View GUID: {dialog.view_guid}")
            print(f"   Sort Levels: {len(dialog.sort_levels)}")
            
            # Teste _get_available_columns_for_sorting direkt
            available_columns = dialog._get_available_columns_for_sorting()
            print(f"   Verfügbare Spalten: {len(available_columns)}")
            
            if available_columns:
                print("   Erste 5 Spalten:")
                for i, (key, name) in enumerate(available_columns[:5]):
                    print(f"     {i+1}. {key} → {name}")
            else:
                print("   ❌ Keine Spalten verfügbar")
            
            # Zeige Dialog
            result = dialog.exec_()
            print(f"Dialog Ergebnis: {'OK' if result == dialog.Accepted else 'Abgebrochen'}")
            
        except Exception as e:
            print(f"❌ Dialog-Test-Fehler: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Hauptfunktion"""
    print("🔍 PDVM Sortier-Projektions-Diagnose")
    print("=" * 50)
    
    # Simple GCS initialisieren (falls nicht bereits passiert)
    try:
        from pdvm_central_systemsteuerung import get_gcs, initialize_gcs
        if not get_gcs():
            print("🔧 Initialisiere GCS für Test...")
            # Verwende Mock-Daten
            initialize_gcs("test-user-guid-12345", "{}")
    except Exception as e:
        print(f"⚠️ GCS-Initialisierung fehlgeschlagen: {e}")
    
    app = QApplication(sys.argv)
    
    window = DiagnoseWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()