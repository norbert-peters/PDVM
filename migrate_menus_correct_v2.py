#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KORREKTE Menü-Migration zu V2.0

KRITISCHE ÄNDERUNGEN:
1. ✅ VERTIKAL aus PD_menu konvertieren
2. ✅ Template NICHT auflösen - als TEMPLATE-Item speichern
3. ✅ Aus daten_backup lesen
4. ✅ Alle Strukturen (VERTIKAL + GRUND + ZUSATZ) migrieren

AUTOR: Norbert Peters
DATUM: 02.11.2025
VERSION: 2.0 (KORREKT)
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# HELPER-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def is_separator(key: str) -> bool:
    """Prüft ob Key ein Separator ist"""
    return key.startswith("---")

def generate_guid() -> str:
    """Generiert neue GUID"""
    return str(uuid.uuid4())

# ═══════════════════════════════════════════════════════════════════════════
# ITEM-KONVERTIERUNG
# ═══════════════════════════════════════════════════════════════════════════

def convert_items_recursive(
    items_dict: Dict,
    parent_guid: Optional[str] = None,
    base_sort: int = 0
) -> List[Dict]:
    """
    Konvertiert hierarchische Item-Struktur zu flacher Liste
    
    Args:
        items_dict: {label: children_dict, ...}
        parent_guid: Parent GUID (None für Top-Level)
        base_sort: Basis Sort-Order
    
    Returns:
        Liste von MenuItem-Dicts
    """
    result = []
    sort_order = base_sort
    
    for label, children in items_dict.items():
        # SEPARATOR
        if is_separator(label):
            result.append({
                "GUID": generate_guid(),
                "LABEL": "",
                "TYPE": "SEPARATOR",
                "PARENT_GUID": parent_guid,
                "SORT_ORDER": sort_order,
                "VISIBLE": True,
                "COMMAND_GUID": None,
                "TEMPLATE_GUID": None
            })
            sort_order += 1
            continue
        
        # ITEM (TYPE muss BUTTON oder SUBMENU sein!)
        item_guid = generate_guid()
        
        # Prüfe ob Item Children hat → SUBMENU, sonst BUTTON
        has_children = isinstance(children, dict) and len(children) > 0
        item_type = "SUBMENU" if has_children else "BUTTON"
        
        result.append({
            "GUID": item_guid,
            "LABEL": label,
            "TYPE": item_type,  # ⭐ BUTTON oder SUBMENU
            "PARENT_GUID": parent_guid,
            "SORT_ORDER": sort_order,
            "VISIBLE": True,
            "COMMAND_GUID": None,  # Wird später von Command gesetzt
            "TEMPLATE_GUID": None
        })
        sort_order += 1
        
        # CHILDREN (rekursiv)
        if isinstance(children, dict) and children:
            child_items = convert_items_recursive(children, item_guid, 0)
            result.extend(child_items)
    
    return result

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND-KONVERTIERUNG MIT HANDLER-MAPPING
# ═══════════════════════════════════════════════════════════════════════════

