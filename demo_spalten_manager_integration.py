#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMO: PdvmSpaltenManager Integration - Einfach und Linear
========================================================

Zeigt die vereinfachte Integration:
1. ColumnControl → SpaltenManager → Fertige Tabelle
2. Mode spielt keine Rolle mehr
3. Widget bekommt saubere Daten
"""

import sys
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# pdvm_systemstart importieren
import importlib.util
spec = importlib.util.spec_from_file_location('pdvm_systemstart', 'pdvm_systemstart.py')
pdvm_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdvm_module)

def demo_spalten_manager_integration():
    """Demonstriert die einfache SpaltenManager Integration"""
    print("🚀 DEMO: PdvmSpaltenManager Integration - Einfach und Linear")
    print("=" * 65)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        from pdvm_view_daten_manager import PdvmViewDatenManager
        from pdvm_spalten_manager import PdvmSpaltenManager
        
        # SCHRITT 1: ViewDaten setup (wie bisher)
        print("\n🔧 SCHRITT 1: ViewDaten Setup")
        
        view_db = PdvmCentralDatenbank(db_name="PdvmManager.db", table_name="viewdaten", guid=None)
        view_records = view_db.lesen_alle_ohne_system(limit=1)
        
        view_guid = view_records[0]["uid"]
        call_daten = {
            "view_guid": view_guid,
            "user_guid": "demo-user",
            "stichtag": 1001.0,
            "mode": "normal"  # WIRD IGNORIERT!
        }
        
        manager = PdvmViewDatenManager(call_daten)
        manager.load_records_data(limit=10)
        
        print(f"   ✅ ViewDaten geladen: {len(manager.column_control.row_guids)} Datensätze")
        
        # SCHRITT 2: SpaltenManager - EINFACH!
        print(f"\n🎯 SCHRITT 2: SpaltenManager Integration")
        
        # Ein-Zeiler: ColumnControl → SpaltenManager
        spalten_manager = PdvmSpaltenManager(manager.column_control)
        
        print(f"   ✅ SpaltenManager erstellt")
        
        # SCHRITT 3: Widget-fertige Tabelle - EINFACH!
        print(f"\n📊 SCHRITT 3: Widget-fertige Tabelle generieren")
        
        # Ein-Zeiler: SpaltenManager → Fertige Tabelle
        widget_data, widget_headers = spalten_manager.get_simple_table_data()
        
        print(f"   ✅ Widget-Tabelle: {len(widget_headers)} Spalten, {len(widget_data)} Zeilen")
        print(f"   📋 Headers: {widget_headers}")
        
        # SCHRITT 4: Daten-Vorschau
        print(f"\n🔍 SCHRITT 4: Daten-Vorschau (erste 3 Zeilen)")
        
        for i, row in enumerate(widget_data[:3]):
            print(f"   📋 Zeile {i+1}:")
            for header in widget_headers[:5]:  # Nur erste 5 Spalten
                value = row.get(header, '')
                value_display = str(value)[:20] if value else '(leer)'
                print(f"      {header:<20}: {value_display}")
            print()
        
        # SCHRITT 5: Vergleich Alt vs. Neu
        print(f"\n⚖️ SCHRITT 5: Vergleich Alt vs. Neu")
        
        # Alte Methode
        old_data, old_headers = manager.get_table_data_for_display(show_only=True)
        
        print(f"   🔄 Alte Integration:")
        print(f"      - Methode: manager.get_table_data_for_display()")
        print(f"      - Ergebnis: {len(old_headers)} Spalten, {len(old_data)} Zeilen")
        print(f"      - Mode-abhängig: Ja")
        print(f"      - Komplexität: Hoch")
        
        print(f"   🆕 Neue Integration:")
        print(f"      - Methode: spalten_manager.get_simple_table_data()")
        print(f"      - Ergebnis: {len(widget_headers)} Spalten, {len(widget_data)} Zeilen")
        print(f"      - Mode-abhängig: NEIN!")
        print(f"      - Komplexität: Niedrig")
        
        # SCHRITT 6: Integration-Code Beispiel
        print(f"\n💻 SCHRITT 6: Integration-Code (nur 3 Zeilen!)")
        print(f"""
   # Alte Integration (komplex):
   manager = PdvmViewDatenManager(call_daten)
   manager.load_records_data()
   data, headers = manager.get_table_data_for_display(show_only=True)
   # + Mode-Handling, Filter-Logik, etc.
   
   # NEUE Integration (einfach):
   manager = PdvmViewDatenManager(call_daten)  
   manager.load_records_data()
   spalten_manager = PdvmSpaltenManager(manager.column_control)
   data, headers = spalten_manager.get_simple_table_data()  # FERTIG!
        """)
        
        # SCHRITT 7: Widget-Simulation
        print(f"\n🖥️ SCHRITT 7: Widget-Simulation")
        
        print(f"   📋 TABELLE für Widget:")
        
        # Header-Zeile
        header_line = " | ".join(f"{h[:12]:<12}" for h in widget_headers[:6])  # Erste 6
        print(f"   {header_line}")
        print(f"   {'-' * len(header_line)}")
        
        # Daten-Zeilen  
        for i, row in enumerate(widget_data[:4]):  # Erste 4 Zeilen
            cells = []
            for header in widget_headers[:6]:  # Erste 6 Spalten
                value = row.get(header, '')
                cell = str(value)[:12] if value else ''
                cells.append(f"{cell:<12}")
            
            row_line = " | ".join(cells)
            print(f"   {row_line}")
        
        if len(widget_data) > 4:
            print(f"   ... und {len(widget_data) - 4} weitere Zeilen")
        
        print(f"\n🎉 SPALTENMANAGER INTEGRATION ERFOLGREICH!")
        print(f"✅ Linear: Control → Manager → Widget")
        print(f"✅ Einfach: 1 Klasse, klare Methoden")
        print(f"✅ Mode-unabhängig: Funktioniert immer gleich") 
        print(f"✅ Widget-Ready: Direkt verwendbar")
        
        return True
        
    except Exception as e:
        print(f"❌ DEMO FEHLGESCHLAGEN: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_spalten_manager_integration()
    print(f"\n{'🚀 INTEGRATION BEREIT' if success else '🔧 WEITERE ENTWICKLUNG'}")
    sys.exit(0 if success else 1)
