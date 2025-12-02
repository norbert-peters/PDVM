"""
View-Templates erstellen - Template-GUID für View-Controls

Erstellt Template-Datensatz in sys_viewdaten mit GUID 55555555-5555-5555-5555-555555555555

VERWENDUNG:
    python create_view_templates.py

Autor: PDVM-System
Datum: 19.11.2025
"""

import logging
import sqlite3
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


TEMPLATE_GUID = '55555555-5555-5555-5555-555555555555'

# View-Control-Templates
VIEW_TEMPLATES = {
    "view_text": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "label": "",
        "tooltip": "",
        "control_type": "text",
        "width": 150,
        "visible": True,
        "sortable": True,
        "filterable": True,
        "editable": False,
        "alignment": "left",
        "display_order": 0
    },
    "view_number": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "label": "",
        "tooltip": "",
        "control_type": "number",
        "width": 100,
        "visible": True,
        "sortable": True,
        "filterable": True,
        "editable": False,
        "alignment": "right",
        "decimal_places": 2,
        "display_order": 0
    },
    "view_date": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "label": "",
        "tooltip": "",
        "control_type": "date",
        "width": 120,
        "visible": True,
        "sortable": True,
        "filterable": True,
        "editable": False,
        "alignment": "center",
        "date_format": "dd.MM.yyyy",
        "display_order": 0
    },
    "view_dropdown": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "label": "",
        "tooltip": "",
        "control_type": "dropdown",
        "width": 150,
        "visible": True,
        "sortable": True,
        "filterable": True,
        "editable": False,
        "alignment": "left",
        "dropdown_config": {
            "table": "dropdowndaten",
            "key": "",
            "value": ""
        },
        "display_order": 0
    },
    "view_checkbox": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "label": "",
        "tooltip": "",
        "control_type": "checkbox",
        "width": 80,
        "visible": True,
        "sortable": True,
        "filterable": True,
        "editable": False,
        "alignment": "center",
        "display_order": 0
    }
}

# ROOT_CONTROLS für View-Editor als DICTIONARY (LINEAR!)
ROOT_CONTROLS = {
    "VIEW_NAME": {
        "label": "View-Name",
        "control_type": "text",
        "readonly": False,
        "display_order": 0,
        "muss": True,
        "default_value": ""
    },
    "VIEW_TABLE": {
        "label": "Basis-Tabelle",
        "control_type": "text",
        "readonly": False,
        "display_order": 1,
        "muss": True,
        "default_value": ""
    },
    "VIEW_GUID": {
        "label": "View-GUID",
        "control_type": "text",
        "readonly": True,
        "display_order": 2,
        "muss": False,
        "default_value": ""
    },
    "HEADER_TEXT": {
        "label": "Kopfzeile",
        "control_type": "text",
        "readonly": False,
        "display_order": 3,
        "muss": False,
        "default_value": ""
    },
    "NO_DATA": {
        "label": "Nur Metadaten (keine Daten)",
        "control_type": "checkbox",
        "readonly": False,
        "display_order": 4,
        "muss": False,
        "default_value": False
    },
    "PROJECTION_MODE": {
        "label": "Projektionsmodus",
        "control_type": "combo",
        "readonly": False,
        "display_order": 5,
        "muss": False,
        "default_value": "standard",
        "options": ["standard", "expert"]
    },
    "ALLOW_FILTER": {
        "label": "Filter erlauben",
        "control_type": "checkbox",
        "readonly": False,
        "display_order": 6,
        "muss": False,
        "default_value": True
    },
    "ALLOW_SORT": {
        "label": "Sortierung erlauben",
        "control_type": "checkbox",
        "readonly": False,
        "display_order": 7,
        "muss": False,
        "default_value": True
    },
    "DEFAULT_SORT_COLUMN": {
        "label": "Standard-Sortier-Spalte",
        "control_type": "text",
        "readonly": False,
        "display_order": 8,
        "muss": False,
        "default_value": ""
    },
    "DEFAULT_SORT_REVERSE": {
        "label": "Standard-Sortierung absteigend",
        "control_type": "checkbox",
        "readonly": False,
        "display_order": 9,
        "muss": False,
        "default_value": False
    }
}