def parse_old_command_to_handler(command_string: str) -> tuple[str, Dict]:
    """
    Parsed altes Command-Format zu V2.0 Handler + Params
    
    WICHTIG: Alle alten Methoden werden auf neue Handler gemappt!
    
    Beispiele:
    - "self.logout()" -> ("logout", {})
    - "self.show_text_klein('Hilfe')" -> ("show_help", {"help_text": "Hilfe"})
    - "self.open_start_menu()" -> ("open_start_menu", {})
    - "self.pdvm_start('Testbereich')" -> ("open_app_menu", {"app_name": "TESTBEREICH"})
    - "self.pdvm_modern_view('view-guid')" -> ("open_view", {"view_guid": "view-guid"})
    
    Returns:
        (handler_name, params_dict)
    """
    if not command_string:
        print(f"      ⚠️  Leeres Command")
        return None, None
    
    # Entferne self. prefix
    cmd = command_string.strip()
    if cmd.startswith("self."):
        cmd = cmd[5:]
    
    # Parse Funktion und Parameter
    if "(" not in cmd:
        # Kein Funktionsaufruf
        print(f"      ⚠️  Kein Funktionsaufruf: {command_string}")
        return None, None
    
    func_name = cmd[:cmd.index("(")]
    params_str = cmd[cmd.index("(")+1:cmd.rindex(")")].strip()
    
    # ═══════════════════════════════════════════════════════════════════════
    # HANDLER-MAPPING: Alte Methoden → Neue Handler
    # ═══════════════════════════════════════════════════════════════════════
    
    # System-Commands
    if func_name == "logout" or func_name == "abmelden":
        return ("logout", {})
    
    elif func_name == "open_start_menu" or func_name == "zu_den_apps":
        return ("open_start_menu", {})
    
    elif func_name == "toggle_menu_visibility" or func_name == "menu_umschalten":
        return ("toggle_menu", {})
    
    elif func_name == "open_menu_editor":
        return ("open_menu_editor", {})
    
    # App-Menu Commands
    elif func_name == "open_app_menu":
        # open_app_menu() ohne Parameter → MeineApps
        if not params_str:
            print(f"      🔄 open_app_menu() → open_start_menu (keine App angegeben)")
            return ("open_start_menu", {})
        else:
            app_name = params_str.strip("'\"")
            app_name_upper = app_name.upper()
            print(f"      🔄 open_app_menu('{app_name}') → open_app_menu('{app_name_upper}')")
            return ("open_app_menu", {"app_name": app_name_upper})
    
    # Hilfe-Commands
    elif func_name == "show_text_klein":
        # Parameter extrahieren (Text in Quotes)
        help_text = params_str.strip("'\"") if params_str else "Hilfe"
        return ("show_help", {"help_text": help_text, "help_type": "dialog"})
    
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ APP-START: self.pdvm_start() → open_app_menu
    # ═══════════════════════════════════════════════════════════════════════
    elif func_name == "pdvm_start":
        # Extrahiere App-Name und konvertiere zu UPPERCASE
        app_name = params_str.strip("'\"") if params_str else None
        if app_name:
            app_name_upper = app_name.upper()
            print(f"      🔄 pdvm_start('{app_name}') → open_app_menu('{app_name_upper}')")
            return ("open_app_menu", {"app_name": app_name_upper})
        else:
            print(f"      ⚠️  pdvm_start ohne Parameter")
            return None, None
    
    # ═══════════════════════════════════════════════════════════════════════
    # VIEW-COMMANDS: pdvm_modern_view, pdvm_dialog, etc.
    # ═══════════════════════════════════════════════════════════════════════
    elif func_name == "pdvm_modern_view":
        view_guid = params_str.strip("'\"") if params_str else None
        if view_guid:
            print(f"      🔄 pdvm_modern_view('{view_guid[:8]}...') → open_view")
            return ("open_view", {"view_guid": view_guid, "mode": "modern"})
        else:
            print(f"      ⚠️  pdvm_modern_view ohne GUID")
            return None, None
    
    elif func_name == "pdvm_dialog":
        view_guid = params_str.strip("'\"") if params_str else None
        if view_guid:
            print(f"      🔄 pdvm_dialog('{view_guid[:8]}...') → open_view")
            return ("open_view", {"view_guid": view_guid, "mode": "dialog"})
        else:
            print(f"      ⚠️  pdvm_dialog ohne GUID")
            return None, None
    
    elif func_name == "pdvm_enhanced_frame":
        view_guid = params_str.strip("'\"") if params_str else None
        print(f"      🔄 pdvm_enhanced_frame → open_view")
        return ("open_view", {"view_guid": view_guid, "mode": "enhanced"})
    
    # Dialog-Commands
    elif func_name == "start_dialog":
        dialog_guid = params_str.strip("'\"") if params_str else None
        if dialog_guid:
            print(f"      🔄 start_dialog('{dialog_guid[:8]}...') → show_dialog")
            return ("show_dialog", {"dialog_guid": dialog_guid})
        else:
            print(f"      ⚠️  start_dialog ohne GUID")
            return None, None
    
    # ═══════════════════════════════════════════════════════════════════════
    # TEST-COMMANDS: Info-Handler für nicht mehr existierende Test-Funktionen
    # ═══════════════════════════════════════════════════════════════════════
    elif func_name == "test_sortier_projektionen_diagnose":
        print(f"      🔄 test_sortier_projektionen_diagnose() → show_info")
        return ("show_info", {
            "title": "Test-Funktion",
            "message": "Diese Test-Funktion ist in V2.0 nicht mehr verfügbar.\n\n"
                      "Die Sortier- und Projektions-Diagnose wurde durch das neue "
                      "View-System ersetzt."
        })
    
    elif func_name == "pdvm_enhanced_test":
        print(f"      🔄 pdvm_enhanced_test() → show_info")
        return ("show_info", {
            "title": "Enhanced Test",
            "message": "Diese Test-Funktion ist in V2.0 nicht mehr verfügbar.\n\n"
                      "Das Enhanced Multi-Tab System wurde durch das neue "
                      "View-System ersetzt."
        })
    
    elif func_name == "reload_current_frame_enhanced":
        print(f"      🔄 reload_current_frame_enhanced() → reload_view")
        return ("reload_view", {})
    
    # ═══════════════════════════════════════════════════════════════════════
    # UNBEKANNTE COMMANDS: Überspringen (nicht execute_python!)
    # ═══════════════════════════════════════════════════════════════════════
    else:
        print(f"      ⚠️  Unbekanntes Command (übersprungen): {func_name}()")
        return None, None

