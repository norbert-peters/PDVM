#!/usr/bin/env python3
"""
🔍 DEBUG: Datenfluss zwischen ViewManager und Widget analysieren

Problembeschreibung:
- ViewManager zeigt: "✅ 24 Datensätze in Column Control geladen"
- get_filtered_data: "24 Zeilen mit 11 Spalten für ViewWidget bereit"
- Widget zeigt: Nur Header, keine Daten

Ziel: Den exakten Datenfluss debuggen und das Mapping-Problem finden.
"""

import sys
import os
import logging

# PDVM System Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdvm_view_daten_manager import PdvmViewDatenManager

# Mock StichtagManager für Debug
class MockStichtagManager:
    def get_stichtag_float(self):
        return 2025152.0

def get_global_stichtag_manager():
    return MockStichtagManager()

# Logging für Debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_data_flow():
    """🔍 Debug den kompletten Datenfluss"""
    
    try:
        # 1. ViewManager erstellen
        logger.info("🔧 Erstelle ViewManager für Debug")
        
        # call_daten wie im echten System
        call_daten = {
            "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
            "user_guid": "5f97b7da-42d4-4b03-815a-34775fbb6138",
            "stichtag": 2025152.0,
            "view_header": "Debug Test",
            "mode": "admin"
        }
        
        view_manager = PdvmViewDatenManager(call_daten)
        
        # 2. Zentrale Stichtag setzen
        stichtag_manager = get_global_stichtag_manager()
        if stichtag_manager:
            stichtag = stichtag_manager.get_stichtag_float()
            logger.info(f"🗓️ Zentraler Stichtag: {stichtag}")
        else:
            logger.warning("⚠️ Kein zentraler StichtagManager verfügbar")
            stichtag = 2025152.0
        
        # 3. Datensätze bereits automatisch geladen beim ViewManager init
        logger.info("📊 ViewManager hat Daten bereits automatisch geladen")
        
        # 4. get_filtered_data() aufrufen wie Widget es macht
        logger.info("🎯 Rufe get_filtered_data() auf (wie Widget)")
        data, headers = view_manager.get_filtered_data()
        
        # 5. Datenstruktur analysieren
        logger.info("=" * 60)
        logger.info("🔍 DATENSTRUKTUR ANALYSE")
        logger.info("=" * 60)
        
        print(f"📋 Headers: {len(headers) if headers else 0}")
        if headers:
            for i, header in enumerate(headers):
                print(f"   [{i}] {header}")
        
        print(f"\n📊 Data: {len(data) if data else 0} Zeilen")
        if data:
            print(f"📊 Erste Zeile: {len(data[0]) if data[0] else 0} Spalten")
            
            # Erste 3 Zeilen anzeigen
            for row_idx, row in enumerate(data[:3]):
                print(f"\n🔍 Zeile {row_idx}:")
                if isinstance(row, (list, tuple)):
                    for col_idx, cell in enumerate(row):
                        header_name = headers[col_idx] if headers and col_idx < len(headers) else f"Col{col_idx}"
                        print(f"   [{col_idx}] {header_name}: {repr(cell)} ({type(cell).__name__})")
                else:
                    print(f"   ❌ Unerwarteter Datentyp: {type(row).__name__} - {repr(row)}")
        
        # 6. Widget-ähnliche Verarbeitung simulieren
        logger.info("\n" + "=" * 60)
        logger.info("🎯 WIDGET-SIMULATION")
        logger.info("=" * 60)
        
        if data and len(data) > 0:
            row_count = len(data)
            col_count = len(data[0]) if data[0] else 0
            print(f"📊 Widget würde erstellen: {row_count} Zeilen × {col_count} Spalten")
            
            # Simuliere Tabellen-Aufbau
            for row_idx, row_data in enumerate(data[:2]):  # Nur erste 2 Zeilen
                print(f"\n🔍 Widget-Verarbeitung Zeile {row_idx}:")
                if isinstance(row_data, (list, tuple)):
                    for col_idx, cell_value in enumerate(row_data):
                        str_value = str(cell_value)
                        print(f"   setItem({row_idx}, {col_idx}, '{str_value}')")
                        if not str_value or str_value.strip() == "":
                            print(f"   ❌ LEERE ZELLE ERKANNT!")
                else:
                    print(f"   ❌ Row-Daten sind kein List/Tuple: {type(row_data)}")
        else:
            print("❌ Keine Daten für Widget-Simulation verfügbar")
            
        # 7. Column Control Status prüfen
        logger.info("\n" + "=" * 60)
        logger.info("🔧 COLUMN CONTROL STATUS")
        logger.info("=" * 60)
        
        if hasattr(view_manager, 'column_control') and view_manager.column_control:
            cc = view_manager.column_control
            print(f"📋 Column Control: {len(cc.columns)} Spalten")
            print(f"📊 Loaded Records: {len(cc.loaded_records)} Datensätze")
            
            # Show-Spalten finden
            show_columns = [col for col in cc.columns if col.get('show', False)]
            print(f"👁️ Sichtbare Spalten: {len(show_columns)}")
            for col in show_columns:
                print(f"   • {col.get('name', 'N/A')} - {col.get('anzeige', 'N/A')}")
        else:
            print("❌ Kein Column Control verfügbar")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ Debug-Fehler: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔍 DEBUG: ViewManager → Widget Datenfluss")
    print("=" * 60)
    
    success = debug_data_flow()
    
    if success:
        print("\n✅ Debug abgeschlossen")
    else:
        print("\n❌ Debug fehlgeschlagen")
