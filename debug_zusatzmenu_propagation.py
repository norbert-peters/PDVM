# -*- coding: utf-8 -*-
"""
Debug: Zusatzmenü Propagation

Prüft warum zusatz_guid nicht zu Children propagiert wird.

Autor: PDVM-System
Datum: 15.10.2025
"""

import logging
import json

# Setup Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


def debug_prepare_logic():
    """Debuggt prepare_menu_with_zusatz() Logik"""
    logger.info("=" * 80)
    logger.info("🔍 DEBUG: Zusatzmenü Propagation")
    logger.info("=" * 80)
    
    # Echte Datenbank-Struktur laden
    menu_structure = {
        "VERTIKAL": {
            "17ac6504-a80d-4087-a8c2-2cb6235eb3c3": {
                "type": "SUBMENU",
                "label": "Neues Submenu",
                "parent_guid": None,
                "sort_order": 2
            },
            "6b61d628-3607-40d4-8124-8d103a7b49ae": {
                "type": "BUTTON",
                "label": "Neuer Menüpunkt darunter",
                "parent_guid": "17ac6504-a80d-4087-a8c2-2cb6235eb3c3",
                "sort_order": 0
            },
            "802d1afa-67cf-46e1-9ef2-72fc0f0e024a": {
                "type": "BUTTON",
                "label": "Neuer Menüpunkt testen",
                "parent_guid": "17ac6504-a80d-4087-a8c2-2cb6235eb3c3",
                "sort_order": 1
            },
            "1088a12a-dc0e-4e5d-9464-d1e13e16bd2e": {
                "type": "BUTTON",
                "label": "Neuer Menüpunkt neuer als neu",
                "parent_guid": "17ac6504-a80d-4087-a8c2-2cb6235eb3c3",
                "sort_order": 2
            }
        },
        "ZUSATZ": {
            "17ac6504-a80d-4087-a8c2-2cb6235eb3c3": {
                "type": "SUBMENU",
                "label": "Zusatzmenü für 17ac6504",
                "parent_guid": None,
                "sort_order": 0
            },
            "7e3fea1b-d8d2-4215-b2c4-0889f5e5c630": {
                "type": "SUBMENU",
                "label": "Sonderfunktionen",
                "parent_guid": "17ac6504-a80d-4087-a8c2-2cb6235eb3c3",
                "sort_order": 1
            },
            "174a1cd6-5638-4815-b0ea-95ee2184337d": {
                "type": "BUTTON",
                "label": "Speichern",
                "parent_guid": "7e3fea1b-d8d2-4215-b2c4-0889f5e5c630",
                "sort_order": 0
            },
            "625b9878-2cc7-44da-ba6c-e89cdc057f4f": {
                "type": "BUTTON",
                "label": "Extrawurst",
                "parent_guid": "17ac6504-a80d-4087-a8c2-2cb6235eb3c3",
                "sort_order": 2
            }
        }
    }
    
    # SCHRITT 1: Root-SUBMENUs finden
    logger.info("\n📂 SCHRITT 1: Root-SUBMENUs in ZUSATZ finden")
    zusatz_gruppe = menu_structure['ZUSATZ']
    root_submenus = []
    
    for guid, item in zusatz_gruppe.items():
        if item.get('type') == 'SUBMENU' and item.get('parent_guid') is None:
            root_submenus.append((guid, item))
            logger.info(f"  ✅ Root-SUBMENU gefunden: {guid} ({item['label']})")
    
    # SCHRITT 2: In VERTIKAL eintragen
    logger.info("\n🔧 SCHRITT 2: zusatz_guid in VERTIKAL Items eintragen")
    vertikal_gruppe = menu_structure['VERTIKAL']
    
    for root_guid, root_item in root_submenus:
        logger.info(f"\n  🎯 Verarbeite Root-SUBMENU: {root_guid}")
        
        # Prüfe ob GUID in VERTIKAL existiert
        if root_guid in vertikal_gruppe:
            logger.info(f"    ✅ Item in VERTIKAL gefunden!")
            vertikal_gruppe[root_guid]['zusatz_guid'] = root_guid
            logger.info(f"    ✅ zusatz_guid eingetragen")
        else:
            logger.warning(f"    ⚠️ Item NICHT in VERTIKAL gefunden!")
    
    # SCHRITT 3: Zu Children propagieren
    logger.info("\n🌳 SCHRITT 3: zusatz_guid zu Children propagieren")
    
    def propagate_to_children(parent_guid, zusatz_guid, indent=0):
        """Propagiert zusatz_guid rekursiv zu allen Children"""
        prefix = "  " * indent
        logger.info(f"{prefix}🔍 Suche Children von {parent_guid}...")
        
        children_found = 0
        for guid, item in vertikal_gruppe.items():
            if item.get('parent_guid') == parent_guid:
                children_found += 1
                logger.info(f"{prefix}  📌 Child gefunden: {guid} ({item['label']})")
                
                # Nur eintragen wenn Child KEIN eigenes Zusatzmenü hat
                if guid not in zusatz_gruppe or zusatz_gruppe[guid].get('parent_guid') is not None:
                    item['zusatz_guid'] = zusatz_guid
                    logger.info(f"{prefix}    ✅ zusatz_guid = {zusatz_guid} eingetragen")
                    
                    # Rekursiv zu Children dieses Childs
                    propagate_to_children(guid, zusatz_guid, indent + 1)
                else:
                    logger.info(f"{prefix}    ⚠️ Child hat eigenes Zusatzmenü - übersprungen")
        
        if children_found == 0:
            logger.info(f"{prefix}  ℹ️ Keine Children gefunden")
    
    for root_guid, root_item in root_submenus:
        if root_guid in vertikal_gruppe:
            logger.info(f"\n🌲 Propagiere von {root_guid} ({root_item['label']})...")
            propagate_to_children(root_guid, root_guid, indent=1)
    
    # SCHRITT 4: Ergebnis anzeigen
    logger.info("\n" + "=" * 80)
    logger.info("📊 ERGEBNIS: VERTIKAL Items mit zusatz_guid")
    logger.info("=" * 80)
    
    for guid, item in sorted(vertikal_gruppe.items(), key=lambda x: x[1].get('sort_order', 0)):
        zusatz = item.get('zusatz_guid', '---')
        parent = item.get('parent_guid', 'ROOT')
        logger.info(f"  {item['type']:8} | {item['label']:30} | zusatz_guid: {zusatz}")
        logger.info(f"           | parent_guid: {parent}")
    
    # SCHRITT 5: Erwartetes Verhalten
    logger.info("\n" + "=" * 80)
    logger.info("✅ ERWARTETES VERHALTEN beim Button-Klick:")
    logger.info("=" * 80)
    logger.info("  Klick auf '6b61d628-...' (Neuer Menüpunkt darunter)")
    logger.info("  → zusatz_guid: 17ac6504-...")
    logger.info("  → Lädt Zusatzmenü-Children:")
    logger.info("      - 7e3fea1b-... (Sonderfunktionen SUBMENU)")
    logger.info("      - 625b9878-... (Extrawurst BUTTON)")
    logger.info("  → Rendert GRUND + ZUSATZ kombiniert")
    
    # Validierung
    button_guid = "6b61d628-3607-40d4-8124-8d103a7b49ae"
    button = vertikal_gruppe[button_guid]
    
    logger.info("\n" + "=" * 80)
    logger.info("🧪 VALIDIERUNG:")
    logger.info("=" * 80)
    
    if 'zusatz_guid' in button:
        logger.info(f"  ✅ Button '{button['label']}' hat zusatz_guid: {button['zusatz_guid']}")
        return True
    else:
        logger.error(f"  ❌ Button '{button['label']}' hat KEINE zusatz_guid!")
        return False


if __name__ == '__main__':
    success = debug_prepare_logic()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ DEBUG ERFOLGREICH - Logik funktioniert theoretisch!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ DEBUG FEHLGESCHLAGEN - Logik hat Fehler!")
        print("=" * 80)
