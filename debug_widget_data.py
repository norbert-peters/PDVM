#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG: Widget-Daten Analyse
============================

Zeigt genau, welche Daten ans Widget gesendet werden
"""

import sys
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

import importlib.util
spec = importlib.util.spec_from_file_location('pdvm_systemstart', 'pdvm_systemstart.py')
pdvm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdvm_module)

def debug_widget_data():
    print("🔍 DEBUG: Widget-Daten Analyse")
    print("=" * 50)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        from pdvm_view_daten_manager import PdvmViewDatenManager
        
        # ViewDaten finden
        view_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="viewdaten", guid=None)
        view_records = view_db.lesen_alle_ohne_system(limit=1)
        
        if not view_records:
            print("❌ Keine ViewDaten gefunden")
            return False
        
        view_guid = view_records[0]["uid"]
        print(f"✅ View: {view_guid[:12]}...")
        
        # Manager erstellen
        call_daten = {
            "view_guid": view_guid,
            "user_guid": "test-user-guid",
            "stichtag": 1001.0,
            "mode": "normal"
        }
        
        manager = PdvmViewDatenManager(call_daten)
        loaded_count = manager.load_records_data(limit=5)
        print(f"✅ {loaded_count} Datensätze geladen")
        
        if loaded_count == 0:
            print("⚠️ Keine Daten zum Anzeigen")
            return False
        
        print(f"\n1️⃣ SHOW_ONLY=TRUE (wie für Widget):")
        display_data_show, display_columns_show = manager.get_table_data_for_display(show_only=True)
        
        print(f"   📊 Spalten ({len(display_columns_show)}):")
        for i, col in enumerate(display_columns_show):
            print(f"      {i+1:2d}. {col}")
        
        print(f"   📋 Daten ({len(display_data_show)} Zeilen):")
        for i, row in enumerate(display_data_show):
            print(f"      Zeile {i+1}:")
            for col in display_columns_show[:5]:  # Erste 5 Spalten
                value = row.get(col, "?")
                print(f"         {col:<20} = '{value}'")
            if len(display_columns_show) > 5:
                print(f"         ... und {len(display_columns_show)-5} weitere")
            print()
        
        print(f"\n2️⃣ SHOW_ONLY=FALSE (alle Spalten):")
        display_data_all, display_columns_all = manager.get_table_data_for_display(show_only=False)
        
        print(f"   📊 Spalten ({len(display_columns_all)}):")
        for i, col in enumerate(display_columns_all):
            col_type = "show" if col.endswith("_show") else ("original" if col.endswith("_original") else "system")
            print(f"      {i+1:2d}. {col:<30} ({col_type})")
        
        print(f"   📋 Erste Zeile (alle Spalten):")
        if display_data_all:
            first_row = display_data_all[0]
            for col in display_columns_all:
                value = first_row.get(col, "?")
                if value and str(value).strip():  # Nur non-empty Werte zeigen
                    print(f"      {col:<30} = '{value}'")
        
        print(f"\n3️⃣ COLUMN CONTROL DIREKT:")
        if manager.column_control.row_guids:
            first_guid = manager.column_control.row_guids[0]
            raw_data = manager.column_control.get_row_data(first_guid)
            
            print(f"   📋 Raw-Daten (GUID: {first_guid[:8]}...):")
            for key, value in raw_data.items():
                if value and str(value).strip():  # Nur non-empty Werte zeigen
                    print(f"      {key:<30} = '{value}'")
        
        # 4. Widget-Format simulieren
        print(f"\n4️⃣ WIDGET-FORMAT SIMULATION:")
        print(f"   🎯 Das Widget würde folgende Daten empfangen:")
        
        if display_data_show and display_columns_show:
            print(f"      Spalten-Header: {display_columns_show}")
            print(f"      Zeilen-Daten:")
            for i, row in enumerate(display_data_show[:3]):  # Erste 3 Zeilen
                row_values = [str(row.get(col, "")) for col in display_columns_show]
                print(f"         Zeile {i+1}: {row_values}")
        
        return True
        
    except Exception as e:
        print(f"❌ DEBUG FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_widget_data()
