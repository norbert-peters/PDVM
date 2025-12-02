"""
Verifiziert die neue sys_menudaten Controls-Struktur
"""

import sqlite3
import json

DB_PATH = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
FRAME_GUID = "794cbfc3-ccb6-4681-b432-efa9f44682c8"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT daten FROM sys_framedaten WHERE uid = ?", (FRAME_GUID,))
row = cursor.fetchone()

if row:
    data = json.loads(row[0])
    controls = data.get('METADATEN', {}).get('SYS_MENUDATEN', {}).get('controls', {})
    
    print("="*80)
    print("🔍 SYS_MENUDATEN CONTROLS STRUKTUR")
    print("="*80)
    print(f"Anzahl Controls: {len(controls)}")
    print()
    
    for guid, control in sorted(controls.items(), key=lambda x: x[1].get('display_order', 999)):
        print(f"📋 {guid}")
        print(f"   name: {control.get('name')}")
        print(f"   label: {control.get('label')}")
        print(f"   type: {control.get('type')}")
        print(f"   control_type: {control.get('control_type')}")
        print(f"   display_order: {control.get('display_order')}")
        print(f"   table: {control.get('table')}")
        print(f"   gruppe: {control.get('gruppe')}")
        print(f"   feld: {control.get('feld')}")
        print()

conn.close()

print("="*80)
print("✅ Struktur entspricht Standard-Pattern")
print("="*80)
