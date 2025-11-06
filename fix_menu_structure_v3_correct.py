"""
Fix Menu Structure - V3 KORREKTE STRUKTUR
==========================================
Konvertiert Array-Struktur → Dict-Struktur für PdvmCentralDatenbank

ALTE STRUKTUR (FALSCH):
{
    "VERTIKAL": [MenuItem-Dict, MenuItem-Dict, ...],
    "GRUND": [MenuItem-Dict, ...]
}

NEUE STRUKTUR (RICHTIG):
{
    "META": {"VERSION": "V3", ...},
    "VERTIKAL": {
        "item-guid-1": {...item-daten...},
        "item-guid-2": {...item-daten...}
    },
    "GRUND": {
        "item-guid-3": {...item-daten...}
    }
}

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import sys
import json
import logging
from pathlib import Path

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import V2 Komponenten
from v2_central_systemsteuerung import get_gcs
from v2_pdvm_central_datenbank import PdvmCentralDatenbank


def convert_array_to_dict_structure(old_data: dict) -> dict:
    """
    Konvertiert Array-Struktur → Dict-Struktur
    
    Args:
        old_data: Alte Struktur mit Arrays
        
    Returns:
        Neue Struktur mit Dicts (Gruppe → guid → item-data)
    """
    new_data = {}
    
    # META übernehmen (wenn vorhanden)
    if 'META' in old_data:
        new_data['META'] = old_data['META']
    else:
        new_data['META'] = {'VERSION': 'V3', 'MIGRATED_FROM': 'V2'}
    
    # Gruppen konvertieren
    for gruppe in ['VERTIKAL', 'GRUND', 'ZUSATZ']:
        if gruppe not in old_data:
            new_data[gruppe] = {}
            continue
        
        items = old_data[gruppe]
        
        # Wenn schon Dict → übernehmen
        if isinstance(items, dict):
            new_data[gruppe] = items
            logger.info(f"   ✅ {gruppe} bereits Dict-Format: {len(items)} Items")
            continue
        
        # Wenn Array → konvertieren
        if isinstance(items, list):
            gruppe_dict = {}
            for item in items:
                guid = item.get('guid')
                if not guid:
                    logger.warning(f"   ⚠️ Item ohne GUID in {gruppe}: {item}")
                    continue
                
                # Item ohne 'guid' Key speichern (ist ja der Dict-Key)
                item_data = {k: v for k, v in item.items() if k != 'guid'}
                gruppe_dict[guid] = item_data
            
            new_data[gruppe] = gruppe_dict
            logger.info(f"   ✅ {gruppe} konvertiert: {len(gruppe_dict)} Items (Array → Dict)")
        else:
            logger.warning(f"   ⚠️ {gruppe} hat unbekanntes Format: {type(items)}")
            new_data[gruppe] = {}
    
    return new_data


def fix_menu(menu_guid: str, central_db: PdvmCentralDatenbank) -> bool:
    """
    Korrigiert Menü-Struktur
    
    Args:
        menu_guid: GUID des Menüs
        central_db: PdvmCentralDatenbank-Instanz
        
    Returns:
        True bei Erfolg
    """
    try:
        logger.info(f"\n🔧 Korrigiere Menü: {menu_guid}")
        
        # Alte Daten laden
        old_data = central_db.data
        if not old_data:
            logger.warning("   ⚠️ Keine Daten vorhanden")
            return False
        
        logger.info(f"   📦 Alte Struktur geladen: {list(old_data.keys())}")
        
        # Konvertieren
        new_data = convert_array_to_dict_structure(old_data)
        
        logger.info(f"   ✅ Neue Struktur erstellt:")
        for gruppe in ['META', 'VERTIKAL', 'GRUND', 'ZUSATZ']:
            if gruppe == 'META':
                logger.info(f"      {gruppe}: {new_data.get(gruppe, {})}")
            else:
                items = new_data.get(gruppe, {})
                logger.info(f"      {gruppe}: {len(items)} Items")
        
        # Speichern
        central_db.data = new_data
        central_db.speichern()
        
        logger.info("   ✅ Gespeichert!")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Fehler: {e}", exc_info=True)
        return False


def main():
    """Hauptfunktion"""
    print("\n" + "=" * 70)
    print("🔧 FIX MENU STRUCTURE - V3 KORREKTE STRUKTUR")
    print("=" * 70)
    
    # GCS prüfen
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht initialisiert - Login erforderlich!")
        logger.info("💡 Führe v2_main.py aus und versuche es erneut")
        return
    
    logger.info("✅ GCS verfügbar")
    logger.info(f"   DB-Pfad: {gcs.db_path}")
    
    # Alle Menüs aus sys_menudaten laden
    from v2_pdvm_datenbank import PdvmDatenbank
    db = PdvmDatenbank('sys_menudaten')
    
    # Alle GUIDs holen
    connection = db._get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT guid FROM sys_menudaten WHERE guid IS NOT NULL")
    menu_guids = [row[0] for row in cursor.fetchall()]
    connection.close()
    
    logger.info(f"\n📋 Gefundene Menüs: {len(menu_guids)}")
    
    # Jedes Menü korrigieren
    erfolg = 0
    fehler = 0
    
    for menu_guid in menu_guids:
        central_db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        if fix_menu(menu_guid, central_db):
            erfolg += 1
        else:
            fehler += 1
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 70)
    logger.info(f"✅ Erfolgreich: {erfolg}")
    logger.info(f"❌ Fehler: {fehler}")
    logger.info(f"📋 Gesamt: {len(menu_guids)}")
    
    print("\n🎯 Struktur-Korrektur abgeschlossen!")
    print("   Starte v2_main.py neu, um die korrigierten Menüs zu testen")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Hinweis für direkte Ausführung
    print("\n⚠️  HINWEIS: Dieses Skript benötigt initialisiertes GCS")
    print("   1. Starte v2_main.py")
    print("   2. Melde dich an")
    print("   3. Dann in anderem Terminal: python fix_menu_structure_v3_correct.py")
    print()
    
    antwort = input("GCS bereits initialisiert? (j/n): ").strip().lower()
    if antwort == 'j':
        main()
    else:
        print("\n❌ Abgebrochen. Starte zuerst v2_main.py mit Login.")
