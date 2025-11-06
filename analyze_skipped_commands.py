#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysiert übersprungene Commands aus der Migration

AUTOR: Norbert Peters
DATUM: 02.11.2025
"""

import sqlite3
import json

def analyze_skipped_commands(db_path: str):
    """Analysiert übersprungene Commands"""
    
    print("=" * 80)
    print("🔍 ANALYSE: ÜBERSPRUNGENE COMMANDS")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Hole alle Menüs mit backup_daten
    cursor.execute('SELECT name, uid, daten_backup FROM sys_menudaten')
    menus = cursor.fetchall()
    
    skipped_commands = []
    
    for menu_name, menu_guid, backup_str in menus:
        if not backup_str:
            continue
        
        data = json.loads(backup_str)
        commands = data.get('PD_commands', {})
        menu_structure = data.get('PD_menu', {})
        grund_structure = data.get('PD_grund', {})
        
        for command_key, command_string in commands.items():
            if not command_string or command_string == "null":
                continue
            
            # Prüfe auf bekannte übersprungene Commands
            if any(pattern in command_string for pattern in [
                'pdvm_enhanced_test',
                'reload_current_frame_enhanced',
                'test_sortier_projektionen_diagnose'
            ]):
                # Finde zugehöriges Menu-Item
                item_found = False
                item_location = None
                
                # Suche in PD_menu (VERTIKAL)
                for label, children in menu_structure.items():
                    if label == command_key:
                        item_found = True
                        item_location = f"VERTIKAL: {label}"
                        break
                
                # Suche in PD_grund (GRUND)
                def search_grund(struktur, parent_label=""):
                    for label, children in struktur.items():
                        if label.startswith("---"):
                            continue
                        
                        # Baue Command-Key
                        if parent_label:
                            check_key = f"{parent_label}_{label}"
                        else:
                            check_key = label
                        
                        if check_key == command_key:
                            return True, f"GRUND: {parent_label}/{label}" if parent_label else f"GRUND: {label}"
                        
                        # Rekursiv in Children suchen
                        if isinstance(children, dict) and children:
                            found, location = search_grund(children, label)
                            if found:
                                return found, location
                    
                    return False, None
                
                if not item_found:
                    item_found, item_location = search_grund(grund_structure)
                
                skipped_commands.append({
                    'menu': menu_name,
                    'menu_guid': menu_guid,
                    'command_key': command_key,
                    'command_string': command_string,
                    'has_menu_item': item_found,
                    'item_location': item_location
                })
    
    conn.close()
    
    # Ausgabe
    print(f"\n📊 Gefunden: {len(skipped_commands)} übersprungene Commands\n")
    
    for item in skipped_commands:
        print(f"{'─'*80}")
        print(f"📋 Menü: {item['menu']}")
        print(f"   GUID: {item['menu_guid']}")
        print(f"   Command-Key: {item['command_key']}")
        print(f"   Command: {item['command_string']}")
        print(f"   Hat Menu-Item: {'✅ JA' if item['has_menu_item'] else '❌ NEIN'}")
        if item['item_location']:
            print(f"   Location: {item['item_location']}")
        print()
    
    # Zusammenfassung
    print(f"\n{'='*80}")
    print("📊 ZUSAMMENFASSUNG")
    print(f"{'='*80}")
    
    with_items = sum(1 for item in skipped_commands if item['has_menu_item'])
    without_items = len(skipped_commands) - with_items
    
    print(f"\n✅ Mit Menu-Item: {with_items}")
    print(f"❌ Ohne Menu-Item: {without_items}")
    
    if with_items > 0:
        print(f"\n⚠️  WICHTIG: {with_items} Commands haben Menu-Items und brauchen Handler!")
        print("\nEmpfohlene Handler:")
        print(f"{'─'*80}")
        
        for item in skipped_commands:
            if item['has_menu_item']:
                func_name = item['command_string'].split('(')[0].replace('self.', '')
                print(f"\n🔹 {item['command_key']}")
                print(f"   Original: {item['command_string']}")
                print(f"   Funktion: {func_name}()")
                
                # Handler-Vorschlag
                if 'test' in func_name.lower():
                    print(f"   → Handler: show_info")
                    print(f"      PARAMS: {{'message': 'Test-Funktion: {func_name}', 'title': '{item['command_key']}'}}")
                elif 'reload' in func_name.lower():
                    print(f"   → Handler: reload_view")
                    print(f"      PARAMS: {{}}")
                else:
                    print(f"   → Handler: show_info")
                    print(f"      PARAMS: {{'message': 'Funktion nicht verfügbar: {func_name}', 'title': '{item['command_key']}'}}")

if __name__ == '__main__':
    analyze_skipped_commands('Daten/mandant_001/datenbank.db')
