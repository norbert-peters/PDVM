"""
Frame-Templates erstellen - Template-GUID für Frame-Controls

Erstellt Template-Datensatz in sys_framedaten mit GUID 55555555-5555-5555-5555-555555555555

VERWENDUNG:
    python create_frame_templates.py

Autor: PDVM-System
Datum: 18.11.2025
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

# Frame-Control-Templates
FRAME_TEMPLATES = {
    "frame_text": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "source_path": "root",
        "type": "text",
        "label": "",
        "tooltip": "",
        "historical": False,
        "abdatum": False,
        "display_ab": None,
        "display_val": None,
        "display_ti_ab_short": False,
        "display_ti_val_short": False,
        "tab": 1,
        "display_order": 0,
        "read_only": False,
        "conversion_in": None,
        "conversion_out": None,
        "ui_width_label": None,
        "ui_width_value": None,
        "ui_width_button": None,
        "ui_indent_ab": None,
        "dropdown_config": {},
        "help_config": {}
    },
    "frame_dropdown": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "source_path": "root",
        "type": "dropdown",
        "label": "",
        "tooltip": "",
        "historical": False,
        "abdatum": False,
        "display_ab": None,
        "display_val": None,
        "display_ti_ab_short": False,
        "display_ti_val_short": False,
        "tab": 1,
        "display_order": 0,
        "read_only": False,
        "conversion_in": None,
        "conversion_out": None,
        "ui_width_label": None,
        "ui_width_value": None,
        "ui_width_button": None,
        "ui_indent_ab": None,
        "dropdown_config": {
            "table": "dropdowndaten",
            "key": "",
            "value": ""
        },
        "help_config": {}
    },
    "frame_datetime": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "source_path": "root",
        "type": "datetime",
        "label": "",
        "tooltip": "",
        "historical": True,
        "abdatum": True,
        "display_ab": "all",
        "display_val": "only_date",
        "display_ti_ab_short": False,
        "display_ti_val_short": False,
        "tab": 1,
        "display_order": 0,
        "read_only": False,
        "conversion_in": None,
        "conversion_out": None,
        "ui_width_label": None,
        "ui_width_value": None,
        "ui_width_button": None,
        "ui_indent_ab": None,
        "dropdown_config": {},
        "help_config": {}
    },
    "frame_viewtable": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "source_path": "root",
        "type": "viewtable",
        "label": "",
        "tooltip": "",
        "historical": True,
        "abdatum": True,
        "display_ab": "all",
        "display_val": "only_date",
        "display_ti_ab_short": False,
        "display_ti_val_short": False,
        "tab": 1,
        "display_order": 0,
        "read_only": False,
        "conversion_in": None,
        "conversion_out": None,
        "ui_width_label": None,
        "ui_width_value": None,
        "ui_width_button": None,
        "ui_indent_ab": None,
        "viewtable_config": {
            "guid": ""
        },
        "dropdown_config": {},
        "help_config": {}
    },
    "frame_number": {
        "table": "",
        "gruppe": "",
        "feld": "",
        "source_path": "root",
        "type": "number",
        "label": "",
        "tooltip": "",
        "historical": False,
        "abdatum": False,
        "display_ab": None,
        "display_val": None,
        "display_ti_ab_short": False,
        "display_ti_val_short": False,
        "tab": 1,
        "display_order": 0,
        "read_only": False,
        "conversion_in": None,
        "conversion_out": None,
        "ui_width_label": None,
        "ui_width_value": None,
        "ui_width_button": None,
        "ui_indent_ab": None,
        "dropdown_config": {},
        "help_config": {}
    }
}

# ROOT_CONTROLS für Frame-Editor als DICTIONARY (LINEAR!)
ROOT_CONTROLS = {
    "ROOT_TABLE": {"label": "Root-Tabelle", "control_type": "text", "readonly": False, "display_order": 0, "muss": True, "default_value": ""},
    "VIEW_GUID": {"label": "View-GUID", "control_type": "text", "readonly": False, "display_order": 1, "muss": False, "default_value": ""},
    "DIALOG_GUID": {"label": "Dialog-GUID", "control_type": "text", "readonly": False, "display_order": 2, "muss": False, "default_value": ""},
    "HEADER_TEXT": {"label": "Kopfzeile", "control_type": "text", "readonly": False, "display_order": 3, "muss": False, "default_value": ""},
    "EDIT_TYPE": {"label": "Editor-Typ", "control_type": "text", "readonly": False, "display_order": 4, "muss": True, "default_value": "input_form"},
    "EDIT_TABS": {"label": "Anzahl Tabs", "control_type": "number", "readonly": False, "display_order": 5, "muss": False, "default_value": "1"},
    "EDIT_TAB_LABEL_01": {"label": "Tab 1 Label", "control_type": "text", "readonly": False, "display_order": 6, "muss": False, "default_value": "Allgemein"},
    "EDIT_TAB_LABEL_02": {"label": "Tab 2 Label", "control_type": "text", "readonly": False, "display_order": 7, "muss": False, "default_value": ""},
    "DISPLAY_ST": {"label": "Display-Stichtag", "control_type": "text", "readonly": False, "display_order": 8, "muss": False, "default_value": "current"},
    "DISPLAY_TIME_SHORT": {"label": "Zeit kurz", "control_type": "checkbox", "readonly": False, "display_order": 9, "muss": False, "default_value": False},
    "WIDTH_INDENT_AB": {"label": "Einrückung AB", "control_type": "number", "readonly": False, "display_order": 10, "muss": False, "default_value": "20"},
    "WIDTH_LABEL": {"label": "Breite Label", "control_type": "number", "readonly": False, "display_order": 11, "muss": False, "default_value": "150"},
    "WIDTH_BUTTON": {"label": "Breite Button", "control_type": "number", "readonly": False, "display_order": 12, "muss": False, "default_value": "30"},
    "WIDTH_CONTROL": {"label": "Breite Control", "control_type": "number", "readonly": False, "display_order": 13, "muss": False, "default_value": "200"},
    "WIDTH_FRAME": {"label": "Breite Frame", "control_type": "number", "readonly": False, "display_order": 14, "muss": False, "default_value": "600"}
}

# CONTROL_PROPERTIES für Frame-Controls als DICTIONARY (LINEAR!)
CONTROL_PROPERTIES = {
    "table": {"label": "Tabelle", "control_type": "text", "display_order": 0},
    "gruppe": {"label": "Gruppe", "control_type": "text", "display_order": 1},
    "feld": {"label": "Feld", "control_type": "text", "display_order": 2},
    "source_path": {"label": "Datenquelle", "control_type": "text", "display_order": 3},
    "label": {"label": "Label", "control_type": "text", "display_order": 4},
    "tooltip": {"label": "Tooltip", "control_type": "text", "display_order": 5},
    "type": {"label": "Typ", "control_type": "dropdown", "options": ["text", "dropdown", "datetime", "viewtable", "number"], "display_order": 6},
    "tab": {"label": "Tab", "control_type": "number", "display_order": 7},
    "display_order": {"label": "Reihenfolge", "control_type": "number", "display_order": 8},
    "historical": {"label": "Historisch", "control_type": "checkbox", "display_order": 9},
    "abdatum": {"label": "AB-Datum", "control_type": "checkbox", "display_order": 10},
    "display_ab": {"label": "AB-Anzeige", "control_type": "dropdown", "options": ["all", "only_date", None], "display_order": 11},
    "display_val": {"label": "Wert-Anzeige", "control_type": "dropdown", "options": ["all", "only_date", None], "display_order": 12},
    "read_only": {"label": "Nur Lesen", "control_type": "checkbox", "display_order": 13},
    "ui_width_label": {"label": "Breite Label", "control_type": "number", "display_order": 14},
    "ui_width_value": {"label": "Breite Wert", "control_type": "number", "display_order": 15},
    "ui_width_button": {"label": "Breite Button", "control_type": "number", "display_order": 16}
}


def create_template_frame():
    """Erstellt Template-Frame-Struktur"""
    return {
        "ROOT": {
            "ROOT_TABLE": "",
            "VIEW_GUID": "",
            "DIALOG_GUID": "",
            "HEADER_TEXT": "",
            "EDIT_TYPE": "input_form",
            "EDIT_TABS": "1",
            "EDIT_TAB_LABEL_01": "Allgemein",
            "EDIT_TAB_LABEL_02": "",
            "DISPLAY_ST": "current",
            "DISPLAY_TIME_SHORT": False,
            "WIDTH_INDENT_AB": "20",
            "WIDTH_LABEL": "150",
            "WIDTH_BUTTON": "30",
            "WIDTH_CONTROL": "200",
            "WIDTH_FRAME": "600"
        },
        "METADATEN": {
            "TEMPLATES": FRAME_TEMPLATES,
            "ROOT_CONTROLS": ROOT_CONTROLS,
            "CONTROL_PROPERTIES": CONTROL_PROPERTIES
        }
    }


def insert_or_update_template(db_path):
    """
    Erstellt oder aktualisiert Template in System-Datenbank.
    
    WICHTIG: sys_framedaten liegt in pdvm_system.db!
    """
    logger.info(f"🚀 Erstelle Frame-Templates...")
    logger.info(f"  📂 System-Datenbank: {db_path}")
    logger.info(f"  🆔 Template-GUID: {TEMPLATE_GUID}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Template bereits existiert
        cursor.execute(
            "SELECT COUNT(*) FROM sys_framedaten WHERE uid = ?",
            (TEMPLATE_GUID,)
        )
        
        exists = cursor.fetchone()[0] > 0
        
        # Template-Daten erstellen
        template_data = create_template_frame()
        template_json = json.dumps(template_data, ensure_ascii=False, indent=2)
        
        if exists:
            logger.info(f"  🔄 Template existiert - aktualisiere...")
            cursor.execute(
                "UPDATE sys_framedaten SET daten = ? WHERE uid = ?",
                (template_json, TEMPLATE_GUID)
            )
        else:
            logger.info(f"  ➕ Template erstellen...")
            cursor.execute(
                "INSERT INTO sys_framedaten (uid, daten) VALUES (?, ?)",
                (TEMPLATE_GUID, template_json)
            )
        
        conn.commit()
        
        logger.info(f"  ✅ Template gespeichert")
        logger.info(f"     - {len(FRAME_TEMPLATES)} Templates")
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
    # sys_framedaten liegt in pdvm_system.db, nicht in datenbank.db!
    db_path = Path(__file__).parent / 'Daten' / 'pdvm_system.db'
    
    if not db_path.exists():
        logger.error(f"❌ System-Datenbank nicht gefunden: {db_path}")
        exit(1)
    
    insert_or_update_template(str(db_path))
