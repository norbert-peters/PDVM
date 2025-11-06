#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konvertiert alte Menü-Struktur (hierarchisch) zu V2.0 Format

Features:
- Template-Einbettung via !guid!
- Hierarchische Struktur (Parent-Child)
- Separatoren (--- und ---(X))
- Command-Mapping zu Handlers
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Tuple, Optional

# Command-Mapping: Alte Commands -> Handler-Calls
COMMAND_HANDLERS = {
    "self.show_text_klein": {"handler": "show_help", "params": {"message": None}},
    "self.logout": {"handler": "logout", "params": {}},
    "self.open_start_menu": {"handler": "open_start_menu", "params": {}},
    "self.open_app_menu": {"handler": "open_app_menu", "params": {"app_name": None}},
    "self.toggle_menu_visibility": {"handler": "toggle_menu", "params": {}},
    "self.open_menu_editor": {"handler": "open_menu_editor", "params": {}},
    "self.pdvm_modern_view": {"handler": "open_view", "params": {"view_guid": None, "mode": "modern"}},
    "self.pdvm_dialog": {"handler": "open_view", "params": {"view_guid": None, "mode": "dialog"}},
    "self.start_dialog": {"handler": "show_dialog", "params": {"dialog_guid": None}},
    "self.test_sortier_projektionen_diagnose": {"handler": "execute_python", "params": {"code": "self.test_sortier_projektionen_diagnose()"}},
    "self.pdvm_enhanced_frame": {"handler": "execute_python", "params": {"code": "self.pdvm_enhanced_frame()"}},
    "self.reload_current_frame_enhanced": {"handler": "execute_python", "params": {"code": "self.reload_current_frame_enhanced()"}},
}

def parse_command(command_str: str) -> Optional[Dict]:
    """
    Parsed altes Command-Format zu Handler-Call
    
    Beispiele:
    - "self.logout()" -> {"handler": "logout", "params": {}}
    - "self.open_app_menu('MeineApps')" -> {"handler": "open_app_menu", "params": {"app_name": "MeineApps"}}
    - "self.pdvm_modern_view('guid-123')" -> {"handler": "open_view", "params": {"view_guid": "guid-123", "mode": "modern"}}
    """
    if not command_str or command_str == "null":
        return None
    
    # Entferne self. prefix
    if command_str.startswith("self."):
        command_str = command_str[5:]
    
    # Parse Funktionsname und Parameter
    if "(" in command_str:
        func_name = command_str[:command_str.index("(")]
        params_str = command_str[command_str.index("(")+1:command_str.rindex(")")]
        
        # Suche Handler-Mapping
        handler_key = f"self.{func_name}"
        if handler_key in COMMAND_HANDLERS:
            handler_info = COMMAND_HANDLERS[handler_key].copy()
            
            # Parse Parameter
            if params_str:
                # Nimm nur ersten Parameter (für Multi-Parameter Funktionen)
                if "," in params_str:
                    param_value = params_str.split(",")[0].strip().strip("'\"")
                else:
                    # Entferne Quotes
                    param_value = params_str.strip().strip("'\"")
                
                # Setze Parameter basierend auf Handler-Typ
                if "app_name" in handler_info["params"]:
                    handler_info["params"]["app_name"] = param_value
                elif "view_guid" in handler_info["params"]:
                    handler_info["params"]["view_guid"] = param_value
                elif "dialog_guid" in handler_info["params"]:
                    handler_info["params"]["dialog_guid"] = param_value
                elif "message" in handler_info["params"]:
                    handler_info["params"]["message"] = param_value
            
            return handler_info
    
    # Fallback: execute_python
    return {
        "handler": "execute_python",
        "params": {"code": command_str}
    }

def is_separator(key: str) -> bool:
    """Prüft ob Key ein Separator ist (--- oder ---(X))"""
    return key.startswith("---")

def load_template(cursor, template_guid: str) -> Dict:
    """Lädt Template-Menü rekursiv"""
    cursor.execute('SELECT daten_backup FROM sys_menudaten WHERE uid = ?', (template_guid,))
    row = cursor.fetchone()
    if not row:
        return {}
    
    template_data = json.loads(row[0])
    
    # Wenn Template selbst Template einbettet, rekursiv laden
    if 'PD_grund' in template_data and '!guid!' in template_data['PD_grund']:
        nested_template = load_template(cursor, template_data['PD_grund']['!guid!'])
        # Merge templates
        result = nested_template.copy()
        result.update(template_data)
        return result
    
    return template_data

