#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix: Controls in "controls" Dictionary speichern statt in "ColumnControls"
"""

import re

FILE_PATH = "pdvm_view_daten_manager.py"

# Lese Datei
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Finde den Block
old_code = r'''        # SCHRITT 5: Persistierung nur bei neuen Controls UND first_call
        # Bei Refresh \(first_call=False\) niemals speichern!
        if found_new_controls and self\.first_call:
            persist_map = \{col\['name'\]: \{
                'show': col\['show'\],
                'expertOrder': col\['expertOrder'\],
                'displayOrder': col\['displayOrder'\]
            \} for col in columns\}
            
            try:
                gcs\(\)\.set_value\(gruppe=self\.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001\.0\)
                gcs\(\)\.save_values\(\)
                logger\.info\(f".*Neue Controls in Systemsteuerung gespeichert.*"\)
            except Exception as e:
                logger\.warning\(f".*Konnte ColumnControl-Attribute nicht speichern.*"\)
        elif found_new_controls and not self\.first_call:
            logger\.info\(f".*Neue Controls erkannt aber NICHT gespeichert.*"\)
        else:
            logger\.info\(f".*Keine neuen Controls - keine Persistierung erforderlich.*"\)'''

new_code = '''        # SCHRITT 5: Persistierung nur bei neuen Controls UND first_call
        # Bei Refresh (first_call=False) niemals speichern!
        if found_new_controls and self.first_call:
            try:
                # Hole existierendes controls Dictionary aus GCS
                existing_controls, _ = gcs().db.get_value(self.view_guid, "controls")
                if not existing_controls or not isinstance(existing_controls, dict):
                    existing_controls = {}
                    logger.info(f"Erstelle neues controls Dictionary fuer {self.view_guid}")
                else:
                    logger.info(f"Lade existierendes controls Dictionary mit {len(existing_controls)} Controls")
                
                # Merge neue/geaenderte Controls (komplettes Control-Objekt!)
                new_count = 0
                updated_count = 0
                for col in columns:
                    control_name = col['name']
                    if control_name not in existing_controls:
                        # Neues Control - komplettes Objekt speichern
                        existing_controls[control_name] = col
                        new_count += 1
                        logger.debug(f"  Neues Control: {control_name}")
                    else:
                        # Existierendes Control - nur Attribute aktualisieren
                        existing_controls[control_name]['show'] = col['show']
                        existing_controls[control_name]['expertOrder'] = col['expertOrder']
                        existing_controls[control_name]['displayOrder'] = col['displayOrder']
                        updated_count += 1
                
                # Speichere zurueck ins controls Dictionary
                gcs().db.set_value(self.view_guid, "controls", existing_controls)
                gcs().save_values()
                logger.info(f"Controls gespeichert fuer {self.view_guid}: {new_count} neue, {updated_count} aktualisiert, {len(existing_controls)} total")
                
                # Projektionen neu bauen damit neue Controls sichtbar werden
                gcs().rebuild_projection_tables(self.view_guid)
                logger.info(f"Projektions-Tabellen neu gebaut mit allen {len(existing_controls)} Controls")
                
            except Exception as e:
                logger.warning(f"Konnte Controls nicht speichern: {e}")
                import traceback
                logger.error(traceback.format_exc())
        elif found_new_controls and not self.first_call:
            logger.info(f"Neue Controls erkannt aber NICHT gespeichert (Refresh-Modus, first_call=False)")
        else:
            logger.info(f"Keine neuen Controls - keine Persistierung erforderlich")'''

# Ersetze
content_new = re.sub(old_code, new_code, content, flags=re.MULTILINE | re.DOTALL)

if content != content_new:
    print("✅ Ersetzung erfolgreich!")
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content_new)
    print(f"✅ Datei gespeichert: {FILE_PATH}")
else:
    print("❌ Kein Match gefunden")
