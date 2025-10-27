# -*- coding: utf-8 -*-
"""Fügt _get_visible_columns() Methode hinzu"""

with open('pdvm_view_daten_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Finde rebuild_pipeline_with_stichtag
insert_index = None
for i, line in enumerate(lines):
    if "def rebuild_pipeline_with_stichtag(self):" in line:
        insert_index = i
        print(f"✅ Gefunden rebuild_pipeline_with_stichtag in Zeile {i+1}")
        break

if insert_index:
    # Füge _get_visible_columns DAVOR ein
    indent = "    "
    new_method = [
        f"{indent}def _get_visible_columns(self):\n",
        f"{indent}    \"\"\"\n",
        f"{indent}    Ermittelt sichtbare Spalten mit SPEZIAL-Logik.\n",
        f"{indent}    \n",
        f"{indent}    WICHTIG: name_original und name_show sind IMMER sichtbar!\n",
        f"{indent}    \n",
        f"{indent}    Returns:\n",
        f"{indent}        list: Liste der sichtbaren Spalten-Namen\n",
        f"{indent}    \"\"\"\n",
        f"{indent}    visible_columns = []\n",
        f"{indent}    for col in self.basis_columns:\n",
        f"{indent}        col_name = col['name']\n",
        f"{indent}        is_visible = col.get('show', False)\n",
        f"{indent}        \n",
        f"{indent}        # SPEZIAL: name_original und name_show sind IMMER sichtbar\n",
        f"{indent}        if col_name in ('name_original', 'name_show'):\n",
        f"{indent}            is_visible = True\n",
        f"{indent}        \n",
        f"{indent}        if is_visible:\n",
        f"{indent}            visible_columns.append(col_name)\n",
        f"{indent}    \n",
        f"{indent}    return visible_columns\n",
        f"{indent}\n",
    ]
    
    lines[insert_index:insert_index] = new_method
    print(f"✅ {len(new_method)} Zeilen eingefügt vor rebuild_pipeline_with_stichtag")
    
    # Schreibe zurück
    with open('pdvm_view_daten_manager.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Datei gespeichert")
else:
    print("❌ rebuild_pipeline_with_stichtag nicht gefunden")
