# -*- coding: utf-8 -*-
"""Debug: Warum zeigt Viewtable History 'kein Name'?"""
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*60)
print("🔍 DEBUG: Viewtable History Name-Problem")
print("="*60)

# Test mit finanzstamm (wie User berichtet)
print("\n[1] Teste finanzstamm Tabelle...")
finanz_db = PdvmCentralDatenbank(table_name="finanzstamm")

# Hole alle Records
all_records = finanz_db.get_all_records()
print(f"✅ {len(all_records)} Datensätze gefunden")

# Prüfe ersten Datensatz
if all_records:
    first = all_records[0]
    guid = first['uid']
    
    print(f"\n[2] Prüfe Datensatz {guid[:8]}...")
    
    # Direkt get_name aufrufen
    name = finanz_db.get_name(guid)
    print(f"  get_name('{guid[:8]}...'): '{name}'")
    
    # Prüfe auch direkt in Basis-DB
    from pdvm_datenbank import PdvmDatenbank
    basis_db = PdvmDatenbank(table_name="finanzstamm")
    name_basis = basis_db.get_name(guid)
    print(f"  Basis-DB get_name(): '{name_basis}'")
    
    # Prüfe DB-Struktur
    import sqlite3
    conn = sqlite3.connect(basis_db.db_name)
    cursor = conn.cursor()
    
    # Prüfe ob 'name' Spalte existiert
    cursor.execute(f"PRAGMA table_info(finanzstamm)")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    print(f"\n[3] Spalten in finanzstamm: {col_names}")
    
    if 'name' in col_names:
        print("  ✅ 'name' Spalte existiert")
        
        # Hole name-Wert direkt aus DB
        cursor.execute(f"SELECT name FROM finanzstamm WHERE uid = ?", (guid,))
        result = cursor.fetchone()
        if result:
            db_name = result[0]
            print(f"  DB name-Wert: '{db_name}'")
        else:
            print(f"  ⚠️ Kein Datensatz gefunden")
    else:
        print("  ❌ 'name' Spalte FEHLT!")
    
    conn.close()
    
    print("\n[4] Simuliere History-Dialog Logik...")
    
    # Simuliere _get_name_for_viewtable_guid
    field_config = {
        'viewtable_config': {
            'table_name': 'finanzstamm'
        }
    }
    
    # Wie im Dialog
    viewtable_config = field_config.get('viewtable_config', {})
    table_name = viewtable_config.get('table_name')
    
    print(f"  table_name aus config: '{table_name}'")
    
    # Neue DB-Instanz erstellen (wie im Dialog)
    ref_db = PdvmCentralDatenbank(table_name=table_name, guid=guid)
    name_from_dialog = ref_db.get_name(guid)
    
    print(f"  get_name() wie im Dialog: '{name_from_dialog}'")
    
else:
    print("❌ Keine Datensätze in finanzstamm!")

print("\n" + "="*60)
print("✅ DEBUG ABGESCHLOSSEN")
print("="*60)
