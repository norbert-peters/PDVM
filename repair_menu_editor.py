"""
Repariert pdvm_menu_editor_widget.py
Entfernt ALLEN Duplikat-Code zwischen MenuItemEditor und MenuListWidget
"""

def repair_file():
    with open('pdvm_menu_editor_widget.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📂 Original-Datei hat {len(lines)} Zeilen")
    
    # Finde ALLE MenuListWidget Vorkommen
    menulist_lines = []
    for i, line in enumerate(lines):
        if 'class MenuListWidget(QWidget):' in line:
            menulist_lines.append(i)
            print(f"   MenuListWidget gefunden bei Zeile {i + 1}")
    
    if len(menulist_lines) < 2:
        print("❌ Keine doppelte MenuListWidget gefunden!")
        return False
    
    # Nehme die LETZTE (echte) MenuListWidget
    real_menulist_line = menulist_lines[-1]
    fake_menulist_line = menulist_lines[0]
    print(f"✅ Fake MenuListWidget: Zeile {fake_menulist_line + 1}")
    print(f"✅ Echte MenuListWidget: Zeile {real_menulist_line + 1}")
    
    # Finde Ende von MenuItemEditor (vor der ersten fake MenuListWidget)
    editor_end_line = None
    for i in range(fake_menulist_line - 1, max(0, fake_menulist_line - 10), -1):
        if 'return None' in lines[i]:
            editor_end_line = i
            print(f"✅ Ende von MenuItemEditor bei Zeile {i + 1}")
            break
    
    if not editor_end_line:
        print("❌ Konnte Ende von MenuItemEditor nicht finden!")
        return False
    
    # Berechne zu löschenden Bereich
    deleted_lines = real_menulist_line - (editor_end_line + 1)
    print(f"🗑️ Lösche {deleted_lines} Zeilen Müll (Zeile {editor_end_line + 2} bis {real_menulist_line})")
    
    # Neue Datei zusammenbauen
    new_lines = []
    new_lines.extend(lines[:editor_end_line + 1])  # Bis Ende MenuItemEditor
    new_lines.append('\n\n')  # 2 Leerzeilen
    new_lines.extend(lines[real_menulist_line:])  # Ab echter MenuListWidget
    
    # Backup erstellen
    with open('pdvm_menu_editor_widget.py.backup2', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"💾 Backup erstellt: pdvm_menu_editor_widget.py.backup2")
    
    # Reparierte Datei schreiben
    with open('pdvm_menu_editor_widget.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✅ Datei repariert! Neue Länge: {len(new_lines)} Zeilen (war {len(lines)})")
    print(f"   Gelöscht: {deleted_lines} Zeilen Duplikat-Code")
    
    return True

if __name__ == '__main__':
    repair_file()
