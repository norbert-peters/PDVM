"""Prüfe Admin-Testmenü in System-DB"""
import sqlite3
import json

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

menu_guid = '113c6a2c-af9a-4022-929b-6544799e8954'

result = cursor.execute('SELECT daten FROM sys_menudaten WHERE uid=?', (menu_guid,)).fetchone()

if result:
    print(f"✅ Admin-Testmenü gefunden!")
    data = json.loads(result[0])
    
    print(f"\n📋 META:")
    print(f"  Version: {data.get('META', {}).get('VERSION')}")
    print(f"  VERTIKAL: {data.get('META', {}).get('VERTIKAL')}")
    print(f"  GRUND: {data.get('META', {}).get('GRUND')}")
    print(f"  ZUSATZ: {data.get('META', {}).get('ZUSATZ')}")
    
    print(f"\n📋 VERTIKAL ({len(data.get('VERTIKAL', {}))} Items):")
    vertikal = data.get('VERTIKAL', {})
    for guid, item in list(vertikal.items())[:5]:  # Erste 5
        print(f"  - {item.get('label')} (Type={item.get('type')}, Parent={item.get('parent_guid', 'None')[:8] if item.get('parent_guid') else 'None'})")
    
    print(f"\n📋 GRUND ({len(data.get('GRUND', {}))} Items):")
    grund = data.get('GRUND', {})
    for guid, item in list(grund.items())[:5]:  # Erste 5
        print(f"  - {item.get('label')} (Type={item.get('type')}, Parent={item.get('parent_guid', 'None')[:8] if item.get('parent_guid') else 'None'})")
    
    print(f"\n📋 ZUSATZ ({len(data.get('ZUSATZ', {}))} Items):")
    zusatz = data.get('ZUSATZ', {})
    for guid, item in list(zusatz.items())[:5]:  # Erste 5
        print(f"  - {item.get('label')} (Type={item.get('type')}, Parent={item.get('parent_guid', 'None')[:8] if item.get('parent_guid') else 'None'})")
else:
    print(f"❌ Admin-Testmenü NICHT gefunden in sys_menudaten!")

conn.close()
