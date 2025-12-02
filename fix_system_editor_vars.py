"""Ersetzt self.view_data durch self.data im System-Editor"""
import re

# Datei einlesen
with open('pdvm_view_editor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetzen
content = content.replace('self.view_data', 'self.data')
content = content.replace('self.view_db', 'self.edit_db')
content = content.replace('self.view_guid', 'self.edit_guid')

# _get_table_name vereinfachen
old_method = """    def _get_table_name(self):
        \"\"\"Gibt ROOT_TABLE zurück (aus framedaten, bereits in __init__ validiert)\"\"\"
        return self.root_table"""

new_method = """    def _get_table_name(self):
        \"\"\"Gibt ROOT_TABLE zurück (aus framedaten)\"\"\"
        return self.root_table"""

content = content.replace(old_method, new_method)

# Speichern
with open('pdvm_view_editor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Ersetzungen durchgeführt:")
print(f"   - self.view_data → self.data")
print(f"   - self.view_db → self.edit_db")
print(f"   - self.view_guid → self.edit_guid")