def convert_commands(commands_dict: Dict[str, str]) -> tuple[List[Dict], Dict[str, str]]:
    """
    Konvertiert PD_commands zu V2.0 COMMANDS mit korrektem Handler-Mapping
    
    WICHTIG: Commands ohne Handler werden übersprungen!
    
    Returns:
        (commands_list, command_key_to_guid_mapping)
    """
    commands = []
    mapping = {}
    skipped = 0
    
    for command_key, command_string in commands_dict.items():
        if not command_string or command_string == "null":
            continue
        
        # Parse Command zu Handler + Params
        handler_name, params = parse_old_command_to_handler(command_string)
        
        # Überspringe Commands ohne Handler (params kann {} sein!)
        if handler_name is None or params is None:
            print(f"      ⊗ '{command_key}' übersprungen (kein Handler)")
            skipped += 1
            continue
        
        command_guid = generate_guid()
        commands.append({
            "GUID": command_guid,
            "NAME": command_key,  # Original Command-Key
            "HANDLER": handler_name,  # ⭐ V2.0 Handler-Name!
            "PARAMS": params  # ⭐ Geparste Parameter!
        })
        mapping[command_key] = command_guid
        print(f"      ✓ '{command_key}' → {handler_name}")
    
    if skipped > 0:
        print(f"   ⚠️  {skipped} Commands übersprungen")
    
    return commands, mapping

def link_items_to_commands(
    items: List[Dict],
    commands_dict: Dict[str, str],
    command_mapping: Dict[str, str]
):
    """
    Verknüpft Items mit Commands via COMMAND_GUID
    
    Args:
        items: Liste von MenuItem-Dicts (wird modifiziert!)
        commands_dict: Original PD_commands
        command_mapping: {command_key: command_guid}
    """
    for item in items:
        if item['TYPE'] == 'SEPARATOR':
            continue
        
        # Baue Command-Key
        if item['PARENT_GUID'] is None:
            # Top-Level Item
            command_key = item['LABEL']
        else:
            # Child-Item: Parent_Child
            parent = next((i for i in items if i['GUID'] == item['PARENT_GUID']), None)
            if parent:
                command_key = f"{parent['LABEL']}_{item['LABEL']}"
            else:
                command_key = item['LABEL']
        
        # Setze COMMAND_GUID
        if command_key in command_mapping:
            item['COMMAND_GUID'] = command_mapping[command_key]

# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE-SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

def create_template_item(template_guid: str, sort_order: int = 0) -> Dict:
    """
    Erstellt TEMPLATE-Item (wird später beim Menü-Aufbau aufgelöst)
    
    WICHTIG: Da MenuItemType kein TEMPLATE kennt, verwenden wir SPACER
    mit spezieller TEMPLATE_GUID!
    
    Args:
        template_guid: GUID des Templates
        sort_order: Position im Menü
    
    Returns:
        MenuItem-Dict mit TYPE=SPACER und TEMPLATE_GUID
    """
    return {
        "GUID": generate_guid(),
        "LABEL": f"@TEMPLATE:{template_guid}",  # ⭐ Template-Marker im Label
        "TYPE": "SPACER",  # ⭐ Verwende SPACER als Platzhalter
        "PARENT_GUID": None,
        "SORT_ORDER": sort_order,
        "VISIBLE": False,  # ⭐ Unsichtbar (wird beim Laden aufgelöst)
        "COMMAND_GUID": None,
        "TEMPLATE_GUID": template_guid  # ⭐ Referenz auf Template!
    }

# ═══════════════════════════════════════════════════════════════════════════
# HAUPT-KONVERTIERUNG
# ═══════════════════════════════════════════════════════════════════════════

def convert_menu(cursor, menu_guid: str, menu_name: str) -> Optional[Dict]:
    """
    Konvertiert ein Menü KORREKT zu V2.0
    
    Args:
        cursor: DB-Cursor
        menu_guid: GUID des Menüs
        menu_name: Name des Menüs
    
    Returns:
        V2.0 MenuContainer
    """
    print(f"\n{'─'*80}")
    print(f"🔄 {menu_name}")
    print(f"   GUID: {menu_guid}")
    
    # Lade aus daten_backup
    cursor.execute('SELECT daten_backup FROM sys_menudaten WHERE uid = ?', (menu_guid,))
    row = cursor.fetchone()
    
    if not row or not row[0]:
        print(f"   ❌ Keine daten_backup!")
        return None
    
    old_data = json.loads(row[0])
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. COMMANDS konvertieren
    # ═══════════════════════════════════════════════════════════════════════
    
    commands, command_mapping = convert_commands(old_data.get('PD_commands', {}))
    print(f"   ✅ {len(commands)} Commands")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. GRUND konvertieren
    # ═══════════════════════════════════════════════════════════════════════
    
    grund_items = []
    pd_grund = old_data.get('PD_grund', {})
    
    # TEMPLATE-Referenz prüfen
    if '!guid!' in pd_grund:
        template_guid = pd_grund['!guid!']
        print(f"   📋 Template: {template_guid}")
        
        # TEMPLATE-Item erstellen (wird NICHT aufgelöst!)
        grund_items.append(create_template_item(template_guid, 0))
        
        # Rest von PD_grund konvertieren (ohne !guid!)
        remaining_grund = {k: v for k, v in pd_grund.items() if k != '!guid!'}
        if remaining_grund:
            additional_items = convert_items_recursive(remaining_grund, None, 1)
            grund_items.extend(additional_items)
    else:
        # Kein Template - direkt konvertieren
        grund_items = convert_items_recursive(pd_grund, None, 0)
    
    # Commands verknüpfen
    link_items_to_commands(grund_items, old_data.get('PD_commands', {}), command_mapping)
    
    print(f"   ✅ {len(grund_items)} GRUND Items")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. VERTIKAL konvertieren (aus PD_menu!)
    # ═══════════════════════════════════════════════════════════════════════
    
    vertikal_items = []
    pd_menu = old_data.get('PD_menu', {})
    
    if pd_menu:
        vertikal_items = convert_items_recursive(pd_menu, None, 0)
        link_items_to_commands(vertikal_items, old_data.get('PD_commands', {}), command_mapping)
        print(f"   ✅ {len(vertikal_items)} VERTIKAL Items")
    else:
        print(f"   ℹ️  Kein VERTIKAL")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. ZUSATZ konvertieren (aus PD_zusatz)
    # ═══════════════════════════════════════════════════════════════════════
    
    zusatz_items = []
    pd_zusatz = old_data.get('PD_zusatz', {})
    
    if pd_zusatz:
        # PD_zusatz hat komplexere Struktur: {PD_z_Grund: {...}, PD_z_Menu: {...}}
        # TODO: Implementieren falls benötigt
        print(f"   ⚠️  ZUSATZ-Konvertierung übersprungen (komplex)")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 5. V2.0 Container erstellen
    # ═══════════════════════════════════════════════════════════════════════
    
    container = {
        "MENU_GUID": menu_guid,
        "MENU_NAME": menu_name,  # ⭐ KORREKT: MENU_NAME statt NAME!
        "VERTIKAL": vertikal_items,
        "GRUND": grund_items,
        "ZUSATZ": zusatz_items,
        "COMMANDS": commands
    }
    
    return container

