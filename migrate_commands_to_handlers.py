"""
Aktualisiert migrierte Commands für Handler-System
===================================================
Konvertiert alte Python-Code-Strings zu Handler-Calls mit Parametern

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import sqlite3
import json
import re

def convert_command_to_handler(command_string: str) -> tuple:
    """
    Konvertiert alten Command-String zu Handler-Name + Params
    
    Returns:
        (handler_name, params_dict)
    """
    if not command_string:
        return ('noop', {})
    
    # PATTERN 1: self.logout()
    if 'logout' in command_string:
        return ('logout', {})
    
    # PATTERN 2: self.open_start_menu() oder self.pdvm_start(...)
    if 'open_start_menu' in command_string or 'pdvm_start' in command_string:
        # Extrahiere Parameter
        match = re.search(r"pdvm_start\('([^']+)'\)", command_string)
        if match:
            app_name = match.group(1)
            return ('open_app_menu', {'app_name': app_name})
        return ('open_start_menu', {})
    
    # PATTERN 3: self.pdvm_modern_view('guid')
    if 'pdvm_modern_view' in command_string:
        match = re.search(r"pdvm_modern_view\('([^']+)'\)", command_string)
        if match:
            view_guid = match.group(1)
            return ('open_view', {'view_guid': view_guid, 'view_type': 'modern'})
    
    # PATTERN 4: self.pdvm_dialog('guid', mode)
    if 'pdvm_dialog' in command_string:
        match = re.search(r"pdvm_dialog\('([^']+)',\s*(\d+)\)", command_string)
        if match:
            dialog_guid = match.group(1)
            dialog_mode = int(match.group(2))
            return ('show_dialog', {'dialog_guid': dialog_guid, 'dialog_mode': dialog_mode})
    
    # PATTERN 5: self.start_dialog('guid')
    if 'start_dialog' in command_string:
        match = re.search(r"start_dialog\('([^']+)'\)", command_string)
        if match:
            dialog_guid = match.group(1)
            return ('show_dialog', {'dialog_guid': dialog_guid})
    
    # PATTERN 6: self.toggle_menu_visibility()
    if 'toggle_menu' in command_string:
        return ('toggle_menu', {})
    
    # PATTERN 7: self.show_text_klein(...)
    if 'show_text_klein' in command_string:
        match = re.search(r"show_text_klein\('([^']+)'\)", command_string)
        if match:
            help_text = match.group(1)
            return ('show_help', {'help_topic': help_text})
    
    # PATTERN 8: self.open_menu_editor(...)
    if 'open_menu_editor' in command_string:
        match = re.search(r"open_menu_editor\('([^']+)'\)", command_string)
        if match:
            menu_name = match.group(1)
            return ('open_menu_editor', {'menu_name': menu_name})
    
    # PATTERN 9: Andere Methoden → execute_python
    # Alle anderen Code-Strings werden als execute_python mit method_name behandelt
    method_match = re.search(r"self\.(\w+)\((.*?)\)", command_string)
    if method_match:
        method_name = method_match.group(1)
        args_str = method_match.group(2)
        
        # Einfache Parameter extrahieren
        params = {'method_name': method_name}
        if args_str:
            # Versuche String-Parameter zu extrahieren
            string_matches = re.findall(r"'([^']+)'", args_str)
            if string_matches:
                if len(string_matches) == 1:
                    params['arg1'] = string_matches[0]
                elif len(string_matches) > 1:
                    for i, val in enumerate(string_matches):
                        params[f'arg{i+1}'] = val
        
        return ('execute_python', params)
    
    # Fallback: execute_python mit Code-String
    return ('execute_python', {'code': command_string})


def update_menu_commands(db_path: str):
    """Aktualisiert Commands in einer Mandanten-DB"""
    print(f"\n{'='*80}")
    print(f"🔧 Aktualisiere: {db_path}")
    print(f"{'='*80}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lade alle Menüs
    cursor.execute("SELECT uid, name, daten FROM sys_menudaten")
    rows = cursor.fetchall()
    
    updated_count = 0
    for uid, name, daten_json in rows:
        try:
            menu_data = json.loads(daten_json)
            
            if 'COMMANDS' not in menu_data:
                continue
            
            print(f"\n📂 Menü: {name}")
            commands_updated = 0
            
            for command in menu_data['COMMANDS']:
                old_handler = command.get('HANDLER', '')
                
                # Überspringe schon konvertierte
                if old_handler in ['open_view', 'show_dialog', 'logout', 'toggle_menu', 
                                  'show_help', 'execute_python', 'open_app_menu']:
                    continue
                
                # Konvertiere
                new_handler, new_params = convert_command_to_handler(old_handler)
                
                if new_handler != old_handler:
                    print(f"   🔄 {command['NAME']}")
                    print(f"      Alt: {old_handler[:80]}")
                    print(f"      Neu: {new_handler} + {new_params}")
                    
                    command['HANDLER'] = new_handler
                    command['PARAMS'] = new_params
                    commands_updated += 1
            
            if commands_updated > 0:
                # Speichere zurück
                new_json = json.dumps(menu_data, ensure_ascii=False, indent=2)
                cursor.execute(
                    "UPDATE sys_menudaten SET daten = ? WHERE uid = ?",
                    (new_json, uid)
                )
                updated_count += 1
                print(f"   ✅ {commands_updated} Commands aktualisiert")
        
        except Exception as e:
            print(f"   ❌ Fehler bei {name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {updated_count} Menüs aktualisiert")


def main():
    """Hauptfunktion"""
    print("🚀 PDVM Handler-Migration")
    print("="*80)
    print("Konvertiert alte Python-Code-Strings zu Handler-Calls")
    print()
    
    # Mandant 001
    update_menu_commands("Daten/mandant_001/datenbank.db")
    
    # Mandant 002
    update_menu_commands("Daten/mandant_002/datenbank.db")
    
    print(f"\n\n{'='*80}")
    print("🎉 HANDLER-MIGRATION ABGESCHLOSSEN")
    print(f"{'='*80}")
    print()
    print("📝 ÄNDERUNGEN:")
    print("  • Python-Code-Strings → Handler-Namen")
    print("  • Parameter extrahiert und strukturiert")
    print("  • Fallback: execute_python für unbekannte Methoden")
    print()
    print("🔍 NÄCHSTE SCHRITTE:")
    print("  1. Test mit: python v2_main.py")
    print("  2. Menü-Commands sollten jetzt funktionieren")
    print()


if __name__ == "__main__":
    main()
