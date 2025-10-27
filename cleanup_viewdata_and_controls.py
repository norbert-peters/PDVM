#!/usr/bin/env python3
"""
🔧 CLEANUP SCRIPT: Behebt 4 Probleme mit ViewDaten und Controls

PROBLEME:
1. Controls doppelt gespeichert (controls Dictionary + einzelne Felder)
2. name_original/name_show fehlen in Controls
3. standard_control in falscher Spalte 'name'
4. uid_original/uid_show fehlen ebenfalls

LÖSUNG:
- Controls nur in 'controls' Dictionary behalten
- Einzelne Control-Felder löschen
- name_original/name_show hinzufügen
- uid_original/uid_show hinzufügen
- standard_control aus 'name' entfernen
"""

import sys
import logging
from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def cleanup_view_guid(view_guid: str):
    """Bereinigt ViewDaten und Controls für eine View-GUID"""
    
    logger.info(f"🎯 === CLEANUP START für View {view_guid} ===")
    
    try:
        gcs = get_gcs()
        if not gcs:
            logger.error("❌ GCS nicht verfügbar - bitte erst anmelden!")
            return False
        
        # 1. Lade Controls Dictionary
        logger.info("📂 SCHRITT 1: Lade Controls Dictionary")
        existing_controls = gcs.db.get_static_value(
            gruppe=view_guid,
            feld='controls'
        )
        
        if not existing_controls:
            logger.warning(f"⚠️ Keine Controls gefunden für {view_guid}")
            existing_controls = {}
        else:
            logger.info(f"✅ {len(existing_controls)} Controls geladen")
        
        # 2. Füge fehlende SYSTEM-Controls hinzu
        logger.info("🔧 SCHRITT 2: Prüfe SYSTEM-Controls (uid, name)")
        
        # uid_original
        if 'uid_original' not in existing_controls:
            logger.info("  ➕ Füge uid_original hinzu")
            existing_controls['uid_original'] = {
                'feld': 'UID',
                'name': 'UID',
                'type': 'string',
                'gruppe': 'SYSTEM',
                'control_type': 'original',
                'show': False,
                'expert_mode': True,
                'display_order': 0,
                'expert_order': 0
            }
        
        # name_original
        if 'name_original' not in existing_controls:
            logger.info("  ➕ Füge name_original hinzu")
            existing_controls['name_original'] = {
                'feld': 'NAME',
                'name': 'Satzname',
                'type': 'string',
                'gruppe': 'SYSTEM',
                'control_type': 'original',
                'show': False,
                'expert_mode': True,
                'display_order': 1,
                'expert_order': 1
            }
        
        # uid_show
        if 'uid_show' not in existing_controls:
            logger.info("  ➕ Füge uid_show hinzu")
            existing_controls['uid_show'] = {
                'feld': 'UID',
                'name': 'UID',
                'type': 'string',
                'gruppe': 'SYSTEM',
                'control_type': 'show',
                'show': True,
                'expert_mode': False,
                'display_order': 0,
                'expert_order': 0
            }
        
        # name_show
        if 'name_show' not in existing_controls:
            logger.info("  ➕ Füge name_show hinzu")
            existing_controls['name_show'] = {
                'feld': 'NAME',
                'name': 'Satzname',
                'type': 'string',
                'gruppe': 'SYSTEM',
                'control_type': 'show',
                'show': True,
                'expert_mode': False,
                'display_order': 1,
                'expert_order': 1
            }
        
        logger.info(f"✅ Controls jetzt: {len(existing_controls)}")
        
        # 3. Speichere bereinigte Controls
        logger.info("💾 SCHRITT 3: Speichere bereinigte Controls")
        gcs.db.set_value(
            gruppe=view_guid,
            feld='controls',
            wert=existing_controls
        )
        gcs.db.save_all_values()
        logger.info(f"✅ {len(existing_controls)} Controls in 'controls' Dictionary gespeichert")
        
        # 4. Lösche einzelne Control-Felder (falls vorhanden)
        logger.info("🧹 SCHRITT 4: Lösche doppelte Control-Felder")
        deleted_count = 0
        for control_key in existing_controls.keys():
            try:
                # Prüfe ob Feld existiert
                field_value = gcs._db.get_value(view_guid, control_key)
                if field_value and field_value[0] is not None:
                    # Lösche das Feld
                    gcs._db.set_value(view_guid, control_key, None)
                    deleted_count += 1
                    logger.debug(f"  🗑️ Gelöscht: {control_key}")
            except Exception as e:
                logger.debug(f"  ℹ️ Feld {control_key} existiert nicht: {e}")
        
        if deleted_count > 0:
            gcs._db.save_all_values()
            logger.info(f"✅ {deleted_count} doppelte Felder gelöscht")
        else:
            logger.info("✅ Keine doppelten Felder gefunden")
        
        # 5. Bereinige ViewDaten (standard_control aus 'name' entfernen)
        logger.info("🧹 SCHRITT 5: Bereinige ViewDaten")
        try:
            view_db = PdvmCentralDatenbank('viewdaten', view_guid)
            
            # Prüfe ob 'name' Feld existiert und falsche Daten enthält
            name_value = view_db.get_static_value(gruppe='METADATEN', feld='name')
            if name_value and isinstance(name_value, dict):
                logger.info("  🗑️ Lösche falsches 'name' Feld aus ViewDaten")
                view_db.set_static_value(gruppe='METADATEN', feld='name', wert=None)
                view_db.save_all_values()
                logger.info("  ✅ ViewDaten bereinigt")
            else:
                logger.info("  ✅ ViewDaten sind sauber (kein falsches 'name' Feld)")
                
        except Exception as e:
            logger.warning(f"  ⚠️ ViewDaten-Bereinigung nicht möglich: {e}")
        
        # 6. Projektionen neu bauen
        logger.info("🔄 SCHRITT 6: Projektionen neu bauen")
        gcs._build_projection_tables(view_guid)
        logger.info("✅ Projektionen neu gebaut")
        
        # 7. Status ausgeben
        logger.info("📊 === CLEANUP ABGESCHLOSSEN ===")
        logger.info(f"✅ Controls: {len(existing_controls)}")
        logger.info(f"✅ uid_original: {'uid_original' in existing_controls}")
        logger.info(f"✅ name_original: {'name_original' in existing_controls}")
        logger.info(f"✅ uid_show: {'uid_show' in existing_controls}")
        logger.info(f"✅ name_show: {'name_show' in existing_controls}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cleanup fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Hauptfunktion"""
    
    # Standard View-GUID (kann als Parameter übergeben werden)
    view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
    
    if len(sys.argv) > 1:
        view_guid = sys.argv[1]
    
    logger.info(f"🚀 CLEANUP SCRIPT gestartet")
    logger.info(f"🎯 View-GUID: {view_guid}")
    
    success = cleanup_view_guid(view_guid)
    
    if success:
        logger.info("✅ === CLEANUP ERFOLGREICH ===")
        logger.info("📋 Bitte Anwendung neu starten für vollständige Aktualisierung")
    else:
        logger.error("❌ === CLEANUP FEHLGESCHLAGEN ===")
        sys.exit(1)

if __name__ == '__main__':
    main()
