"""
Migration: sys_menudaten Controls nach Standard-Pattern umstrukturieren

PROBLEM:
- Controls sind als Unter-Properties eines einzigen Controls verschachtelt
- Key "bc9f35c4-..." enthält alle Feld-Definitionen als Unter-Objekte

LÖSUNG:
- Jedes Control bekommt eigene GUID als Key
- Jedes Control hat: name, label, type, control_type, etc.
- Standard-Pattern wie bei anderen Tabellen
"""

import sqlite3
import json
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Datenbank-Pfad
DB_PATH = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"

# GUID des sys_menudaten Framedaten-Datensatzes
FRAME_GUID = "794cbfc3-ccb6-4681-b432-efa9f44682c8"

# Neue Control-Definitionen mit EINDEUTIGEN GUIDs
NEW_CONTROLS = {
    str(uuid.uuid4()): {
        "name": "guid",
        "label": "GUID",
        "type": "string",
        "control_type": "text",
        "readonly": True,
        "auto_generate": True,
        "visible": False,
        "display_order": 0,
        "required": False,
        "default": "",
        "table": "menu",
        "gruppe": "item",
        "feld": "guid"
    },
    str(uuid.uuid4()): {
        "name": "label",
        "label": "Beschriftung",
        "type": "string",
        "control_type": "text",
        "readonly": False,
        "visible": True,
        "display_order": 1,
        "required": True,
        "default": "Neuer Menüpunkt",
        "placeholder": "z.B. Personen",
        "max_length": 50,
        "validation": "not_empty",
        "table": "menu",
        "gruppe": "item",
        "feld": "label"
    },
    str(uuid.uuid4()): {
        "name": "type",
        "label": "Typ",
        "type": "string",
        "control_type": "dropdown",
        "readonly": False,
        "visible": True,
        "display_order": 2,
        "required": True,
        "default": "BUTTON",
        "dropdown": {
            "BUTTON": "Button (Aktion)",
            "SUBMENU": "Untermenü",
            "SEPARATOR": "Trennlinie",
            "SPACER": "Abstand"
        },
        "table": "menu",
        "gruppe": "item",
        "feld": "type"
    },
    str(uuid.uuid4()): {
        "name": "icon",
        "label": "Icon",
        "type": "string",
        "control_type": "text",
        "readonly": False,
        "visible": True,
        "display_order": 3,
        "required": False,
        "default": "",
        "placeholder": "Icon-Name oder Pfad",
        "table": "menu",
        "gruppe": "item",
        "feld": "icon"
    },
    str(uuid.uuid4()): {
        "name": "command_guid",
        "label": "Command",
        "type": "string",
        "control_type": "text",
        "readonly": False,
        "visible": True,
        "display_order": 4,
        "required": False,
        "default": "",
        "condition": "type == 'BUTTON'",
        "placeholder": "Command-GUID",
        "table": "menu",
        "gruppe": "item",
        "feld": "command_guid"
    },
    str(uuid.uuid4()): {
        "name": "zusatz_guid",
        "label": "Zusatzmenü",
        "type": "string",
        "control_type": "text",
        "readonly": False,
        "visible": True,
        "display_order": 5,
        "required": False,
        "default": "",
        "condition": "type == 'SUBMENU'",
        "placeholder": "Zusatzmenü-GUID",
        "table": "menu",
        "gruppe": "item",
        "feld": "zusatz_guid"
    },
    str(uuid.uuid4()): {
        "name": "sort_order",
        "label": "Reihenfolge",
        "type": "number",
        "control_type": "number",
        "readonly": False,
        "visible": True,
        "display_order": 6,
        "required": True,
        "default": 0,
        "auto_calculate": True,
        "min": 0,
        "max": 9999,
        "table": "menu",
        "gruppe": "item",
        "feld": "sort_order"
    },
    str(uuid.uuid4()): {
        "name": "visible",
        "label": "Sichtbar",
        "type": "boolean",
        "control_type": "checkbox",
        "readonly": False,
        "visible": True,
        "display_order": 7,
        "required": False,
        "default": True,
        "table": "menu",
        "gruppe": "item",
        "feld": "visible"
    },
    str(uuid.uuid4()): {
        "name": "enabled",
        "label": "Aktiviert",
        "type": "boolean",
        "control_type": "checkbox",
        "readonly": False,
        "visible": True,
        "display_order": 8,
        "required": False,
        "default": True,
        "table": "menu",
        "gruppe": "item",
        "feld": "enabled"
    },
    str(uuid.uuid4()): {
        "name": "tooltip",
        "label": "Tooltip",
        "type": "string",
        "control_type": "text",
        "readonly": False,
        "visible": True,
        "display_order": 9,
        "required": False,
        "default": "",
        "placeholder": "Hilfetext beim Hover...",
        "max_length": 200,
        "table": "menu",
        "gruppe": "item",
        "feld": "tooltip"
    }
}


def migrate_sys_menudaten_controls():
    """Migriert sys_menudaten Controls nach Standard-Pattern"""
    
    logger.info("="*80)
    logger.info("🔧 MIGRATION: sys_menudaten Controls → Standard-Pattern")
    logger.info("="*80)
    
    # Datenbank öffnen
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Datensatz laden
        cursor.execute(
            "SELECT daten FROM sys_framedaten WHERE uid = ?",
            (FRAME_GUID,)
        )
        row = cursor.fetchone()
        
        if not row:
            logger.error(f"❌ Datensatz nicht gefunden: {FRAME_GUID}")
            return
        
        # JSON parsen
        data = json.loads(row[0])
        
        logger.info(f"✅ Datensatz geladen: {FRAME_GUID}")
        logger.info(f"📋 ROOT_TABLE: {data.get('ROOT', {}).get('ROOT_TABLE')}")
        
        # Alte Struktur prüfen
        old_controls = data.get('METADATEN', {}).get('SYS_MENUDATEN', {}).get('controls', {})
        logger.info(f"📂 Alte Controls: {len(old_controls)} Einträge")
        for key in old_controls.keys():
            logger.info(f"   - {key}")
        
        # Neue Struktur setzen
        if 'METADATEN' not in data:
            data['METADATEN'] = {}
        if 'SYS_MENUDATEN' not in data['METADATEN']:
            data['METADATEN']['SYS_MENUDATEN'] = {}
        
        data['METADATEN']['SYS_MENUDATEN']['controls'] = NEW_CONTROLS
        
        logger.info(f"✅ Neue Controls erstellt: {len(NEW_CONTROLS)} Einträge")
        for guid, control in NEW_CONTROLS.items():
            logger.info(f"   - {guid}: {control['name']} ({control['label']})")
        
        # Zurückschreiben
        cursor.execute(
            "UPDATE sys_framedaten SET daten = ? WHERE uid = ?",
            (json.dumps(data, ensure_ascii=False, indent=2), FRAME_GUID)
        )
        
        conn.commit()
        logger.info("💾 Datenbank aktualisiert")
        
        logger.info("="*80)
        logger.info("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    migrate_sys_menudaten_controls()
