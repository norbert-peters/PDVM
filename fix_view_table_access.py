"""Ersetzt alle VIEW_TABLE-Zugriffe durch Helper-Methode"""
import re

# Datei einlesen
with open('pdvm_view_editor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern: view_table = self.view_data['ROOT'].get('VIEW_TABLE', '')
pattern = r"view_table = self\.view_data\['ROOT'\]\.get\('VIEW_TABLE', ''\)"
replacement = "view_table = self._get_table_name()"

# Ersetzen
new_content = re.sub(pattern, replacement, content)

# Zählen
count = len(re.findall(pattern, content))
print(f"✅ {count} Vorkommen ersetzt")

# Speichern
with open('pdvm_view_editor.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Datei gespeichert")
