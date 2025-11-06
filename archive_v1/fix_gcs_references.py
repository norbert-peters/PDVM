# -*- coding: utf-8 -*-
"""
Ersetzt 'gcs.' durch 'self.gcs.' in v2_column_management_dialog.py
ABER NUR außerhalb von Imports und Kommentaren
"""

import re

filename = "v2_column_management_dialog.py"

with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

# Regex: Ersetze 'gcs.' nur wenn NICHT 'self.gcs.' davor steht
# Negative Lookbehind: (?<!self\.)
pattern = r'(?<!self\.)gcs\.'
replacement = r'self.gcs.'

# Ersetzen
new_content = re.sub(pattern, replacement, content)

# Zähle Ersetzungen
count = len(re.findall(pattern, content))

# Schreiben
with open(filename, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ {count} Ersetzungen durchgeführt: 'gcs.' → 'self.gcs.'")
