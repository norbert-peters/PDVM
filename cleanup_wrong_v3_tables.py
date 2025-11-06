"""
Cleanup: Entfernt falsch erstellte V3-Tabellen
================================================
Entfernt alle menudaten.{guid} Tabellen die fälschlicherweise
erstellt wurden anstatt die bestehende sys_menudaten zu nutzen.

Autor: PDVM V3.0 Cleanup
Datum: 02.11.2025
"""

import sqlite3
import os

def cleanup_database(db_path: str, mandant_name: str):
    """
    Entfernt alle menudaten.* Tabellen aus einer Datenbank
    
    Args:
        db_path: Pfad zur Datenbank
        mandant_name: Name für Ausgabe
    """
    print(f"\n{'='*80}")
    print(f"🧹 Cleanup: {mandant_name}")
    print(f"   {db_path}")
    print('='*80)
    
    if not os.path.exists(db_path):
        print(f"❌ Datenbank nicht gefunden!")
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
        print("✅ Keine falschen Tabellen gefunden!")
    else:
        print(f"📋 Gefunden: {len(tables)} falsche Tabellen\n")
        
        for table in tables:
            table_name = table[0]
            
            # Tabelle löschen
            try:
                cursor.execute(f'DROP TABLE "{table_name}"')
                print(f"   ✅ Gelöscht: {table_name}")
            except Exception as e:
                print(f"   ❌ Fehler bei {table_name}: {e}")
        
        conn.commit()
        print(f"\n✅ {len(tables)} Tabellen entfernt!")
    
    conn.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧹 CLEANUP: Falsche V3-Tabellen entfernen")
    print("="*80)
    print("\nEntfernt alle menudaten.{guid} Tabellen")
    print("Diese wurden fälschlicherweise erstellt anstatt")
    print("die bestehende sys_menudaten Tabelle zu nutzen.")
    print("\n" + "="*80)
    
    # Mandant 1
    cleanup_database(
        "Daten/mandant_001/datenbank.db",
        "MANDANT 1"
    )
    
    # Mandant 2
    cleanup_database(
        "Daten/mandant_002/datenbank.db",
        "MANDANT 2"
    )
    
    print("\n" + "="*80)
    print("✅ CLEANUP ABGESCHLOSSEN")
    print("="*80)
