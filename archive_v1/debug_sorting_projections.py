#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug: Sortier-Projektions-Tabellen Problem
==========================================

Analysiert warum die Sortier-Projektions-Tabellen leer sind:
1. Prüft ob Controls geladen werden
2. Zeigt Struktur der Projektions-Tabellen
3. Debuggt Dictionary vs List Problem
"""

import logging
import sys
from pprint import pprint

try:
    from pdvm_central_systemsteuerung import get_gcs
    from simple_projection_manager import SimpleProjectionManager
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)

def debug_projection_manager():
    """Debug: SimpleProjectionManager im Detail"""
    print("🔍 Debugging SimpleProjectionManager")
    
    view_guid = "debug_test_view"
    
    try:
        # Mock-Controls für Test
        mock_controls = {
            'familienname_show': {
                'name': 'Familienname',
                'show': True,
                'sortable': True,
                'expert_mode': False
            },
            'vorname_show': {
                'name': 'Vorname', 
                'show': True,
                'sortable': True,
                'expert_mode': False
            },
            'email_show': {
                'name': 'E-Mail',
                'show': False,
                'sortable': True,
                'expert_mode': True
            },
            'dummy_show': {
                'name': 'Dummy',
                'show': False,
                'sortable': False,
                'expert_mode': False
            }
        }
        
        # Manager erstellen
        manager = SimpleProjectionManager(view_guid)
        
        # Mock-Controls injizieren für Test
        print(f"📋 Ursprüngliche Controls: {len(manager.controls)}")
        manager.controls = mock_controls
        print(f"📋 Mock Controls injiziert: {len(manager.controls)}")
        
        # Projektionen neu erstellen
        manager._create_default_projections()
        
        # Sortier-Projektions-Tabellen prüfen
        sort_standard = manager.get_sort_projection_standard()
        sort_expert = manager.get_sort_projection_expert()
        
        print(f"\n📊 Sortier-Projektions-Analyse:")
        print(f"   👤 Standard: {type(sort_standard)} mit {len(sort_standard)} Einträgen")
        print(f"   🔧 Expert: {type(sort_expert)} mit {len(sort_expert)} Einträgen")
        
        if isinstance(sort_standard, dict):
            print(f"\n🔍 Standard Sortier-Projektion Details:")
            for key, value in sort_standard.items():
                print(f"      {key}: {value}")
        
        if isinstance(sort_expert, dict):
            print(f"\n🔍 Expert Sortier-Projektion Details:")
            for key, value in sort_expert.items():
                print(f"      {key}: {value}")
        
        # Test Dialog-Logik Simulation
        print(f"\n🧪 Simuliere Dialog-Logik:")
        
        # Mock Dialog-Test
        class MockDialog:
            def __init__(self):
                self.sorting_manager = type('obj', (object,), {})()
                self.sorting_manager.view_dialog = type('obj', (object,), {})()
                self.sorting_manager.view_dialog.simple_projection_manager = manager
                self.sorting_manager.view_dialog.current_user_mode = 'standard'
                self.sort_levels = []
        
        mock_dialog = MockDialog()
        
        # Simuliere _get_available_columns_for_sorting
        try:
            projection_manager = mock_dialog.sorting_manager.view_dialog.simple_projection_manager
            sort_projection = projection_manager.get_sort_projection_standard()
            
            result = []
            for column_key, column_data in sort_projection.items():
                if isinstance(column_data, dict):
                    display_name = column_data.get('_original', column_key)
                    if column_data.get('_show', False):
                        result.append((column_key, str(display_name)))
            
            print(f"✅ Dialog-Simulation erfolgreich: {len(result)} verfügbare Spalten")
            for col_key, display_name in result:
                print(f"      • {display_name} ({col_key})")
        
        except Exception as e:
            print(f"❌ Dialog-Simulation Fehler: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Haupttest-Funktion"""
    print("🔍 Debug: Sortier-Projektions-Tabellen Problem")
    print("=" * 50)
    
    # Logging setup
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    success = debug_projection_manager()
    
    print(f"\n{'='*50}")
    if success:
        print("✅ Debug erfolgreich - Problem identifiziert!")
    else:
        print("❌ Debug fehlgeschlagen - Weitere Analyse notwendig")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)