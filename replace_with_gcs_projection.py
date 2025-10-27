# -*- coding: utf-8 -*-
"""Ersetzt _get_visible_columns() durch GCS-Projektion"""

with open('pdvm_view_daten_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Finde die Zeile mit visible_columns = self._get_visible_columns()
for i, line in enumerate(lines):
    if "visible_columns = self._get_visible_columns()" in line:
        print(f"✅ Gefunden in Zeile {i+1}")
        
        # Ersetze durch GCS-Projektion
        indent = "            "
        new_code = [
            f"{indent}# Hole Projektion aus GCS (berücksichtigt Expert Mode automatisch)\n",
            f"{indent}projection_table = gcs().get_current_projection(self.view_guid, 'table')\n",
            f"{indent}\n",
            f"{indent}if projection_table:\n",
            f"{indent}    visible_columns = projection_table\n",
            f"{indent}    logger.info(f\"👁️ Sichtbare Spalten aus GCS: {{len(visible_columns)}}\")\n",
            f"{indent}else:\n",
            f"{indent}    # Fallback: Alle Spalten außer dummy und row_type\n",
            f"{indent}    visible_columns = [col['name'] for col in self.basis_columns \n",
            f"{indent}                     if col['name'] not in ('dummy', 'row_type')]\n",
            f"{indent}    logger.warning(f\"⚠️ Keine GCS-Projektion - Fallback: {{len(visible_columns)}} Spalten\")\n"
        ]
        
        # Ersetze die eine Zeile
        lines[i:i+1] = new_code
        
        print(f"✅ Zeile ersetzt durch {len(new_code)} neue Zeilen")
        break

# Schreibe zurück
with open('pdvm_view_daten_manager.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Datei gespeichert - GCS-Projektion wird jetzt verwendet")