# CONTROL_PROPERTIES für View-Controls als DICTIONARY (LINEAR!)
CONTROL_PROPERTIES = {
    "table": {
        "label": "Tabelle",
        "control_type": "text",
        "display_order": 0
    },
    "gruppe": {
        "label": "Gruppe",
        "control_type": "text",
        "display_order": 1
    },
    "feld": {
        "label": "Feld",
        "control_type": "text",
        "display_order": 2
    },
    "label": {
        "label": "Spalten-Label",
        "control_type": "text",
        "display_order": 3
    },
    "tooltip": {
        "label": "Tooltip",
        "control_type": "text",
        "display_order": 4
    },
    "control_type": {
        "label": "Typ",
        "control_type": "dropdown",
        "options": ["text", "number", "date", "dropdown", "checkbox"],
        "display_order": 5
    },
    "width": {
        "label": "Breite",
        "control_type": "number",
        "display_order": 6
    },
    "visible": {
        "label": "Sichtbar",
        "control_type": "checkbox",
        "display_order": 7
    },
    "sortable": {
        "label": "Sortierbar",
        "control_type": "checkbox",
        "display_order": 8
    },
    "filterable": {
        "label": "Filterbar",
        "control_type": "checkbox",
        "display_order": 9
    },
    "editable": {
        "label": "Editierbar",
        "control_type": "checkbox",
        "display_order": 10
    },
    "alignment": {
        "label": "Ausrichtung",
        "control_type": "dropdown",
        "options": ["left", "center", "right"],
        "display_order": 11
    },
    "display_order": {
        "label": "Reihenfolge",
        "control_type": "number",
        "display_order": 12
    }
}


def create_template_view():
    """Erstellt Template-View-Struktur"""
    return {
        "ROOT": {
            "VIEW_NAME": "",
            "VIEW_TABLE": "",
            "VIEW_GUID": "",
            "HEADER_TEXT": "",
            "NO_DATA": False,
            "PROJECTION_MODE": "standard",
            "ALLOW_FILTER": True,
            "ALLOW_SORT": True,
            "DEFAULT_SORT_COLUMN": "",
            "DEFAULT_SORT_REVERSE": False
        },
        "METADATEN": {
            "TEMPLATES": VIEW_TEMPLATES,
            "ROOT_CONTROLS": ROOT_CONTROLS,
            "CONTROL_PROPERTIES": CONTROL_PROPERTIES
        }
    }


def insert_or_update_template(db_path):
    """
    Erstellt oder aktualisiert Template in System-Datenbank.
    
    WICHTIG: sys_viewdaten liegt in pdvm_system.db!
    """
    logger.info(f"🚀 Erstelle View-Templates...")
    logger.info(f"  📂 System-Datenbank: {db_path}")
    logger.info(f"  🆔 Template-GUID: {TEMPLATE_GUID}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Template bereits existiert
        cursor.execute(
            "SELECT COUNT(*) FROM sys_viewdaten WHERE uid = ?",
            (TEMPLATE_GUID,)
        )
        
        exists = cursor.fetchone()[0] > 0
        
        # Template-Daten erstellen
        template_data = create_template_view()
        template_json = json.dumps(template_data, ensure_ascii=False, indent=2)
        
        if exists:
            logger.info(f"  🔄 Template existiert - aktualisiere...")
            cursor.execute(
                "UPDATE sys_viewdaten SET daten = ? WHERE uid = ?",
                (template_json, TEMPLATE_GUID)
            )
        else:
            logger.info(f"  ➕ Template erstellen...")
            cursor.execute(
                "INSERT INTO sys_viewdaten (uid, daten) VALUES (?, ?)",
                (TEMPLATE_GUID, template_json)
            )
        
        conn.commit()
        
        logger.info(f"  ✅ Template gespeichert")
        logger.info(f"     - {len(VIEW_TEMPLATES)} Templates")
        logger.info(f"     - {len(ROOT_CONTROLS)} ROOT-Controls (Dictionary-Struktur)")
        logger.info(f"     - {len(CONTROL_PROPERTIES)} Control-Properties (Dictionary-Struktur)")
        
        # Pflichtfelder anzeigen
        pflichtfelder = [key for key, control in ROOT_CONTROLS.items() if control.get('muss')]
        logger.info(f"     - Pflichtfelder: {', '.join(pflichtfelder)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    # sys_viewdaten liegt in pdvm_system.db, nicht in datenbank.db!
    db_path = Path(__file__).parent / 'Daten' / 'pdvm_system.db'
    
    if not db_path.exists():
        logger.error(f"❌ System-Datenbank nicht gefunden: {db_path}")
        exit(1)
    
    insert_or_update_template(str(db_path))
