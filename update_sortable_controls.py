#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update-Skript: Sortierbare Controls aktivieren

Setzt für alle relevanten Controls die sortable-Eigenschaft auf true.
Damit kann die Sortierung in der View funktionieren.

Autor: PDVM-System
Datum: 2025-01-24
"""

import logging
import sys
from pdvm_central_systemsteuerung import get_gcs

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# View-GUID (aus dem Log entnommen)
VIEW_GUID = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"

# Controls die sortierbar sein sollen mit ihren Default-Einstellungen
SORTABLE_CONTROLS = {
    # === Show-Felder (Anzeige-Werte) ===
    'familienname_show': {
        'direction': 'asc',
        'by_original': False
    },
    'vorname_show': {
        'direction': 'asc',
        'by_original': False
    },
    'geburtsdatum_show': {
        'direction': 'desc',
        'by_original': True  # Nach Original-Datum sortieren (nicht formatiert)
    },
    'geburtsdatum_alter_show': {
        'direction': 'desc',
        'by_original': False
    },
    'geburtsdatum_jahr_show': {
        'direction': 'desc',
        'by_original': False
    },
    'geburtsdatum_monat_show': {
        'direction': 'asc',
        'by_original': False
    },
    'geburtsdatum_tag_show': {
        'direction': 'asc',
        'by_original': False
    },
    'anrede_show': {
        'direction': 'asc',
        'by_original': False
    },
    'email_show': {
        'direction': 'asc',
        'by_original': False
    },
    'telefon_show': {
        'direction': 'asc',
        'by_original': False
    },
    'strasse_show': {
        'direction': 'asc',
        'by_original': False
    },
    'plz_show': {
        'direction': 'asc',
        'by_original': False
    },
    'ort_show': {
        'direction': 'asc',
        'by_original': False
    },
    
    # === Original-Felder (Datenbank-Werte, für ExpertMode) ===
    'familienname_original': {
        'direction': 'asc',
        'by_original': False
    },
    'vorname_original': {
        'direction': 'asc',
        'by_original': False
    },
    'geburtsdatum_original': {
        'direction': 'desc',
        'by_original': False
    },
    'geburtsdatum_alter_original': {
        'direction': 'desc',
        'by_original': False
    },
    'geburtsdatum_jahr_original': {
        'direction': 'desc',
        'by_original': False
    },
    'geburtsdatum_monat_original': {
        'direction': 'asc',
        'by_original': False
    },
    'geburtsdatum_tag_original': {
        'direction': 'asc',
        'by_original': False
    },
    'anrede_original': {
        'direction': 'asc',
        'by_original': False
    },
    'email_original': {
        'direction': 'asc',
        'by_original': False
    },
    'telefon_original': {
        'direction': 'asc',
        'by_original': False
    },
    'strasse_original': {
        'direction': 'asc',
        'by_original': False
    },
    'plz_original': {
        'direction': 'asc',
        'by_original': False
    },
    'ort_original': {
        'direction': 'asc',
        'by_original': False
    },
}


def update_sortable_controls():
    """
    Setzt sortable=true für alle relevanten Controls.
    
    Für jedes Control in SORTABLE_CONTROLS:
    1. Hole Control aus GCS
    2. Setze ui.sortable = true
    3. Setze ui.sortDirection = 'asc' oder 'desc'
    4. Setze ui.sortByOriginal = true/false
    5. Speichere zurück in GCS
    
    Returns:
        bool: True wenn erfolgreich, False bei Fehler
    """
    try:
        logger.info("🚀 Starte Update der sortierbaren Controls...")
        
        # GCS initialisieren falls nötig
        from pdvm_central_systemsteuerung import initialize_gcs, is_gcs_initialized
        
        if not is_gcs_initialized():
            logger.info("🔧 GCS noch nicht initialisiert - initialisiere mit Template-Daten...")
            # Initialisiere mit einer gültigen User-GUID (wird aus Template geladen)
            temp_user_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
            gcs = initialize_gcs(temp_user_guid, None)
            logger.info("✅ GCS temporär initialisiert")
        else:
            gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht verfügbar! Ist das System gestartet?")
            return False
        
        logger.info(f"📋 View-GUID: {VIEW_GUID}")
        
        # Hole Projektions-Tabelle (enthält alle Controls)
        projection_table = gcs.get_projection_table(VIEW_GUID, "table")
        
        if not projection_table:
            logger.warning("⚠️ Keine Projektions-Tabelle für diese View gefunden!")
            return False
        
        logger.info(f"📊 Gefunden: {len(projection_table)} Controls in Projektion")
        logger.info(f"🎯 Zu aktualisieren: {len(SORTABLE_CONTROLS)} Controls")
        
        # Zähler für Statistik
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        # Aktualisiere jedes sortierbare Control
        for control_key, sort_config in SORTABLE_CONTROLS.items():
            try:
                # Prüfe ob Control in Projektion vorhanden
                if control_key not in projection_table:
                    logger.warning(f"⚠️ Control nicht in Projektion gefunden: {control_key}")
                    skipped_count += 1
                    continue
                
                # Hole Control-JSON aus Systemsteuerung-DB
                control_data = gcs._systemsteuerung_db.get_value(VIEW_GUID, control_key)
                
                if not control_data or len(control_data) != 2:
                    logger.warning(f"⚠️ Keine Control-Daten gefunden für: {control_key}")
                    skipped_count += 1
                    continue
                
                control_json, _ = control_data
                
                if not control_json:
                    logger.warning(f"⚠️ Control-JSON ist leer für: {control_key}")
                    skipped_count += 1
                    continue
                
                # Parse JSON
                import json
                control = json.loads(control_json)
                
                # Stelle sicher, dass ui-Dict existiert
                if 'ui' not in control:
                    control['ui'] = {}
                
                # Aktuelle Werte zum Vergleich
                old_sortable = control['ui'].get('sortable', False)
                old_direction = control['ui'].get('sortDirection', 'asc')
                old_by_original = control['ui'].get('sortByOriginal', False)
                
                # Aktualisiere Sortier-Einstellungen
                control['ui']['sortable'] = True
                control['ui']['sortDirection'] = sort_config['direction']
                control['ui']['sortByOriginal'] = sort_config['by_original']
                
                # Speichere zurück als JSON
                updated_json = json.dumps(control, ensure_ascii=False)
                gcs._systemsteuerung_db.set_value(VIEW_GUID, control_key, updated_json)
                
                # Log mit Details
                changes = []
                if old_sortable != True:
                    changes.append(f"sortable: {old_sortable} → True")
                if old_direction != sort_config['direction']:
                    changes.append(f"direction: {old_direction} → {sort_config['direction']}")
                if old_by_original != sort_config['by_original']:
                    changes.append(f"byOriginal: {old_by_original} → {sort_config['by_original']}")
                
                if changes:
                    logger.info(f"✅ {control_key:30s} | {', '.join(changes)}")
                else:
                    logger.info(f"✓  {control_key:30s} | bereits korrekt konfiguriert")
                
                updated_count += 1
                
            except Exception as e:
                logger.error(f"❌ Fehler bei {control_key}: {e}")
                error_count += 1
        
        # Rebuild Projektions-Tabellen nach Änderungen
        logger.info("🔄 Rebuild Projektions-Tabellen...")
        try:
            gcs.rebuild_projection_tables(VIEW_GUID)
            logger.info("✅ Projektions-Tabellen neu erstellt")
        except Exception as e:
            logger.error(f"❌ Fehler beim Rebuild: {e}")
        
        # Zusammenfassung
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 UPDATE ZUSAMMENFASSUNG:")
        logger.info(f"✅ Erfolgreich aktualisiert: {updated_count}")
        logger.info(f"⚠️  Übersprungen:          {skipped_count}")
        logger.info(f"❌ Fehler:                 {error_count}")
        logger.info("=" * 60)
        
        if error_count > 0:
            logger.warning("⚠️ Es gab Fehler! Bitte Logs prüfen.")
            return False
        
        logger.info("🎉 Update erfolgreich abgeschlossen!")
        logger.info("")
        logger.info("📝 Nächste Schritte:")
        logger.info("1. Anwendung neu starten")
        logger.info("2. View öffnen")
        logger.info("3. Auf Spalten-Header klicken zum Sortieren")
        logger.info("4. Zahnrad → '📊 Sortierung & Gruppierung' für erweiterte Optionen")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False


def verify_updates():
    """
    Verifiziert die Updates durch erneutes Laden der Controls.
    
    Returns:
        bool: True wenn alle Updates korrekt sind
    """
    try:
        logger.info("")
        logger.info("🔍 Verifiziere Updates...")
        
        gcs = get_gcs()
        if not gcs:
            logger.error("❌ GCS nicht verfügbar!")
            return False
        
        import json
        
        verification_passed = True
        verified_count = 0
        
        for control_key, expected_config in SORTABLE_CONTROLS.items():
            # Hole Control-JSON
            control_data = gcs._systemsteuerung_db.get_value(VIEW_GUID, control_key)
            
            if not control_data or len(control_data) != 2:
                continue
            
            control_json, _ = control_data
            if not control_json:
                continue
            
            control = json.loads(control_json)
            ui_config = control.get('ui', {})
            
            sortable = ui_config.get('sortable')
            direction = ui_config.get('sortDirection')
            by_original = ui_config.get('sortByOriginal')
            
            # Prüfe ob korrekt gesetzt
            if sortable != True:
                logger.error(f"❌ {control_key}: sortable ist {sortable}, sollte True sein")
                verification_passed = False
            
            if direction != expected_config['direction']:
                logger.error(f"❌ {control_key}: sortDirection ist {direction}, sollte {expected_config['direction']} sein")
                verification_passed = False
            
            if by_original != expected_config['by_original']:
                logger.error(f"❌ {control_key}: sortByOriginal ist {by_original}, sollte {expected_config['by_original']} sein")
                verification_passed = False
            
            verified_count += 1
        
        if verification_passed:
            logger.info(f"✅ Verifikation erfolgreich! Alle {verified_count} Einstellungen korrekt.")
        else:
            logger.error("❌ Verifikation fehlgeschlagen! Einige Einstellungen sind falsch.")
        
        return verification_passed
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Verifikation: {e}")
        return False


if __name__ == "__main__":
    try:
        # Update durchführen
        success = update_sortable_controls()
        
        if not success:
            logger.error("❌ Update fehlgeschlagen!")
            sys.exit(1)
        
        # Verifizieren
        if not verify_updates():
            logger.error("❌ Verifikation fehlgeschlagen!")
            sys.exit(1)
        
        logger.info("")
        logger.info("✅ Alles erfolgreich abgeschlossen!")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Abbruch durch Benutzer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        sys.exit(1)
