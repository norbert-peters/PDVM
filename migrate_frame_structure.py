"""
Frame-Struktur Migration - Von sprechenden Keys zu GUID-basierten Controls

MIGRATION:
- Alte Struktur: METADATEN[TABELLE_GRUPPE_FELD] = {...}
- Neue Struktur: METADATEN[TABELLE][controls][guid] = {table, gruppe, feld, ...}

VERWENDUNG:
    python migrate_frame_structure.py

Autor: PDVM-System
Datum: 18.11.2025
"""

import logging
import sqlite3
import json
import uuid
import sys
from pathlib import Path

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)


def parse_old_key(old_key):
    """
    Extrahiert Tabelle, Gruppe, Feld aus altem Key-Format.
    
    Format: TABELLE_GRUPPE_FELD
    Beispiel: PERSONDATEN_PERSDATEN_ANREDE
    
    Returns:
        (table, gruppe, feld) oder None bei Fehler
    """
    parts = old_key.split('_')
    
    if len(parts) < 3:
        logger.warning(f"⚠️ Key '{old_key}' hat unerwartetes Format")
        return None
    
    # TABELLE ist immer erste Komponente
    table = parts[0]
    
    # Für mehrteilige Gruppen/Felder: Alles zwischen erster und letzter Komponente
    # Beispiel: PERSONDATEN_FINANZDATEN_FINANZDATEN-FINANZDATEN
    if len(parts) == 3:
        # Einfaches Format: TABELLE_GRUPPE_FELD
        gruppe = parts[1]
        feld = parts[2]
    else:
        # Komplexes Format: TABELLE_GRUPPE1_GRUPPE2_..._FELD
        # Heuristik: Letztes Element = Feld, Rest = Gruppe
        gruppe = '_'.join(parts[1:-1])
        feld = parts[-1]
    
    return (table, gruppe, feld)


def migrate_frame_metadaten(old_metadaten):
    """
    Migriert alte METADATEN-Struktur zur neuen hierarchischen Struktur.
    
    Args:
        old_metadaten: Dict mit alten sprechenden Keys
        
    Returns:
        Dict mit neuer Struktur: {TABELLE: {controls: {guid: {...}}}}
    """
    new_metadaten = {}
    
    logger.info(f"🔄 Migriere {len(old_metadaten)} Controls...")
    
    for old_key, control_data in old_metadaten.items():
        # Key parsen
        parsed = parse_old_key(old_key)
        if not parsed:
            logger.error(f"❌ Konnte Key nicht parsen: {old_key}")
            continue
            
        table, gruppe, feld = parsed
        table_upper = table.upper()
        
        logger.info(f"  📋 {old_key} → {table_upper}.controls.{feld}")
        
        # Tabellen-Struktur erstellen wenn nicht vorhanden
        if table_upper not in new_metadaten:
            new_metadaten[table_upper] = {
                'controls': {},
                'standard_controls': {}
            }
        
        # Neue GUID generieren
        control_guid = str(uuid.uuid4())
        
        # Neue Control-Daten erstellen
        new_control = control_data.copy()
        
        # Neue Felder hinzufügen
        new_control['table'] = table.lower()
        new_control['gruppe'] = gruppe.lower()
        new_control['feld'] = feld.lower()
        
        # 'order' → 'display_order' umbenennen (Konsistenz mit View-Editor)
        if 'order' in new_control:
            new_control['display_order'] = new_control.pop('order')
        
        # In neue Struktur einfügen
        new_metadaten[table_upper]['controls'][control_guid] = new_control
        
        logger.info(f"    ✅ GUID: {control_guid}")
    
    logger.info(f"✅ Migration abgeschlossen: {len(new_metadaten)} Tabellen")
    return new_metadaten


