"""Quick check: Type-Feld der VERTIKAL Menu Items"""
import sqlite3

conn = sqlite3.connect('Daten/datenbank.db')
cursor = conn.cursor()

result = cursor.execute("""
    SELECT guid, label, type, parent_guid, sort_order 
    FROM menu 
    WHERE menu_guid='5ca6674e-b9ce-4581-9756-64e742883f80' 
    AND gruppe='VERTIKAL' 
    ORDER BY sort_order
""").fetchall()

print("VERTIKAL Menu Items:")
for i, row in enumerate(result):
    guid, label, item_type, parent_guid, sort_order = row
    parent_str = parent_guid[:8] + "..." if parent_guid else "None"
    print(f"  {i+1}. Label='{label}', Type='{item_type}', GUID={guid[:8]}..., Parent={parent_str}, Sort={sort_order}")

conn.close()