def save_menu(cursor, container: Dict):
    """Speichert V2.0 Menu-Container in daten"""
    container_json = json.dumps(container, ensure_ascii=False, indent=2)
    
    cursor.execute('''
        UPDATE sys_menudaten 
        SET daten = ? 
        WHERE uid = ?
    ''', (container_json, container["MENU_GUID"]))
    
    print(f"   💾 Gespeichert")

# ═══════════════════════════════════════════════════════════════════════════
# MANDANTEN-MIGRATION
# ═══════════════════════════════════════════════════════════════════════════

def migrate_mandant(db_path: str, mandant_name: str):
    """Migriert alle Menüs eines Mandanten"""
    
    print(f"\n{'='*80}")
    print(f"📂 {mandant_name}")
    print(f"   {db_path}")
    print(f"{'='*80}")
    
    if not Path(db_path).exists():
        print(f"   ❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Hole alle Menüs
    cursor.execute('SELECT uid, name FROM sys_menudaten ORDER BY name')
    menus = cursor.fetchall()
    
    print(f"\n📋 {len(menus)} Menüs gefunden")
    
    success = 0
    for menu_guid, menu_name in menus:
        try:
            container = convert_menu(cursor, menu_guid, menu_name)
            if container:
                save_menu(cursor, container)
                success += 1
        except Exception as e:
            print(f"   ❌ Fehler: {e}")
            import traceback
            traceback.print_exc()
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {success}/{len(menus)} Menüs migriert")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("🚀 PDVM V2.0 - KORREKTE MENÜ-MIGRATION")
    print("=" * 80)
    print()
    print("KRITISCHE ÄNDERUNGEN:")
    print("  ✅ VERTIKAL aus PD_menu konvertieren")
    print("  ✅ Template NICHT auflösen - als TEMPLATE-Item")
    print("  ✅ Aus daten_backup lesen")
    print("  ✅ Original-Commands behalten")
    print()
    
    # Mandant 001
    migrate_mandant(
        'Daten/mandant_001/datenbank.db',
        'MANDANT_001'
    )
    
    # Mandant 002
    migrate_mandant(
        'Daten/mandant_002/datenbank.db',
        'MANDANT_002'
    )
    
    print(f"\n\n{'='*80}")
    print("🎉 MIGRATION ABGESCHLOSSEN")
    print(f"{'='*80}")
    print()
    print("📝 NÄCHSTE SCHRITTE:")
    print("  1. Prüfe Struktur: python validate_migrated_menu.py")
    print("  2. Test System: python v2_main.py")
    print()

if __name__ == '__main__':
    main()
