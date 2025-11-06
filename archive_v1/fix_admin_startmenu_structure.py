"""
Manuelle Struktur-Korrektur für Admin-Startmenü
================================================
Setzt die Struktur auf das von Norbert vorgegebene Format

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import json
import logging
from v2_central_systemsteuerung import get_gcs
from v2_pdvm_central_datenbank import PdvmCentralDatenbank

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Admin-Startmenü GUID
ADMIN_START_MENU_GUID = "5ca6674e-b9ce-4581-9756-64e742883f80"

# KORREKTE STRUKTUR (von Norbert vorgegeben)
CORRECT_STRUCTURE = {
    "META": {
        "VERSION": "V3",
        "MIGRATED_FROM": "V2"
    },
    "VERTIKAL": {
        "c8bef35f-2cdf-49b6-934b-4cddf5b80303": {
            "type": "BUTTON",
            "label": "Personalwesen",
            "sort_order": 0,
            "parent_guid": None,
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "open_app_menu",
                "params": {"app_name": "PERSONALWESEN"}
            }
        },
        "cea83e84-32ea-4361-8b33-8cea9df12b1c": {
            "type": "BUTTON",
            "label": "Finanzwesen",
            "sort_order": 1,
            "parent_guid": None,
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "open_app_menu",
                "params": {"app_name": "FINANZWESEN"}
            }
        },
        "3f9005ad-2507-44a0-a856-146272d5c267": {
            "type": "BUTTON",
            "label": "Benutzerdaten",
            "sort_order": 2,
            "parent_guid": None,
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "open_app_menu",
                "params": {"app_name": "BENUTZERDATEN"}
            }
        },
        "37a77e4a-7d27-4349-92ee-4daae15f9a8d": {
            "type": "BUTTON",
            "label": "Administration",
            "sort_order": 3,
            "parent_guid": None,
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "open_app_menu",
                "params": {"app_name": "ADMINISTRATION"}
            }
        },
        "5412d2d5-0402-42ce-bff6-f1886858a67e": {
            "type": "BUTTON",
            "label": "Testbereich",
            "sort_order": 4,
            "parent_guid": None,
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "open_app_menu",
                "params": {"app_name": "TESTBEREICH"}
            }
        }
    },
    "GRUND": {
        "fecf6732-8ec4-4b0b-8bfd-eddf0c18af88": {
            "type": "SUBMENU",
            "label": "Basis",
            "sort_order": 0,
            "parent_guid": None,
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": None
        },
        "c9662797-e446-4f59-a37d-f652c42d15b9": {
            "type": "BUTTON",
            "label": "Hilfe",
            "sort_order": 0,
            "parent_guid": "fecf6732-8ec4-4b0b-8bfd-eddf0c18af88",
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "show_help",
                "params": {
                    "help_text": "Admin-Startmenü Hilfe",
                    "help_type": "dialog"
                }
            }
        },
        "ae473e8a-12a9-4dda-97f0-a743d0f96498": {
            "type": "BUTTON",
            "label": "Abmelden",
            "sort_order": 1,
            "parent_guid": "fecf6732-8ec4-4b0b-8bfd-eddf0c18af88",
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": {
                "handler": "logout",
                "params": {}
            }
        },
        "6353ee28-c72b-4843-9b00-3d5f846a5de9": {
            "type": "SEPARATOR",
            "label": "",
            "sort_order": 2,
            "parent_guid": "fecf6732-8ec4-4b0b-8bfd-eddf0c18af88",
            "template_guid": None,
            "icon": None,
            "visible": True,
            "enabled": True,
            "tooltip": None,
            "command": None
        }
    },
    "ZUSATZ": {}
}


def main():
    print("\n" + "=" * 70)
    print("🔧 MANUELLE STRUKTUR-KORREKTUR: Admin-Startmenü")
    print("=" * 70)
    
    # Direkt auf Datenbank zugreifen (OHNE GCS)
    from v2_pdvm_datenbank import PdvmDatenbank
    import sqlite3
    
    # Datenbank-Pfad
    db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\mandant_001\datenbank.db"
    
    logger.info(f"✅ Verwende Datenbank: {db_path}")
    
    # Direkt mit SQLite arbeiten
    logger.info(f"\n📂 Lade Menü: {ADMIN_START_MENU_GUID}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Alte Struktur laden
    cursor.execute("SELECT daten FROM sys_menudaten WHERE guid = ?", (ADMIN_START_MENU_GUID,))
    row = cursor.fetchone()
    
    if not row:
        logger.error(f"❌ Menü nicht gefunden: {ADMIN_START_MENU_GUID}")
        conn.close()
        return
    
    old_data = json.loads(row[0])
    
    # Alte Struktur anzeigen
    logger.info("\n📋 ALTE STRUKTUR:")
    if central_db.data:
        for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
            if gruppe in central_db.data:
                value = central_db.data[gruppe]
                if isinstance(value, list):
                    logger.info(f"   {gruppe}: Array mit {len(value)} Items")
                elif isinstance(value, dict):
                    logger.info(f"   {gruppe}: Dict mit {len(value)} Items")
                else:
                    logger.info(f"   {gruppe}: {value}")
    
    # Neue Struktur setzen
    logger.info("\n✏️  Setze NEUE STRUKTUR...")
    central_db.data = CORRECT_STRUCTURE
    central_db.speichern()
    
    logger.info("\n📋 NEUE STRUKTUR:")
    for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
        if gruppe in CORRECT_STRUCTURE:
            value = CORRECT_STRUCTURE[gruppe]
            if isinstance(value, dict):
                logger.info(f"   {gruppe}: Dict mit {len(value)} Items")
    
    logger.info("\n✅ Struktur erfolgreich korrigiert!")
    logger.info("   Starte v2_main.py neu, um das korrigierte Menü zu testen")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
