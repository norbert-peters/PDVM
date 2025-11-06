"""
Check V3 Migration Status
Prüft ob V3 Menüdaten in den richtigen Datenbanken sind
"""
import sqlite3
import os

def check_database(db_path, mandant_name):
    """Prüft eine Datenbank auf V3 Menü-Tabellen"""
    print(f"\n{'='*80}")
    print(f"🔍 {mandant_name}: {db_path}")
    print('='*80)
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank existiert nicht!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alle menudaten.* Tabellen finden
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'menudaten.%'
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    
    if not tables:
        print("❌ Keine V3 Menü-Tabellen gefunden!")
    else:
        print(f"✅ {len(tables)} V3 Menü-Tabellen gefunden:\n")
        for table in tables:
            table_name = table[0]
            # GUID aus Tabellenname extrahieren
            guid = table_name.replace('menudaten.', '')
            
            # Menü-Name aus META holen
            try:
                cursor.execute(f'SELECT wert FROM "{table_name}" WHERE gruppe="META" AND feld="name"')
                result = cursor.fetchone()
                menu_name = result[0] if result else "Unknown"
            except:
                menu_name = "Unknown"
            
            # Anzahl Items zählen
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE gruppe IN ("VERTIKAL", "GRUND", "ZUSATZ")')
            item_count = cursor.fetchone()[0]
            
            print(f"  📋 {menu_name}")
            print(f"     GUID: {guid}")
            print(f"     Items: {item_count}")
            print()
    
    conn.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔄 V3 MIGRATION STATUS CHECK")
    print("="*80)
    
    # Mandant 1
    check_database(
        "Daten/mandant_001/datenbank.db",
        "MANDANT 1"
    )
    
    # Mandant 2
    check_database(
        "Daten/mandant_002/datenbank.db",
        "MANDANT 2"
    )
    
    # Falsche Location (falls da migriert wurde)
    print("\n" + "="*80)
    print("🔍 Prüfe falsche Location (MyApplication Root)...")
    print("="*80)
    
    if os.path.exists("datenbank.db"):
        check_database("datenbank.db", "ROOT (FALSCH)")
    else:
        print("\n✅ Keine datenbank.db in Root gefunden (gut!)")
    
    print("\n" + "="*80)
    print("✅ CHECK ABGESCHLOSSEN")
    print("="*80)
