"""
Debug: PdvmCentralDatenbank für sys_menudaten
=============================================
Prüft ob PdvmCentralDatenbank sys_menudaten lesen kann
"""

import json
from pdvm_central_datenbank import PdvmCentralDatenbank

print("\n" + "="*80)
print("🔍 DEBUG: PdvmCentralDatenbank mit sys_menudaten")
print("="*80)

# Prüfe PdvmInit.json
print("\n📋 PdvmInit.json:")
with open('PdvmInit.json', 'r', encoding='utf-8') as f:
    init_data = json.load(f)
    print(f"   Datenbank: {init_data['ROOT']['datenbank']}")

# Test: Admin-Startmenü laden
menu_guid = "5ca6674e-b9ce-4581-9756-64e742883f80"

print(f"\n🔧 Erstelle PdvmCentralDatenbank für Menü:")
print(f"   Tabelle: sys_menudaten")
print(f"   GUID: {menu_guid}")

try:
    menu_db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
    
    print(f"\n✅ PdvmCentralDatenbank erstellt")
    print(f"   DB-Name: {menu_db.db_name}")
    print(f"   Historisch: {menu_db.historisch}")
    print(f"   Daten geladen: {menu_db._data_loaded}")
    
    if menu_db.data:
        print(f"\n📦 Daten vorhanden:")
        print(f"   Gruppen: {list(menu_db.data.keys())}")
        
        if 'META' in menu_db.data:
            meta = menu_db.data['META']
            print(f"\n   META:")
            for key, value in meta.items():
                print(f"      {key}: {value}")
        
        if 'VERTIKAL' in menu_db.data:
            vertikal_items = menu_db.data['VERTIKAL']
            print(f"\n   VERTIKAL: {len(vertikal_items)} Items")
            if vertikal_items:
                print(f"      Beispiel: {vertikal_items[0].get('label', 'N/A')}")
        
        if 'GRUND' in menu_db.data:
            grund_items = menu_db.data['GRUND']
            print(f"\n   GRUND: {len(grund_items)} Items")
            if grund_items:
                print(f"      Beispiel: {grund_items[0].get('label', 'N/A')}")
    else:
        print(f"\n❌ Keine Daten geladen!")
        print(f"   menu_db.data = {menu_db.data}")
    
except Exception as e:
    print(f"\n❌ FEHLER: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("✅ DEBUG ABGESCHLOSSEN")
print("="*80)
