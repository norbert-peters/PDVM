#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyse der TATSÄCHLICHEN Datenstruktur aus User-Beispiel

Zeigt wie Controls WIRKLICH gespeichert sind
"""

import json

# Original User-Daten (gekürzt für Übersicht)
user_data_raw = """
{
  "0d10a0d0-b1a5-4544-b284-e8a09ca979b5": {
    "controls": {
      "uid_original": {"gruppe": "SYSTEM", "show": false, "expert_order": 2},
      "name_original": {"gruppe": "SYSTEM", "show": false, "expert_order": 20},
      "familienname_original": {"gruppe": "PERSDATEN", "show": false},
      "uid_show": {"gruppe": "SYSTEM", "show": true, "display_order": 1},
      "name_show": {"gruppe": "SYSTEM", "show": true, "display_order": 11}
    },
    "uid_original": "{\\"gruppe\\": \\"SYSTEM\\", ...}",
    "name_original": "{\\"gruppe\\": \\"SYSTEM\\", ...}",
    "familienname_original": "{\\"gruppe\\": \\"PERSDATEN\\", ...}",
    "uid_show": "{\\"gruppe\\": \\"SYSTEM\\", ...}",
    "name_show": "{\\"gruppe\\": \\"SYSTEM\\", ...}"
  }
}
"""

print("\n" + "="*80)
print("TATSÄCHLICHE DATENSTRUKTUR - ANALYSE")
print("="*80)

print("\n📊 STRUKTUR PRO VIEW:")
print("─"*80)
print("""
{
  "view-guid": {
    
    ┌─ VARIANTE 1: Dictionary (für GCS Projektion)
    │
    "controls": {
      "uid_original": {komplettes Control-Objekt},
      "name_original": {komplettes Control-Objekt},
      "familienname_original": {komplettes Control-Objekt},
      ...
    },
    
    ┌─ VARIANTE 2: Einzelne Felder (für direkte get_value Zugriffe)
    │
    "uid_original": "{JSON-String des Control-Objekts}",
    "name_original": "{JSON-String des Control-Objekts}",
    "familienname_original": "{JSON-String des Control-Objekts}",
    ...
  }
}
""")

print("\n✅ BEIDE VARIANTEN PARALLEL GESPEICHERT!")
print("─"*80)
print("""
WARUM?
- controls Dictionary    → Für _build_projection_tables() (alle auf einmal)
- Einzelne Felder        → Für get_value(view_guid, "uid_original") (einzeln)
- REDUNDANT aber FUNKTIONAL!
""")

print("\n🔍 WAS BEDEUTET DAS FÜR name_original?")
print("─"*80)
print("""
FRAGE: Ist name_original im "controls" Dictionary?

Aus User-Daten:
  "0d10a0d0-b1a5-4544-b284-e8a09ca979b5": {
    "controls": {
      "uid_original": {...},
      "familienname_original": {...},
      "vorname_original": {...},
      ...
      ❌ "name_original": FEHLT!
      ❌ "name_show": FEHLT!
    }
  }

ERGEBNIS: name_original wurde NICHT ins controls-Dictionary aufgenommen!
""")

print("\n🎯 LÖSUNG:")
print("─"*80)
print("""
Wenn View-Manager neue Controls erstellt (name_original, name_show):

1. Controls werden in basis_columns[] erstellt ✅
2. Beim Speichern MUSS passieren:
   
   a) In "controls" Dictionary einfügen:
      gcs.db.get_value(view_guid, "controls") → Dictionary holen
      controls_dict["name_original"] = name_orig_control
      controls_dict["name_show"] = name_show_control
      gcs.db.set_value(view_guid, "controls", controls_dict) → Speichern
   
   b) Als einzelne Felder speichern (optional, für Kompatibilität):
      gcs.db.set_value(view_guid, "name_original", json.dumps(name_orig_control))
      gcs.db.set_value(view_guid, "name_show", json.dumps(name_show_control))

3. GCS rebuild_projection_tables() aufrufen
   → Liest controls-Dictionary → Baut Projektionen → name_original erscheint!
""")

print("\n📝 AKTUELLER CODE MACHT:")
print("─"*80)
print("""
pdvm_view_daten_manager.py Zeile 921:

  gcs().set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map)
                                              ↑
                                              FALSCHER FELDNAME!
                                              
Sollte sein:

  # 1. Hole existierendes controls Dictionary
  existing_controls, _ = gcs().db.get_value(self.view_guid, "controls")
  if not existing_controls:
      existing_controls = {}
  
  # 2. Merge neue Controls rein
  for control_name, attrs in persist_map.items():
      if control_name in existing_controls:
          # Update nur Attribute (show, orders)
          existing_controls[control_name].update(attrs)
      else:
          # Neues Control komplett hinzufügen
          # (aus basis_columns holen)
          full_control = [col for col in self.basis_columns if col['name'] == control_name][0]
          existing_controls[control_name] = full_control
  
  # 3. Zurück speichern
  gcs().db.set_value(self.view_guid, "controls", existing_controls)
  gcs().save_values()
  
  # 4. Projektionen neu bauen
  gcs().rebuild_projection_tables(self.view_guid)
""")

print("\n✅ ZUSAMMENFASSUNG:")
print("="*80)
print("""
1. Datenstruktur ist KORREKT (wie du sagst!)
2. Controls sind im "controls" Dictionary (nicht "ColumnControls")
3. name_original/name_show werden erstellt ABER
4. Sie werden NICHT ins "controls" Dictionary eingefügt!
5. Daher findet GCS sie nicht → Projektion leer

FIX: View-Manager muss ins "controls" Dictionary schreiben, nicht "ColumnControls"
""")
print("="*80 + "\n")
