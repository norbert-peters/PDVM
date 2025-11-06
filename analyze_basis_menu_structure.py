"""
Analyse der Basis-Menü Struktur
================================
Zeigt die vollständige Hierarchie inkl. Parent-Child Beziehungen
"""

import sqlite3
import json

def analyze_basis_menu():
    print("=" * 80)
    print("🔍 ANALYSE: Basis-Menü Struktur")
    print("=" * 80)
    
    # Basis-Menü GUID
    basis_guid = "1a653694-3132-48d9-bc3e-a512962ae8e6"
    
    # Mandant 1 DB
    db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\mandant_001\datenbank.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lade Basis-Menü
    cursor.execute("""
        SELECT daten
        FROM sys_menudaten
        WHERE uid = ?
    """, (basis_guid,))
    
    row = cursor.fetchone()
    if not row:
        print(f"❌ Basis-Menü nicht gefunden: {basis_guid}")
        return
    
    data = json.loads(row[0])
    menu_name = data.get('MENU_NAME', 'Unbekannt')
    
    print(f"\n📋 Menü: {menu_name} ({basis_guid})")
    print(f"   VERTIKAL: {len(data.get('VERTIKAL', []))} Items")
    print(f"   GRUND: {len(data.get('GRUND', []))} Items")
    print(f"   ZUSATZ: {len(data.get('ZUSATZ', []))} Items")
    print(f"   COMMANDS: {len(data.get('COMMANDS', []))} Items")
    
    # Analysiere GRUND Items
    grund_items = data.get('GRUND', [])
    
    print(f"\n🔍 GRUND Items Hierarchie:")
    print("-" * 80)
    
    # Top-Level Items (ohne PARENT_GUID)
    top_level = [item for item in grund_items if not item.get('PARENT_GUID')]
    
    print(f"\n📂 Top-Level Items (ohne PARENT_GUID): {len(top_level)}")
    for item in top_level:
        guid = item.get('GUID')
        label = item.get('LABEL')
        item_type = item.get('TYPE')
        sort_order = item.get('SORT_ORDER')
        
        print(f"   {sort_order}. {label} ({item_type})")
        print(f"      GUID: {guid}")
        print(f"      COMMAND_GUID: {item.get('COMMAND_GUID')}")
        print(f"      ZUSATZ_GUID: {item.get('ZUSATZ_GUID')}")
        
        # Suche Children
        children = [c for c in grund_items if c.get('PARENT_GUID') == guid]
        if children:
            print(f"      └─ Children: {len(children)}")
            for child in children:
                child_label = child.get('LABEL')
                child_type = child.get('TYPE')
                child_sort = child.get('SORT_ORDER')
                print(f"         {child_sort}. {child_label} ({child_type})")
                print(f"            GUID: {child.get('GUID')}")
                print(f"            COMMAND_GUID: {child.get('COMMAND_GUID')}")
    
    # Child Items (mit PARENT_GUID)
    child_items = [item for item in grund_items if item.get('PARENT_GUID')]
    
    print(f"\n📂 Child Items (mit PARENT_GUID): {len(child_items)}")
    for item in child_items:
        label = item.get('LABEL')
        parent_guid = item.get('PARENT_GUID')
        sort_order = item.get('SORT_ORDER')
        
        # Finde Parent
        parent = next((p for p in grund_items if p.get('GUID') == parent_guid), None)
        parent_label = parent.get('LABEL') if parent else 'Unbekannt'
        
        print(f"   {sort_order}. {label} → Parent: {parent_label}")
    
    conn.close()

if __name__ == "__main__":
    analyze_basis_menu()
