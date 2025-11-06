#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strukturierte Konvertierung der 7 Menüs zu V2.0 Format

KRITISCH:
- Template-Einbettung via !guid! berücksichtigen
- Hierarchische Struktur (Parent-Child) korrekt aufbauen
- Command-Mapping zu V2.0 Handlers
- Mandantenübergreifend (beide mandant_001 + mandant_002)

Die 7 Menüs:
1. Admin-Administration (4cfbf1ac-c7db-4a3a-ab37-c5b457b89440)
2. Admin-Benutzermenü (e1e77039-d1b5-46ff-b12b-cced0ae0da7c)
3. Admin-Menü (3424b00f-bb4d-4759-9689-e9e08249117b)
4. Admin-Startmenü (5ca6674e-b9ce-4581-9756-64e742883f80)
5. Admin-Testmenü (113c6a2c-af9a-4022-929b-6544799e8954)
6. Basis-Menü (1a653694-3132-48d9-bc3e-a512962ae8e6) ⭐ TEMPLATE
7. Default-Struktur (00000000-0000-0000-0000-000000000000)

AUTOR: Norbert Peters
DATUM: 02.11.2025
VERSION: 1.0
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND-MAPPING: Alte Commands -> V2.0 Handlers
# ═══════════════════════════════════════════════════════════════════════════

