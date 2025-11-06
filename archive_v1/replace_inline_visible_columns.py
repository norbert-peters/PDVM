# -*- coding: utf-8 -*-
"""Ersetzt inline visible_columns durch _get_visible_columns() Aufruf"""

with open('pdvm_view_daten_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ersetze den Block
old_block = """            # Sichtbare Spalten ermitteln - IMMER name_original und name_show einschließen
            visible_columns = []
            for col in self.basis_columns:
                col_name = col['name']
                is_visible = col.get('show', False)
                
                # SPEZIAL: name_original und name_show sind IMMER sichtbar
                if col_name in ('name_original', 'name_show'):
                    is_visible = True
                
                if is_visible:
                    visible_columns.append(col_name)"""

new_block = """            # Sichtbare Spalten ermitteln (mit name_original/name_show IMMER sichtbar)
            visible_columns = self._get_visible_columns()"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Inline-Code durch Methoden-Aufruf ersetzt")
    
    with open('pdvm_view_daten_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Datei gespeichert")
else:
    print("❌ Alter Code-Block nicht gefunden")
    print("\nSuche nach Varianten...")
    if "visible_columns = []" in content:
        print("  ✅ visible_columns = [] gefunden")
    if "name_original" in content and "name_show" in content:
        print("  ✅ name_original/name_show vorhanden")
