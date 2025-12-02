"""
Analysiert alle Systemtabellen und deren 555... Templates
"""

import sqlite3
import json

DB_PATH = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
TEMPLATE_GUID = "55555555-5555-5555-5555-555555555555"

def analyze_table(cursor, table_name):
    """Analysiert Struktur einer Systemtabelle"""
    print("="*80)
    print(f"📋 {table_name}")
    print("="*80)
    
    # Template laden
    cursor.execute(f"SELECT daten FROM {table_name} WHERE uid = ?", (TEMPLATE_GUID,))
    row = cursor.fetchone()
    
    if row:
        data = json.loads(row[0])
        print("✅ Template (555...) gefunden")
        print(f"📂 Root-Keys: {list(data.keys())}")
        
        # Detaillierte Struktur
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"\n   {key}:")
                if key == 'ROOT':
                    for subkey, subval in value.items():
                        print(f"      {subkey}: {subval if not isinstance(subval, dict) else '{...}'}")
                else:
                    print(f"      → {len(value)} Einträge")
                    # Erste 3 Keys zeigen
                    for i, subkey in enumerate(list(value.keys())[:3]):
                        print(f"         - {subkey}")
                    if len(value) > 3:
                        print(f"         ... und {len(value)-3} weitere")
    else:
        print("❌ KEIN Template gefunden!")
    
    # Anzahl Datensätze
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n📊 Gesamt: {count} Datensätze")
    print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n")
print("🔧 ANALYSE ALLER SYSTEMTABELLEN")
print("="*80)
print()

# Alle Systemtabellen
tables = [
    'sys_viewdaten',
    'sys_framedaten',
    'sys_dialogdaten',
    'sys_menudaten',
    'sys_dropdowndaten',
    'sys_beschreibungen'
]

for table in tables:
    try:
        analyze_table(cursor, table)
    except sqlite3.OperationalError as e:
        print(f"❌ Fehler bei {table}: {e}")
        print()

conn.close()

print("="*80)
print("✅ Analyse abgeschlossen")
print("="*80)
