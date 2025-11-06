# -*- coding: utf-8 -*-
"""Fügt name_original/name_show immer zur Projektion hinzu"""

with open('pdvm_view_daten_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Finde die Zeile mit visible_columns Zuweisung
for i, line in enumerate(lines):
    if "visible_columns = [col['name'] for col in self.basis_columns if col.get('show', False)]" in line:
        print(f"✅ Gefunden in Zeile {i+1}")
        
        # Ersetze die Zeile durch erweiterte Logik
        indent = "            "
        new_code = [
            f"{indent}# Sichtbare Spalten ermitteln - IMMER name_original und name_show einschließen\n",
            f"{indent}visible_columns = []\n",
            f"{indent}for col in self.basis_columns:\n",
            f"{indent}    col_name = col['name']\n",
            f"{indent}    is_visible = col.get('show', False)\n",
            f"{indent}    \n",
            f"{indent}    # SPEZIAL: name_original und name_show sind IMMER sichtbar\n",
            f"{indent}    if col_name in ('name_original', 'name_show'):\n",
            f"{indent}        is_visible = True\n",
            f"{indent}    \n",
            f"{indent}    if is_visible:\n",
            f"{indent}        visible_columns.append(col_name)\n"
        ]
        
        # Ersetze die eine Zeile durch mehrere
        lines[i:i+1] = new_code
        
        print(f"✅ Zeile ersetzt durch {len(new_code)} neue Zeilen")
        break

# Schreibe zurück
with open('pdvm_view_daten_manager.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Datei gespeichert")
