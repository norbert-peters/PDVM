"""
VERIFIKATION: Sorgloser Zugriff auf Dictionaries mit einheitlicher GUID

Prüft ob ALLE Dictionaries mit 66666... erreichbar sind:
- persondaten (Daten/mandant_001/datenbank.db)
- sys_mandanten (Daten/auth.db)
- sys_framedaten (Daten/pdvm_system.db)
- sys_viewdaten (Daten/pdvm_system.db)
"""

import sqlite3
import json

DICT_GUID = "66666666-6666-6666-6666-666666666666"

def verify_dictionary_access(table_name, db_path):
    """Prüft Dictionary-Zugriff mit 66666..."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT uid, name, daten FROM {table_name} WHERE uid = ?", (DICT_GUID,))
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            print(f"❌ {table_name}: Dictionary NICHT gefunden unter {DICT_GUID}")
            return False
        
        uid, name, daten_json = result
        daten = json.loads(daten_json)
        
        # Struktur prüfen
        if "ROOT" not in daten:
            print(f"⚠️  {table_name}: ROOT fehlt!")
            return False
        
        gruppen = [k for k in daten.keys() if k != "ROOT"]
        felder_total = sum(len(daten[g]) for g in gruppen)
        
        print(f"✅ {table_name}: {len(gruppen)} Gruppen, {felder_total} Felder")
        print(f"   ROOT.TABLE: {daten['ROOT'].get('TABLE')}")
        print(f"   Gruppen: {', '.join(gruppen)}")
        
        return True
        
    except Exception as e:
        print(f"❌ {table_name}: FEHLER - {e}")
        return False

# ========================================
# SORGLOSER ZUGRIFF TESTEN!
# ========================================
print(f"🔍 Teste sorglosen Zugriff mit {DICT_GUID}\n")

results = []

print("📁 persondaten (Mandanten-DB)")
results.append(verify_dictionary_access("persondaten", "Daten/mandant_001/datenbank.db"))

print("\n📁 sys_mandanten (auth.db)")
results.append(verify_dictionary_access("sys_mandanten", "Daten/auth.db"))

print("\n📁 sys_framedaten (pdvm_system.db)")
results.append(verify_dictionary_access("sys_framedaten", "Daten/pdvm_system.db"))

print("\n📁 sys_viewdaten (pdvm_system.db)")
results.append(verify_dictionary_access("sys_viewdaten", "Daten/pdvm_system.db"))

# ========================================
# ZUSAMMENFASSUNG
# ========================================
print("\n" + "="*70)
if all(results):
    print("🎉 SORGLOSER ZUGRIFF FUNKTIONIERT!")
    print(f"   Alle 4 Dictionaries mit {DICT_GUID} erreichbar!")
    print(f"   ✨ Kein Nachdenken mehr über GUIDs nötig!")
else:
    print("⚠️  PROBLEM: Nicht alle Dictionaries erreichbar!")
    print(f"   Erfolge: {sum(results)}/{len(results)}")
