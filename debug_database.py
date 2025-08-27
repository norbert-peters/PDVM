#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug der PdvmCentralDatenbank
=============================
"""

import sys
import os
from datetime import datetime

def debug_database_behavior():
    """Debuggt das Verhalten der PdvmCentralDatenbank"""
    print("DEBUG: PdvmCentralDatenbank Verhalten")
    print("=" * 50)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        test_view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        
        # Test 1: Normale Datenbank-Struktur verstehen
        print("Schritt 1: Verstehe normale DB-Struktur...")
        
        sys_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=test_view_guid
        )
        
        # Test-Daten
        test_data = {
            "test_field": "test_value",
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Speichere Test-Daten für GUID: {test_view_guid}")
        result = sys_db.speichern(test_view_guid, test_data)
        print(f"Speichern-Ergebnis: {result}")
        
        # Sofort wieder lesen
        print("Lade Daten wieder...")
        loaded = sys_db.lesen()
        print(f"Geladene Daten: {loaded}")
        print(f"Datentyp: {type(loaded)}")
        
        if loaded:
            print("SUCCESS: Grundlegende DB-Operationen funktionieren")
            
            # Test 2: Echte Control-Struktur
            print("\nSchritt 2: Teste echte Control-Struktur...")
            
            control_data = {
                'FAMILIENNAME': {
                    'display_show': True,
                    'display_order': 1
                },
                'VORNAME': {
                    'display_show': True,
                    'display_order': 2
                }
            }
            
            result2 = sys_db.speichern(test_view_guid, control_data)
            print(f"Control-Speicherung: {result2}")
            
            loaded2 = sys_db.lesen()
            print(f"Control-Daten geladen: {loaded2}")
            
            if loaded2:
                for key, value in loaded2.items():
                    print(f"  {key}: {value}")
                    
                return True
            else:
                print("❌ Control-Daten nicht geladen")
                return False
        else:
            print("❌ Grundlegende DB-Operationen funktionieren nicht")
            return False
            
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_database_behavior()