def migrate_frame_in_database(db_path, frame_guid, dry_run=False):
    """
    Migriert ein Frame in der Datenbank.
    
    Args:
        db_path: Pfad zur Datenbank
        frame_guid: GUID des zu migrierenden Frames
        dry_run: Wenn True, keine Änderungen schreiben
    """
    logger.info(f"🚀 Migriere Frame: {frame_guid}")
    logger.info(f"  📂 Datenbank: {db_path}")
    logger.info(f"  🔍 Modus: {'DRY RUN' if dry_run else 'LIVE'}")
    
    # Datenbank öffnen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Frame-Daten laden
        cursor.execute(
            "SELECT daten FROM sys_framedaten WHERE uid = ?",
            (frame_guid,)
        )
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"❌ Frame nicht gefunden: {frame_guid}")
            return False
        
        # JSON parsen
        frame_data = json.loads(row[0])
        
        logger.info(f"  📋 Frame geladen: {frame_data.get('ROOT', {}).get('HEADER_TEXT', 'N/A')}")
        
        # Alte METADATEN
        old_metadaten = frame_data.get('METADATEN', {})
        
        if not old_metadaten:
            logger.warning(f"  ⚠️ Keine METADATEN vorhanden - überspringe")
            return True
        
        # Prüfen ob bereits migriert
        # Alte Struktur: TABELLE_GRUPPE_FELD (sprechende Keys)
        # Neue Struktur: TABELLE -> controls -> GUID
        first_key = next(iter(old_metadaten.keys()), None)
        if first_key:
            first_value = old_metadaten[first_key]
            # Neue Struktur: Tabellen-Keys haben 'controls' Sub-Dict
            if isinstance(first_value, dict) and 'controls' in first_value:
                logger.info(f"  ℹ️ Frame bereits migriert (Tabellen-Struktur)")
                return True
        
        # Migration durchführen
        new_metadaten = migrate_frame_metadaten(old_metadaten)
        
        # Neue Daten zusammenbauen
        frame_data['METADATEN'] = new_metadaten
        
        if dry_run:
            logger.info(f"  🔍 DRY RUN: Würde speichern...")
            logger.info(f"     Neue Struktur: {list(new_metadaten.keys())}")
        else:
            # In Datenbank speichern
            new_json = json.dumps(frame_data, ensure_ascii=False, indent=2)
            
            cursor.execute(
                "UPDATE sys_framedaten SET daten = ? WHERE uid = ?",
                (new_json, frame_guid)
            )
            
            conn.commit()
            logger.info(f"  ✅ Frame gespeichert")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Migration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        conn.close()


def migrate_all_frames(db_path, dry_run=False):
    """
    Migriert alle Frames in der Datenbank.
    
    Args:
        db_path: Pfad zur Datenbank
        dry_run: Wenn True, keine Änderungen schreiben
    """
    logger.info("=" * 80)
    logger.info("🚀 FRAME-STRUKTUR MIGRATION")
    logger.info("=" * 80)
    
    # Datenbank öffnen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Alle Frame-GUIDs holen
        cursor.execute("SELECT uid FROM sys_framedaten")
        rows = cursor.fetchall()
        
        frame_guids = [row[0] for row in rows]
        
        logger.info(f"📊 {len(frame_guids)} Frames gefunden")
        logger.info("")
        
        # Jedes Frame migrieren
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, frame_guid in enumerate(frame_guids, 1):
            logger.info(f"[{i}/{len(frame_guids)}] Frame: {frame_guid}")
            
            result = migrate_frame_in_database(db_path, frame_guid, dry_run)
            
            if result is True:
                success_count += 1
            elif result is None:
                skip_count += 1
            else:
                error_count += 1
            
            logger.info("")
        
        # Zusammenfassung
        logger.info("=" * 80)
        logger.info("📊 MIGRATIONS-ZUSAMMENFASSUNG")
        logger.info("=" * 80)
        logger.info(f"  ✅ Erfolgreich:  {success_count}")
        logger.info(f"  ⏭️  Übersprungen: {skip_count}")
        logger.info(f"  ❌ Fehler:       {error_count}")
        logger.info(f"  📊 Gesamt:       {len(frame_guids)}")
        
        if dry_run:
            logger.info("")
            logger.info("⚠️  DRY RUN - Keine Änderungen geschrieben!")
            logger.info("   Für echte Migration: python migrate_frame_structure.py --live")
        
    finally:
        conn.close()


if __name__ == '__main__':
    # sys_framedaten liegt in pdvm_system.db, nicht in datenbank.db!
    db_path = Path(__file__).parent / 'Daten' / 'pdvm_system.db'
    
    if not db_path.exists():
        logger.error(f"❌ System-Datenbank nicht gefunden: {db_path}")
        sys.exit(1)
    
    # Modus (DRY RUN oder LIVE)
    dry_run = '--live' not in sys.argv
    
    # Migration starten
    migrate_all_frames(str(db_path), dry_run=dry_run)