def convert_hierarchical_menu(cursor, menu_guid: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Konvertiert ein Menü mit hierarchischer Struktur
    
    Returns:
        (grund_items, commands)
    """
    # Lade Menü
    cursor.execute('SELECT daten_backup FROM sys_menudaten WHERE uid = ?', (menu_guid,))
    row = cursor.fetchone()
    if not row:
        return [], []
    
    data = json.loads(row[0])
    
    # Template einbetten
    if 'PD_grund' in data and '!guid!' in data['PD_grund']:
        template_guid = data['PD_grund']['!guid!']
        template = load_template(cursor, template_guid)
        
        # Merge: Template-Struktur als Basis
        if 'PD_grund' in template:
            base_grund = template['PD_grund'].copy()
            # Aktuelle Struktur (ohne !guid!) hinzufügen
            current_grund = {k: v for k, v in data['PD_grund'].items() if k != '!guid!'}
            base_grund.update(current_grund)
            data['PD_grund'] = base_grund
        
        # Commands mergen
        if 'PD_commands' in template:
            base_commands = template['PD_commands'].copy()
            if 'PD_commands' in data:
                base_commands.update(data['PD_commands'])
            data['PD_commands'] = base_commands
    
    # Konvertiere Struktur
    grund_items = []
    commands = []
    commands_dict = data.get('PD_commands', {})
    
    sort_order = 0
    
    # Parse hierarchische Struktur
    for parent_key, children in data.get('PD_grund', {}).items():
        if parent_key == '!guid!':
            continue
        
        # Parent-Item
        parent_guid = str(uuid.uuid4())
        
        if is_separator(parent_key):
            # Separator auf Top-Level
            grund_items.append({
                "GUID": parent_guid,
                "LABEL": "",
                "TYPE": "SEPARATOR",
                "PARENT_GUID": None,
                "SORT_ORDER": sort_order,
                "VISIBLE": True,
                "COMMAND_GUID": None
            })
            sort_order += 1
            continue
        
        # Parent-Command suchen
        parent_command_key = parent_key
        parent_command = commands_dict.get(parent_command_key)
        parent_command_guid = None
        
        if parent_command:
            parent_command_guid = str(uuid.uuid4())
            handler_info = parse_command(parent_command)
            if handler_info:
                commands.append({
                    "GUID": parent_command_guid,
                    "LABEL": parent_key,
                    "HANDLER": handler_info["handler"],
                    "PARAMS": json.dumps(handler_info["params"], ensure_ascii=False)
                })
        
        # Parent-Item
        grund_items.append({
            "GUID": parent_guid,
            "LABEL": parent_key,
            "TYPE": "ITEM",
            "PARENT_GUID": None,
            "SORT_ORDER": sort_order,
            "VISIBLE": True,
            "COMMAND_GUID": parent_command_guid
        })
        sort_order += 1
        
        # Children
        if isinstance(children, dict):
            child_sort = 0
            for child_key, child_value in children.items():
                if is_separator(child_key):
                    # Child-Separator
                    child_guid = str(uuid.uuid4())
                    grund_items.append({
                        "GUID": child_guid,
                        "LABEL": "",
                        "TYPE": "SEPARATOR",
                        "PARENT_GUID": parent_guid,
                        "SORT_ORDER": child_sort,
                        "VISIBLE": True,
                        "COMMAND_GUID": None
                    })
                    child_sort += 1
                    continue
                
                # Child-Command suchen
                child_command_key = f"{parent_key}_{child_key}"
                child_command = commands_dict.get(child_command_key)
                child_command_guid = None
                
                if child_command:
                    child_command_guid = str(uuid.uuid4())
                    handler_info = parse_command(child_command)
                    if handler_info:
                        commands.append({
                            "GUID": child_command_guid,
                            "LABEL": child_key,
                            "HANDLER": handler_info["handler"],
                            "PARAMS": json.dumps(handler_info["params"], ensure_ascii=False)
                        })
                
                # Child-Item
                child_guid = str(uuid.uuid4())
                grund_items.append({
                    "GUID": child_guid,
                    "LABEL": child_key,
                    "TYPE": "ITEM",
                    "PARENT_GUID": parent_guid,
                    "SORT_ORDER": child_sort,
                    "VISIBLE": True,
                    "COMMAND_GUID": child_command_guid
                })
                child_sort += 1
    
    return grund_items, commands

def save_converted_menu(cursor, menu_guid: str, grund_items: List[Dict], commands: List[Dict]):
    """Speichert konvertiertes Menü in sys_menudaten.daten"""
    
    # Hole Menü-Name aus DB
    cursor.execute('SELECT name FROM sys_menudaten WHERE uid = ?', (menu_guid,))
    row = cursor.fetchone()
    menu_name = row[0] if row else "Unbenannt"
    
    # Erstelle neues Menu-Container Format
    container = {
        "MENU_GUID": menu_guid,
        "NAME": menu_name,
        "VERTIKAL": [],  # Leer, wird später manuell gefüllt
        "GRUND": grund_items,
        "ZUSATZ": [],  # Leer, Zusatz-Menüs werden später hinzugefügt
        "COMMANDS": commands
    }
    
    # Speichere als JSON
    container_json = json.dumps(container, ensure_ascii=False, indent=2)
    
    # Update daten Spalte
    cursor.execute('''
        UPDATE sys_menudaten 
        SET daten = ? 
        WHERE uid = ?
    ''', (container_json, menu_guid))
    
    print(f"✅ Menü konvertiert: {menu_guid}")
    print(f"   - GRUND Items: {len(grund_items)}")
    print(f"   - Commands: {len(commands)}")

def main():
    """Hauptfunktion: Konvertiert alle Menüs"""
    
    conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("MENÜ-KONVERTIERUNG: Hierarchisch -> V2.0")
    print("=" * 80)
    
    # Hole alle Menüs mit Backup
    cursor.execute('SELECT uid FROM sys_menudaten WHERE daten_backup IS NOT NULL')
    menu_guids = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📋 Gefundene Menüs: {len(menu_guids)}\n")
    
    for menu_guid in menu_guids:
        print(f"\n🔄 Konvertiere: {menu_guid}")
        
        try:
            grund_items, commands = convert_hierarchical_menu(cursor, menu_guid)
            save_converted_menu(cursor, menu_guid, grund_items, commands)
        except Exception as e:
            print(f"❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
    
    # Commit
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ KONVERTIERUNG ABGESCHLOSSEN")
    print("=" * 80)

if __name__ == '__main__':
    main()
