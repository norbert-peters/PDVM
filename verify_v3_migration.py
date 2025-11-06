"""
Verify V3 Migration in sys_menudaten
=====================================
Prüft ob die V3-Migration korrekt in sys_menudaten durchgeführt wurde
"""
import sqlite3
import json

def verify_migration(db_path: str, mandant_name: str):
    """Prüft V3-Daten in sys_menudaten"""
    print(f"\n{'='*80}")
    print(f"🔍 {mandant_name}: {db_path}")
    print('='*80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Erstes Menü holen als Beispiel
    cursor.execute("""
        SELECT uid, name, daten
        FROM sys_menudaten
        WHERE historisch = 0
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    if not result:
        print("❌ Keine Menüs gefunden!")
        return
    
    uid, name, daten_json = result
    
    print(f"\n📋 Beispiel-Menü: {name}")
    print(f"   GUID: {uid}\n")
    
    # JSON parsen
    try:
        data = json.loads(daten_json)
        
        # V3-Struktur prüfen
        if 'META' in data:
            print("✅ META-Gruppe vorhanden:")
            print(f"   Version: {data['META'].get('version')}")
            print(f"   Migriert von: {data['META'].get('migrated_from')}")
        else:
            print("❌ Keine META-Gruppe gefunden (noch V2?)")
            return
        
        # Items mit Commands prüfen
        print("\n📂 GRUND-Items (erste 3):")
        grund_items = data.get('GRUND', [])
        for idx, item in enumerate(grund_items[:3]):
            print(f"\n   {idx+1}. {item.get('label')}")
            print(f"      Type: {item.get('type')}")
            
            if 'command' in item and item['command']:
                cmd = item['command']
                print(f"      ✅ Command: {cmd.get('handler')}")
                if cmd.get('params'):
                    print(f"         Params: {cmd.get('params')}")
            else:
                print(f"      ℹ️  Kein Command (normal für SUBMENU/SEPARATOR)")
        
        print(f"\n📊 Statistik:")
        print(f"   VERTIKAL: {len(data.get('VERTIKAL', []))} Items")
        print(f"   GRUND: {len(data.get('GRUND', []))} Items")
        print(f"   ZUSATZ: {len(data.get('ZUSATZ', []))} Items")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON-Parse-Fehler: {e}")
    
    conn.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔄 V3 MIGRATION VERIFICATION")
    print("="*80)
    
    verify_migration(
        "Daten/mandant_001/datenbank.db",
        "MANDANT 1"
    )
    
    verify_migration(
        "Daten/mandant_002/datenbank.db",
        "MANDANT 2"
    )
    
    print("\n" + "="*80)
    print("✅ VERIFICATION ABGESCHLOSSEN")
    print("="*80)
