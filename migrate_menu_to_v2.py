"""
Migriert alte Menü-Daten (Tree-basiert) zu neuer V2-Container-Struktur

ALTE STRUKTUR:
{
  "PD_commands": {"key": "command_string", ...},
  "PD_grund": {"label": {...}, ...},
  "PD_zusatz": {"PD_z_Grund": {...}, "PD_z_Menu": {...}},
  "PD_menu": {"label": {...}, ...}  // VERTIKAL
}

NEUE V2-STRUKTUR:
{
  "MENU_GUID": "...",
  "MENU_NAME": "...",
  "IS_STARTMENU": false,
  "VERTIKAL": [MenuItem, ...],
  "GRUND": [MenuItem, ...],
  "ZUSATZ": [MenuItem, ...],
  "COMMANDS": [MenuCommand, ...]
}
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Any

def generate_guid() -> str:
    """Generiert eine neue GUID"""
    return str(uuid.uuid4())

def create_menu_item(
    label: str,
    item_type: str = "BUTTON",
    command_guid: str = None,
    parent_guid: str = None,
    zusatz_guid: str = None,
    sort_order: int = 0
) -> Dict[str, Any]:
    """Erstellt ein MenuItem"""
    return {
        "GUID": generate_guid(),
        "TYPE": item_type,
        "LABEL": label,
        "SORT_ORDER": sort_order,
        "ICON": None,
        "COMMAND_GUID": command_guid,
        "ZUSATZ_GUID": zusatz_guid,
        "PARENT_GUID": parent_guid,
        "VISIBLE": True,
        "ENABLED": True,
        "TOOLTIP": None
    }

def create_command(
    name: str,
    handler: str,
    params: Dict = None,
    sec_profile_default: str = "88888888-8888-8888-8888-888888888888"
) -> Dict[str, Any]:
    """Erstellt ein MenuCommand"""
    return {
        "GUID": generate_guid(),
        "NAME": name,
        "HANDLER": handler,
        "PARAMS": params or {},
        "SEC_PROFILE_DEFAULT": sec_profile_default,
        "SEC_PROFILES": []
    }

def migrate_commands(old_commands: Dict[str, str]) -> tuple[Dict[str, str], List[Dict]]:
    """
    Migriert PD_commands zu COMMANDS Liste
    
    Returns:
        (command_mapping, commands_list)
        command_mapping: {old_key: new_guid}
        commands_list: Liste von MenuCommand Dicts
    """
    command_mapping = {}
    commands_list = []
    
    for old_key, command_string in old_commands.items():
        if command_string is None:
            # Separator - kein Command
            continue
        
        # Erstelle neuen Command
        cmd = create_command(
            name=old_key,
            handler=command_string,
            params={}
        )
        
        command_mapping[old_key] = cmd["GUID"]
        commands_list.append(cmd)
    
    return command_mapping, commands_list

def migrate_grund_menu(
    pd_grund: Dict,
    command_mapping: Dict[str, str]
) -> List[Dict]:
    """
    Migriert PD_grund zu GRUND MenuItem Liste
    
    PD_grund Struktur:
    {
        "!guid!": "basis-menu-guid",
        "Label1": {...submenu...},
        "Label2": {...submenu...}
    }
    """
    grund_items = []
    sort_order = 0
    
    for key, value in pd_grund.items():
        if key == "!guid!":
            # Basis-Menü GUID - überspringen (wird separat behandelt)
            continue
        
        if isinstance(value, dict):
            # Submenu mit Unterpunkten
            submenu_guid = generate_guid()
            submenu_item = create_menu_item(
                label=key,
                item_type="SUBMENU",
                zusatz_guid=submenu_guid,
                sort_order=sort_order
            )
            grund_items.append(submenu_item)
            
            # Unterpunkte als eigene Items mit PARENT_GUID
            sub_sort = 0
            for sub_key, sub_value in value.items():
                if sub_key == "---":
                    # Separator
                    sep = create_menu_item(
                        label="---",
                        item_type="SEPARATOR",
                        parent_guid=submenu_item["GUID"],
                        sort_order=sub_sort
                    )
                    grund_items.append(sep)
                else:
                    # Button
                    command_key = f"{key}_{sub_key}"
                    command_guid = command_mapping.get(command_key)
                    
                    sub_item = create_menu_item(
                        label=sub_key,
                        item_type="BUTTON",
                        command_guid=command_guid,
                        parent_guid=submenu_item["GUID"],
                        sort_order=sub_sort
                    )
                    grund_items.append(sub_item)
                
                sub_sort += 1
        else:
            # Einfacher Button
            command_guid = command_mapping.get(key)
            item = create_menu_item(
                label=key,
                item_type="BUTTON",
                command_guid=command_guid,
                sort_order=sort_order
            )
            grund_items.append(item)
        
        sort_order += 1
    
    return grund_items

def migrate_vertical_menu(
    pd_menu: Dict,
    command_mapping: Dict[str, str]
) -> List[Dict]:
    """
    Migriert PD_menu zu VERTIKAL MenuItem Liste
    
    PD_menu Struktur ähnlich wie PD_grund
    """
    # Gleiche Logik wie GRUND
    return migrate_grund_menu(pd_menu, command_mapping)

def migrate_zusatz_menu(
    pd_zusatz: Dict,
    command_mapping: Dict[str, str]
) -> List[Dict]:
    """
    Migriert PD_zusatz zu ZUSATZ MenuItem Liste
    
    PD_zusatz Struktur:
    {
        "PD_z_Grund": {parent_guid: {label: command_key, ...}},
        "PD_z_Menu": {parent_guid: {label: command_key, ...}}
    }
    """
    zusatz_items = []
    sort_order = 0
    
    # PD_z_Grund: Zusatzmenüs für GRUND-Items
    if "PD_z_Grund" in pd_zusatz:
        for parent_key, items in pd_zusatz["PD_z_Grund"].items():
            # parent_key ist die GUID des Parent-Items
            for label, command_key in items.items():
                if command_key == "---":
                    # Separator
                    sep = create_menu_item(
                        label="---",
                        item_type="SEPARATOR",
                        parent_guid=parent_key,
                        sort_order=sort_order
                    )
                    zusatz_items.append(sep)
                else:
                    command_guid = command_mapping.get(command_key)
                    item = create_menu_item(
                        label=label,
                        item_type="BUTTON",
                        command_guid=command_guid,
                        parent_guid=parent_key,
                        sort_order=sort_order
                    )
                    zusatz_items.append(item)
                sort_order += 1
    
    # PD_z_Menu: Zusatzmenüs für VERTIKAL-Items
    if "PD_z_Menu" in pd_zusatz:
        for parent_key, items in pd_zusatz["PD_z_Menu"].items():
            for label, command_key in items.items():
                if command_key == "---":
                    sep = create_menu_item(
                        label="---",
                        item_type="SEPARATOR",
                        parent_guid=parent_key,
                        sort_order=sort_order
                    )
                    zusatz_items.append(sep)
                else:
                    command_guid = command_mapping.get(command_key)
                    item = create_menu_item(
                        label=label,
                        item_type="BUTTON",
                        command_guid=command_guid,
                        parent_guid=parent_key,
                        sort_order=sort_order
                    )
                    zusatz_items.append(item)
                sort_order += 1
    
    return zusatz_items

def migrate_single_menu(
    uid: str,
    name: str,
    old_data: Dict
) -> Dict:
    """
    Migriert ein einzelnes Menü von alter zu neuer Struktur
    
    Returns:
        V2 MenuContainer Dict
    """
    print(f"\n{'─'*80}")
    print(f"🔄 Migriere: {name} ({uid})")
    
    # 1. Commands migrieren
    command_mapping, commands = migrate_commands(old_data.get("PD_commands", {}))
    print(f"   ✅ {len(commands)} Commands migriert")
    
    # 2. GRUND migrieren
    grund_items = migrate_grund_menu(
        old_data.get("PD_grund", {}),
        command_mapping
    )
    print(f"   ✅ {len(grund_items)} GRUND Items migriert")
    
    # 3. VERTIKAL migrieren
    vertikal_items = migrate_vertical_menu(
        old_data.get("PD_menu", {}),
        command_mapping
    )
    print(f"   ✅ {len(vertikal_items)} VERTIKAL Items migriert")
    
    # 4. ZUSATZ migrieren
    zusatz_items = migrate_zusatz_menu(
        old_data.get("PD_zusatz", {}),
        command_mapping
    )
    print(f"   ✅ {len(zusatz_items)} ZUSATZ Items migriert")
    
    # 5. V2 Container erstellen
    v2_container = {
        "MENU_GUID": uid,  # Behalte alte UID
        "MENU_NAME": name,  # Behalte alten Namen
        "IS_STARTMENU": "Startmenü" in name or "Start" in name,
        "VERTIKAL": vertikal_items,
        "GRUND": grund_items,
        "ZUSATZ": zusatz_items,
        "COMMANDS": commands
    }
    
    return v2_container

def migrate_database(db_path: str, backup: bool = True):
    """
    Migriert alle Menüs in einer Datenbank
    
    Args:
        db_path: Pfad zur Datenbank
        backup: Wenn True, erstelle Backup-Spalte mit alten Daten
    """
    print(f"\n{'='*80}")
    print(f"📂 Migriere Datenbank: {db_path}")
    print(f"{'='*80}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Optional: Backup-Spalte erstellen
    if backup:
        try:
            cursor.execute("ALTER TABLE sys_menudaten ADD COLUMN daten_backup TEXT")
            print("✅ Backup-Spalte 'daten_backup' erstellt")
        except sqlite3.OperationalError:
            print("ℹ️  Backup-Spalte existiert bereits")
    
    # Alle Menüs laden
    cursor.execute("SELECT uid, name, daten FROM sys_menudaten")
    rows = cursor.fetchall()
    
    print(f"\n📊 Gefunden: {len(rows)} Menüs")
    
    migrated_count = 0
    for uid, name, daten_json in rows:
        try:
            # Parse alte Daten
            old_data = json.loads(daten_json)
            
            # Backup erstellen
            if backup:
                cursor.execute(
                    "UPDATE sys_menudaten SET daten_backup = ? WHERE uid = ?",
                    (daten_json, uid)
                )
            
            # Migrieren
            v2_container = migrate_single_menu(uid, name, old_data)
            
            # Speichern
            v2_json = json.dumps(v2_container, ensure_ascii=False, indent=2)
            cursor.execute(
                "UPDATE sys_menudaten SET daten = ? WHERE uid = ?",
                (v2_json, uid)
            )
            
            migrated_count += 1
            print(f"   💾 Gespeichert")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {name}: {e}")
            import traceback
            traceback.print_exc()
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration abgeschlossen: {migrated_count}/{len(rows)} Menüs migriert")

def main():
    """Hauptfunktion"""
    print("🚀 PDVM Menü-Migration V2")
    print("="*80)
    print("Migriert alte Tree-basierte Menüs zu neuer Container-Struktur")
    print()
    
    # Mandant 001
    migrate_database("Daten/mandant_001/datenbank.db", backup=True)
    
    # Mandant 002
    migrate_database("Daten/mandant_002/datenbank.db", backup=True)
    
    print(f"\n\n{'='*80}")
    print("🎉 MIGRATION ERFOLGREICH ABGESCHLOSSEN")
    print(f"{'='*80}")
    print()
    print("📝 HINWEISE:")
    print("  • Alte Daten wurden in 'daten_backup' gesichert")
    print("  • UIDs und Namen wurden beibehalten")
    print("  • Neue V2-Struktur in 'daten' gespeichert")
    print()
    print("🔍 NÄCHSTE SCHRITTE:")
    print("  1. Test mit: python v2_main.py")
    print("  2. Prüfe Menü-Darstellung im System")
    print("  3. Bei Erfolg: Backup-Spalte kann gelöscht werden")
    print()

if __name__ == "__main__":
    main()
