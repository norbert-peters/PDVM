"""
Debug: Zeigt Menüdaten aus sys_menudaten
"""

import json
import sys
import os

# Python-Pfad anpassen
sys.path.insert(0, os.path.dirname(__file__))

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_central_systemsteuerung import get_gcs, initialize_gcs

def debug_menu_data(menu_guid: str):
    """Zeigt Menüdaten für GUID"""
    print(f"\n{'='*80}")
    print(f"🔍 DEBUG: Menüdaten für GUID: {menu_guid}")
    print(f"{'='*80}\n")
    
    try:
        # Datenbank-Instanz erstellen
        db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        db._load_data()
        
        print(f"✅ Datenbank-Instanz erstellt für sys_menudaten")
        print(f"   GUID: {menu_guid}")
        
        # Alle Gruppen auflisten
        print(f"\n📂 Verfügbare Gruppen:")
        if hasattr(db, 'value_cache') and db.value_cache:
            for gruppe in db.value_cache.keys():
                print(f"   - {gruppe}")
        
        # 'system' Gruppe prüfen
        print(f"\n📋 Gruppe 'system':")
        try:
            # Versuche 'daten' Feld zu laden
            daten_value, daten_abdatum = db.get_value('system', 'daten')
            
            if daten_value:
                print(f"✅ 'daten' Feld gefunden")
                print(f"   Typ: {type(daten_value)}")
                print(f"   Länge: {len(str(daten_value))} Zeichen")
                print(f"   AB-Datum: {daten_abdatum}")
                
                # Versuche JSON zu parsen
                try:
                    menu_data = json.loads(daten_value)
                    print(f"\n✅ JSON erfolgreich geparst:")
                    print(f"   VERTIKAL: {len(menu_data.get('VERTIKAL', []))} Items")
                    print(f"   GRUND: {len(menu_data.get('GRUND', []))} Items")
                    print(f"   ZUSATZ: {len(menu_data.get('ZUSATZ', []))} Items")
                    
                    # Erste 3 Items von VERTIKAL zeigen
                    if 'VERTIKAL' in menu_data and menu_data['VERTIKAL']:
                        print(f"\n📌 VERTIKAL Items (erste 3):")
                        for i, item in enumerate(menu_data['VERTIKAL'][:3]):
                            print(f"   [{i}] {item.get('label', 'N/A')} ({item.get('type', 'N/A')})")
                    
                    # Erste 3 Items von GRUND zeigen
                    if 'GRUND' in menu_data and menu_data['GRUND']:
                        print(f"\n🏠 GRUND Items (erste 3):")
                        for i, item in enumerate(menu_data['GRUND'][:3]):
                            print(f"   [{i}] {item.get('label', 'N/A')} ({item.get('type', 'N/A')})")
                    
                    # Komplett-JSON ausgeben
                    print(f"\n📄 Komplettes JSON:")
                    print("-" * 80)
                    print(json.dumps(menu_data, indent=2, ensure_ascii=False))
                    print("-" * 80)
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON-Parse-Fehler: {e}")
                    print(f"\n📄 Raw-Daten:")
                    print("-" * 80)
                    print(daten_value[:500])  # Erste 500 Zeichen
                    print("-" * 80)
            else:
                print(f"⚠️ 'daten' Feld ist leer oder None")
                
        except Exception as e:
            print(f"❌ Fehler beim Laden von 'system.daten': {e}")
            import traceback
            traceback.print_exc()
        
        # Alle Felder in 'system' Gruppe auflisten
        print(f"\n📋 Alle Felder in Gruppe 'system':")
        if hasattr(db, 'value_cache') and 'system' in db.value_cache:
            for feld, wert in db.value_cache['system'].items():
                print(f"   - {feld}: {type(wert)} = {str(wert)[:50]}...")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Test mit einer Menü-GUID (anpassen!)
    test_guid = "113c6a2c-af9a-4022-929b-6544799e8954"  # Beispiel
    
    if len(sys.argv) > 1:
        test_guid = sys.argv[1]
    
    debug_menu_data(test_guid)
