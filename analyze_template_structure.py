"""Analysiert Template-Struktur für Editor-Design"""
import sqlite3
import json

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

# Erst Tabellen-Struktur prüfen
cursor.execute("PRAGMA table_info(sys_viewdaten)")
columns = cursor.fetchall()
print("Tabellen-Spalten:", [col[1] for col in columns])

# uid = 55555555-5555-5555-5555-555555555555
cursor.execute('SELECT * FROM sys_viewdaten WHERE uid = "55555555-5555-5555-5555-555555555555"')
row = cursor.fetchone()

if row:
    # daten ist Spalte 2 (index 1)
    data = json.loads(row[1])
    
    print("=" * 80)
    print("TEMPLATE-STRUKTUR ANALYSE")
    print("=" * 80)
    
    print("\n📋 ROOT Keys:")
    for key in data.get('ROOT', {}).keys():
        print(f"  - {key}")
    
    print("\n📂 METADATEN Keys:")
    metadaten = data.get('METADATEN', {})
    for key in metadaten.keys():
        print(f"  - {key}")
    
    print("\n🔧 TEMPLATES Keys:")
    templates = metadaten.get('TEMPLATES', {})
    for key in templates.keys():
        print(f"  - {key}")
        # Erste Ebene der Struktur anzeigen
        template_data = templates[key]
        if isinstance(template_data, dict):
            print(f"    Felder: {list(template_data.keys())}")
    
    print("\n⚙️ ROOT_CONTROLS Keys:")
    root_controls = metadaten.get('ROOT_CONTROLS', {})
    for key in root_controls.keys():
        control = root_controls[key]
        print(f"  - {key}: {control.get('label', 'N/A')} ({control.get('control_type', 'text')})")
    
    print("\n🎨 CONTROL_PROPERTIES Keys:")
    control_props = metadaten.get('CONTROL_PROPERTIES', {})
    for key in control_props.keys():
        prop = control_props[key]
        print(f"  - {key}: {prop.get('label', 'N/A')} ({prop.get('control_type', 'text')})")
    
    # Beispiel: Ein komplettes Template anzeigen
    print("\n" + "=" * 80)
    print("BEISPIEL: TEMPLATES Structure")
    print("=" * 80)
    if templates:
        first_template_key = list(templates.keys())[0]
        print(f"\nTemplate: {first_template_key}")
        print(json.dumps(templates[first_template_key], indent=2, ensure_ascii=False))
    
    # Vergleich: Normale View-Struktur
    cursor.execute('SELECT * FROM sys_viewdaten WHERE uid != "55555555-5555-5555-5555-555555555555" LIMIT 1')
    view_row = cursor.fetchone()
    if view_row:
        view_data = json.loads(view_row[1])
        print("\n" + "=" * 80)
        print("VERGLEICH: Normale View-Struktur")
        print("=" * 80)
        print(f"\nView GUID: {view_row[0]}")
        print(f"ROOT Keys: {list(view_data.get('ROOT', {}).keys())}")
        metadaten = view_data.get('METADATEN', {})
        print(f"METADATEN Keys (oberste Ebene): {list(metadaten.keys())}")
        if metadaten:
            # Erste METADATEN-Ebene analysieren
            first_key = list(metadaten.keys())[0]
            print(f"\nErste METADATEN-Ebene Beispiel ({first_key}):")
            first_data = metadaten[first_key]
            if isinstance(first_data, dict):
                print(f"  Typ: Dict mit {len(first_data)} Einträgen")
                print(f"  Keys: {list(first_data.keys())[:5]}...")  # Erste 5
            elif isinstance(first_data, list):
                print(f"  Typ: List mit {len(first_data)} Einträgen")

conn.close()

print("\n" + "=" * 80)
print("✅ ANALYSE ABGESCHLOSSEN")
print("=" * 80)
