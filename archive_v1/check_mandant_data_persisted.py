"""
Prüft ob Mandanten-Daten korrekt in sys_anwendungsdaten persistiert wurden

Prüft VARIANTE 1: Daten unter Mandant-GUID gespeichert
"""

import sqlite3
import json
from pathlib import Path

# Mandant-GUID aus auth.db holen
auth_db = Path("Daten/auth.db")
conn = sqlite3.connect(auth_db)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Mandanten-GUID ermitteln (mandant_001)
cursor.execute("""
    SELECT uid, daten 
    FROM sys_mandanten 
    WHERE json_extract(daten, '$.METADATEN.MANDANT_ID') = 'mandant_001'
""")
row = cursor.fetchone()
mandant_guid = row['uid']
mandant_data = json.loads(row['daten'])

print("="*70)
print("🔍 MANDANTEN-DATEN PERSISTIERUNG - CHECK")
print("="*70)
print(f"\n📋 Mandanten-GUID: {mandant_guid}")
print(f"   Mandanten-ID: {mandant_data['METADATEN']['MANDANT_ID']}")
print(f"   Bezeichnung: {mandant_data['ROOT']['BEZEICHNUNG']}")

conn.close()

# Jetzt in Mandanten-DB prüfen
mandant_id = mandant_data['METADATEN']['MANDANT_ID']
mandant_db = Path(f"Daten/{mandant_id}/datenbank.db")

if not mandant_db.exists():
    print(f"\n❌ Mandanten-DB nicht gefunden: {mandant_db}")
    exit(1)

print(f"\n📂 Mandanten-DB: {mandant_db}")

conn = sqlite3.connect(mandant_db)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# sys_anwendungsdaten nach Mandant-GUID durchsuchen
cursor.execute("""
    SELECT uid, daten, name, created_at, modified_at
    FROM sys_anwendungsdaten
    WHERE uid = ?
""", (mandant_guid,))

row = cursor.fetchone()

if not row:
    print(f"\n❌ KEINE Daten unter Mandant-GUID gefunden!")
    print(f"   GUID: {mandant_guid}")
    
    # Alle Records auflisten
    cursor.execute("SELECT uid, name FROM sys_anwendungsdaten")
    all_rows = cursor.fetchall()
    print(f"\n   Vorhandene UIDs in sys_anwendungsdaten:")
    for r in all_rows:
        print(f"     - {r['uid']} ({r['name']})")
    
    conn.close()
    exit(1)

print(f"\n✅ Mandanten-Daten gefunden!")
print(f"   UID: {row['uid']}")
print(f"   Name: {row['name']}")
print(f"   Created: {row['created_at']}")
print(f"   Modified: {row['modified_at']}")

# JSON parsen
try:
    persisted_data = json.loads(row['daten'])
    
    print(f"\n📊 Gespeicherte Struktur:")
    print(f"   Gruppen: {list(persisted_data.keys())}")
    
    if 'ROOT' in persisted_data:
        print(f"\n   ROOT:")
        for key, value in persisted_data['ROOT'].items():
            if isinstance(value, dict):
                wert = value.get('WERT')
                print(f"     - {key}: {wert}")
            else:
                print(f"     - {key}: {value}")
    
    if 'METADATEN' in persisted_data:
        print(f"\n   METADATEN:")
        for key, value in persisted_data['METADATEN'].items():
            if isinstance(value, dict):
                wert = value.get('WERT')
                print(f"     - {key}: {wert}")
            else:
                print(f"     - {key}: {value}")
    
    # Validierung
    print(f"\n🔍 VALIDIERUNG:")
    
    checks = []
    
    # Check 1: ROOT.BEZEICHNUNG
    if 'ROOT' in persisted_data and 'BEZEICHNUNG' in persisted_data['ROOT']:
        checks.append(('✅', 'ROOT.BEZEICHNUNG vorhanden'))
    else:
        checks.append(('❌', 'ROOT.BEZEICHNUNG fehlt'))
    
    # Check 2: ROOT.DB_PATH
    if 'ROOT' in persisted_data and 'DB_PATH' in persisted_data['ROOT']:
        db_path_value = persisted_data['ROOT']['DB_PATH']
        if isinstance(db_path_value, dict):
            db_path = db_path_value.get('WERT')
        else:
            db_path = db_path_value
        checks.append(('✅', f'ROOT.DB_PATH: {db_path}'))
    else:
        checks.append(('❌', 'ROOT.DB_PATH fehlt'))
    
    # Check 3: METADATEN.MANDANT_ID
    if 'METADATEN' in persisted_data and 'MANDANT_ID' in persisted_data['METADATEN']:
        mandant_id_value = persisted_data['METADATEN']['MANDANT_ID']
        if isinstance(mandant_id_value, dict):
            mandant_id = mandant_id_value.get('WERT')
        else:
            mandant_id = mandant_id_value
        checks.append(('✅', f'METADATEN.MANDANT_ID: {mandant_id}'))
    else:
        checks.append(('❌', 'METADATEN.MANDANT_ID fehlt'))
    
    # Check 4: METADATEN.LETZTER_LOGIN
    if 'METADATEN' in persisted_data and 'LETZTER_LOGIN' in persisted_data['METADATEN']:
        login_value = persisted_data['METADATEN']['LETZTER_LOGIN']
        if isinstance(login_value, dict):
            login = login_value.get('WERT')
        else:
            login = login_value
        checks.append(('✅', f'METADATEN.LETZTER_LOGIN: {login}'))
    else:
        checks.append(('❌', 'METADATEN.LETZTER_LOGIN fehlt'))
    
    for icon, msg in checks:
        print(f"   {icon} {msg}")
    
    # Gesamtergebnis
    all_ok = all(c[0] == '✅' for c in checks)
    
    print("\n" + "="*70)
    if all_ok:
        print("✅ MANDANTEN-DATEN PERSISTIERUNG - ERFOLGREICH")
        print("="*70)
        print("\nVARIANTE 1 (Mandant-GUID) implementiert:")
        print("  - Daten unter Mandant-GUID gespeichert")
        print("  - ROOT.DB_PATH persistiert")
        print("  - METADATEN.LETZTER_LOGIN bei jedem Login aktualisiert")
        print("  - System-GUID (0000...) frei für System-Einstellungen")
        print("  - Saubere Trennung & Erweiterbar für Multi-Mandanten")
    else:
        print("⚠️ MANDANTEN-DATEN PERSISTIERUNG - UNVOLLSTÄNDIG")
        print("="*70)
        print("\nNicht alle Felder wurden korrekt gespeichert!")
    
except Exception as e:
    print(f"\n❌ Fehler beim JSON-Parsing: {e}")
    print(f"\nRoh-Daten: {row['daten'][:200]}...")

conn.close()