COMMAND_HANDLERS = {
    # System-Commands
    "self.logout": {"handler": "logout", "params": {}},
    "self.open_start_menu": {"handler": "open_start_menu", "params": {}},
    "self.toggle_menu_visibility": {"handler": "toggle_menu", "params": {}},
    "self.open_menu_editor": {"handler": "open_menu_editor", "params": {}},
    
    # View-Commands
    "self.pdvm_modern_view": {"handler": "open_view", "params": {"view_guid": None, "mode": "modern"}},
    "self.pdvm_dialog": {"handler": "open_view", "params": {"view_guid": None, "mode": "dialog"}},
    "self.pdvm_enhanced_frame": {"handler": "open_view", "params": {"view_guid": None, "mode": "enhanced"}},
    
    # App-Commands
    "self.open_app_menu": {"handler": "open_app_menu", "params": {"app_name": None}},
    
    # Dialog-Commands
    "self.start_dialog": {"handler": "show_dialog", "params": {"dialog_guid": None}},
    
    # Help-Commands
    "self.show_text_klein": {"handler": "show_help", "params": {"message": None}},
    
    # Test/Debug-Commands
    "self.test_sortier_projektionen_diagnose": {
        "handler": "execute_python", 
        "params": {"code": "self.test_sortier_projektionen_diagnose()"}
    },
    "self.reload_current_frame_enhanced": {
        "handler": "execute_python",
        "params": {"code": "self.reload_current_frame_enhanced()"}
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# HELPER-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def is_separator(key: str) -> bool:
    """Prüft ob Key ein Separator ist (--- oder ---(X))"""
    return key.startswith("---")

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
        "params": {"code": f"self.{command_str}" if not command_str.startswith("self.") else command_str}
    }

# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE-SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

def load_template_recursive(cursor, template_guid: str, visited: set = None) -> Dict:
    """
    Lädt Template-Menü rekursiv (verhindert Loops)
    
    Args:
        cursor: DB-Cursor
        template_guid: GUID des Templates
        visited: Set von bereits besuchten GUIDs (Loop-Prevention)
    
    Returns:
        Merged Template-Daten
    """
    if visited is None:
        visited = set()
    
    # Loop-Prevention
    if template_guid in visited:
        print(f"   ⚠️ Template-Loop erkannt: {template_guid}")
        return {}
    
    visited.add(template_guid)
    
    # Lade Template aus daten_backup
    cursor.execute('SELECT daten_backup FROM sys_menudaten WHERE uid = ?', (template_guid,))
    row = cursor.fetchone()
    if not row or not row[0]:
        print(f"   ⚠️ Template nicht gefunden: {template_guid}")
        return {}
    
    template_data = json.loads(row[0])
    
    # Wenn Template selbst Template einbettet, rekursiv laden
    if 'PD_grund' in template_data and '!guid!' in template_data['PD_grund']:
        nested_template_guid = template_data['PD_grund']['!guid!']
        print(f"   🔗 Template-Verschachtelung: {template_guid} -> {nested_template_guid}")
        
        nested_template = load_template_recursive(cursor, nested_template_guid, visited)
        
        # Merge: Nested Template als Basis, aktuelles Template darüber
        result = nested_template.copy()
        
        # PD_grund mergen (ohne !guid!)
        if 'PD_grund' in result:
            result_grund = result['PD_grund'].copy()
            current_grund = {k: v for k, v in template_data['PD_grund'].items() if k != '!guid!'}
            result_grund.update(current_grund)
            result['PD_grund'] = result_grund
        
        # PD_commands mergen
        if 'PD_commands' in result and 'PD_commands' in template_data:
            result['PD_commands'].update(template_data['PD_commands'])
        elif 'PD_commands' in template_data:
            result['PD_commands'] = template_data['PD_commands']
        
        # PD_menu mergen
        if 'PD_menu' in result and 'PD_menu' in template_data:
            result['PD_menu'].update(template_data['PD_menu'])
        elif 'PD_menu' in template_data:
            result['PD_menu'] = template_data['PD_menu']
        
        return result
    
    return template_data

def merge_with_template(cursor, menu_data: Dict) -> Dict:
    """
    Merged Menü-Daten mit Template (falls !guid! vorhanden)
    
    Args:
        cursor: DB-Cursor
        menu_data: Aktuelle Menü-Daten
    
    Returns:
        Gemergtes Menü
    """
    if 'PD_grund' not in menu_data or '!guid!' not in menu_data['PD_grund']:
        # Kein Template
        return menu_data
    
    template_guid = menu_data['PD_grund']['!guid!']
    print(f"   📋 Lade Template: {template_guid}")
    
    # Template laden
    template = load_template_recursive(cursor, template_guid)
    
    # Merge: Template als Basis
    result = template.copy()
    
    # PD_grund mergen (ohne !guid!)
    if 'PD_grund' in result:
        result_grund = result['PD_grund'].copy()
        current_grund = {k: v for k, v in menu_data['PD_grund'].items() if k != '!guid!'}
        result_grund.update(current_grund)
        result['PD_grund'] = result_grund
    else:
        result['PD_grund'] = {k: v for k, v in menu_data['PD_grund'].items() if k != '!guid!'}
    
    # PD_commands mergen
    if 'PD_commands' in result and 'PD_commands' in menu_data:
        result['PD_commands'].update(menu_data['PD_commands'])
    elif 'PD_commands' in menu_data:
        result['PD_commands'] = menu_data['PD_commands']
    
    # PD_menu mergen
    if 'PD_menu' in result and 'PD_menu' in menu_data:
        result['PD_menu'].update(menu_data['PD_menu'])
    elif 'PD_menu' in menu_data:
        result['PD_menu'] = menu_data['PD_menu']
    
    return result

# ═══════════════════════════════════════════════════════════════════════════
# KONVERTIERUNGS-LOGIK
# ═══════════════════════════════════════════════════════════════════════════

def convert_commands(commands_dict: Dict[str, str]) -> List[Dict]:
    """
    Konvertiert PD_commands zu V2.0 COMMANDS Liste
    
    Args:
        commands_dict: {command_key: command_string, ...}
    
    Returns:
        Liste von Command-Dicts
    """
    commands = []
    
    for command_key, command_string in commands_dict.items():
        if not command_string or command_string == "null":
            continue
        
        handler_info = parse_command(command_string)
        if not handler_info:
            continue
        
        command_guid = str(uuid.uuid4())
        commands.append({
            "GUID": command_guid,
            "LABEL": command_key,
            "HANDLER": handler_info["handler"],
            "PARAMS": json.dumps(handler_info["params"], ensure_ascii=False)
        })
    
    return commands

def convert_grund_hierarchical(
    pd_grund: Dict, 
    commands_dict: Dict[str, str]
) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Konvertiert PD_grund hierarchisch zu V2.0 GRUND Liste
    
    Args:
        pd_grund: Hierarchische Struktur {parent: {child: {}, ...}, ...}
        commands_dict: {command_key: command_string, ...}
    
    Returns:
        (grund_items, command_guid_mapping)
        command_guid_mapping: {command_key: command_guid}
    """
    grund_items = []
    command_guid_mapping = {}
    sort_order = 0
    
    for parent_key, children in pd_grund.items():
        if parent_key == '!guid!':
            continue
        
        # SEPARATOR auf Top-Level
        if is_separator(parent_key):
            grund_items.append({
                "GUID": str(uuid.uuid4()),
                "LABEL": "",
                "TYPE": "SEPARATOR",
                "PARENT_GUID": None,
                "SORT_ORDER": sort_order,
                "VISIBLE": True,
                "COMMAND_GUID": None
            })
            sort_order += 1
            continue
        
        # Parent-Item
        parent_guid = str(uuid.uuid4())
        parent_command_key = parent_key
        parent_command_guid = None
        
        # Prüfe ob Parent selbst einen Command hat
        if parent_command_key in commands_dict:
            parent_command_guid = str(uuid.uuid4())
            command_guid_mapping[parent_command_key] = parent_command_guid
        
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
            for child_key, _ in children.items():
                # SEPARATOR als Child
                if is_separator(child_key):
                    grund_items.append({
                        "GUID": str(uuid.uuid4()),
                        "LABEL": "",
                        "TYPE": "SEPARATOR",
                        "PARENT_GUID": parent_guid,
                        "SORT_ORDER": child_sort,
                        "VISIBLE": True,
                        "COMMAND_GUID": None
                    })
                    child_sort += 1
                    continue
                
                # Child-Item
                child_command_key = f"{parent_key}_{child_key}"
                child_command_guid = None
                
                if child_command_key in commands_dict:
                    child_command_guid = str(uuid.uuid4())
                    command_guid_mapping[child_command_key] = child_command_guid
                
                grund_items.append({
                    "GUID": str(uuid.uuid4()),
                    "LABEL": child_key,
                    "TYPE": "ITEM",
                    "PARENT_GUID": parent_guid,
                    "SORT_ORDER": child_sort,
                    "VISIBLE": True,
                    "COMMAND_GUID": child_command_guid
                })
                child_sort += 1
    
    return grund_items, command_guid_mapping

def convert_menu(cursor, menu_guid: str, menu_name: str) -> Optional[Dict]:
    """
    Konvertiert ein einzelnes Menü zu V2.0 Format
    
    Args:
        cursor: DB-Cursor
        menu_guid: GUID des Menüs
        menu_name: Name des Menüs
    
    Returns:
        V2.0 Menu-Container oder None bei Fehler
    """
    print(f"\n{'─'*80}")
    print(f"🔄 Konvertiere: {menu_name}")
    print(f"   GUID: {menu_guid}")
    
    # Lade alte Struktur aus daten_backup
    cursor.execute('SELECT daten_backup FROM sys_menudaten WHERE uid = ?', (menu_guid,))
    row = cursor.fetchone()
    
    if not row or not row[0]:
        print(f"   ❌ Keine daten_backup gefunden!")
        return None
    
    old_data = json.loads(row[0])
    
    # Template-Merge (falls !guid! vorhanden)
    merged_data = merge_with_template(cursor, old_data)
    
    # Konvertiere Commands
    commands_dict = merged_data.get('PD_commands', {})
    grund_items, command_guid_mapping = convert_grund_hierarchical(
        merged_data.get('PD_grund', {}),
        commands_dict
    )
    
    print(f"   ✅ {len(grund_items)} GRUND Items konvertiert")
    
    # Erstelle Commands mit korrekten GUIDs
    commands = []
    for command_key, command_string in commands_dict.items():
        if not command_string or command_string == "null":
            continue
        
        # Nutze vorher gemappte GUID (falls vorhanden)
        if command_key in command_guid_mapping:
            command_guid = command_guid_mapping[command_key]
        else:
            command_guid = str(uuid.uuid4())
        
        handler_info = parse_command(command_string)
        if not handler_info:
            continue
        
        commands.append({
            "GUID": command_guid,
            "LABEL": command_key,
            "HANDLER": handler_info["handler"],
            "PARAMS": json.dumps(handler_info["params"], ensure_ascii=False)
        })
    
    print(f"   ✅ {len(commands)} Commands konvertiert")
    
    # V2.0 Container erstellen
    container = {
        "MENU_GUID": menu_guid,
        "NAME": menu_name,
        "VERTIKAL": [],  # Wird später manuell gefüllt
        "GRUND": grund_items,
        "ZUSATZ": [],  # Wird später manuell gefüllt
        "COMMANDS": commands
    }
    
    return container

def save_converted_menu(cursor, container: Dict):
    """
    Speichert konvertiertes Menü in sys_menudaten.daten
    
    Args:
        cursor: DB-Cursor
        container: V2.0 Menu-Container
    """
    container_json = json.dumps(container, ensure_ascii=False, indent=2)
    
    cursor.execute('''
        UPDATE sys_menudaten 
        SET daten = ? 
        WHERE uid = ?
    ''', (container_json, container["MENU_GUID"]))
    
    print(f"   💾 Gespeichert in daten-Spalte")

# ═══════════════════════════════════════════════════════════════════════════
# HAUPT-KONVERTIERUNG
# ═══════════════════════════════════════════════════════════════════════════

def convert_mandant_menus(db_path: str, mandant_name: str):
    """
    Konvertiert alle Menüs in einer Mandanten-DB
    
    Args:
        db_path: Pfad zur Datenbank
        mandant_name: Name des Mandanten (für Logging)
    """
    print(f"\n{'='*80}")
    print(f"📂 Mandant: {mandant_name}")
    print(f"   DB: {db_path}")
    print(f"{'='*80}")
    
    if not Path(db_path).exists():
        print(f"   ❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Hole alle Menüs
    cursor.execute('SELECT uid, name FROM sys_menudaten ORDER BY name')
    menus = cursor.fetchall()
    
    print(f"\n📋 Gefundene Menüs: {len(menus)}")
    
    success_count = 0
    for menu_guid, menu_name in menus:
        try:
            container = convert_menu(cursor, menu_guid, menu_name)
            if container:
                save_converted_menu(cursor, container)
                success_count += 1
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
    
    # Commit
    conn.commit()
    conn.close()
    
    print(f"\n✅ {success_count}/{len(menus)} Menüs erfolgreich konvertiert")

def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("🚀 PDVM V2.0 - STRUKTURIERTE MENÜ-KONVERTIERUNG")
    print("=" * 80)
    print()
    print("FEATURES:")
    print("  ✅ Template-Einbettung via !guid!")
    print("  ✅ Hierarchische Struktur (Parent-Child)")
    print("  ✅ Command-Mapping zu V2.0 Handlers")
    print("  ✅ Mandantenübergreifend")
    print()
    
    # Mandant 001
    convert_mandant_menus(
        'Daten/mandant_001/datenbank.db',
        'MANDANT_001'
    )
    
    # Mandant 002
    convert_mandant_menus(
        'Daten/mandant_002/datenbank.db',
        'MANDANT_002'
    )
    
    print(f"\n\n{'='*80}")
    print("🎉 KONVERTIERUNG ABGESCHLOSSEN")
    print(f"{'='*80}")
    print()
    print("📝 NÄCHSTE SCHRITTE:")
    print("  1. Test mit: python v2_main.py")
    print("  2. Login als admin@pdvm.de / admin")
    print("  3. Prüfe Menü-Darstellung im System")
    print()

if __name__ == '__main__':
    main()
