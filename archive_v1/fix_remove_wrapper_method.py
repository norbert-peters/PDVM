#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Entfernt _get_visible_columns_from_gcs() Wrapper und ersetzt mit direktem GCS-Aufruf
"""

import re

file_path = 'c:/Users/norbe/OneDrive/Dokumente/MyApplication/pdvm_view_dialog.py'

# Lese Datei
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("🔍 Suche Aufrufe von _get_visible_columns_from_gcs()...")

# Pattern für Methoden-Aufrufe
pattern = r'(\s+)visible_columns\s*=\s*self\._get_visible_columns_from_gcs\(\)'

matches = list(re.finditer(pattern, content))
print(f"   Gefunden: {len(matches)} Aufrufe")

# Ersetze alle Aufrufe mit direktem GCS-Zugriff
replacement = r'''\1# ✅ DIREKT aus GCS-Projektion (ohne Wrapper)
\1from pdvm_central_systemsteuerung import get_gcs
\1gcs_temp = get_gcs()
\1projection_index = 5 if (gcs_temp and gcs_temp.expert_mode) else 0
\1visible_columns = gcs_temp.get_projection_table(self.view_guid, projection_index) if gcs_temp else []'''

content_new = re.sub(pattern, replacement, content)

print(f"✅ Ersetzt: {len(matches)} Aufrufe")

# Schreibe zurück
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content_new)

print(f"💾 Datei gespeichert: {file_path}")
print("\n⚠️  HINWEIS: Die Methode _get_visible_columns_from_gcs() kann jetzt manuell gelöscht werden!")
