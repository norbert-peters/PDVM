#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REPARATUR: Controls-Daten

Repariert inkonsistente Controls-Daten:
1. Setzt fehlende display_order Werte
2. Behebt Duplikate
3. Normalisiert expert_order
4. Stellt sicher, dass alle Spalten korrekt sortierbar sind
"""

import logging
from pdvm_central_systemsteuerung import get_gcs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def repair_controls(view_guid, dry_run=True):
    """
    Repariert Controls-Daten für eine View
    
    Args:
        view_guid: GUID der View
        dry_run: Wenn True, nur Simulation ohne Speicherung
    """
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔧 REPARATUR: Controls für View '{view_guid}'")
    logger.info(f"   Modus: {'DRY RUN (Simulation)' if dry_run else 'LIVE (Speichert Änderungen!)'}")
    logger.info(f"{'='*80}\n")
    
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return False
    
    # Controls aus DB holen
    controls, _ = gcs.db.get_value(view_guid, 'controls')
    
    if not controls:
        logger.error(f"❌ Keine Controls für View '{view_guid}' gefunden!")
        return False
    
    logger.info(f"📊 Anzahl Controls: {len(controls)}")
    
    # Sammle Änderungen
    changes = []
    
    # SCHRITT 1: display_order reparieren
    logger.info(f"\n🔧 SCHRITT 1: display_order reparieren...")
    
    # Sammle alle Controls mit und ohne display_order
    controls_with_order = []
    controls_without_order = []
    
    for key, control in controls.items():
        display_order = control.get('display_order')
        if display_order is None or display_order == 999:
            controls_without_order.append(key)
        else:
            controls_with_order.append((key, display_order))
    
    logger.info(f"   ✅ Controls mit display_order: {len(controls_with_order)}")
    logger.info(f"   ❌ Controls ohne display_order: {len(controls_without_order)}")
    
    # Sortiere vorhandene nach display_order
    controls_with_order.sort(key=lambda x: x[1])
    
    # Finde höchsten display_order Wert
    max_order = max([order for _, order in controls_with_order], default=-1)
    
    # Weise fehlenden Controls neue display_order zu
    next_order = max_order + 1
    for key in controls_without_order:
        old_value = controls[key].get('display_order', 'FEHLT')
        controls[key]['display_order'] = next_order
        changes.append(f"   {key}: display_order {old_value} → {next_order}")
        next_order += 1
    
    # SCHRITT 2: Duplikate in display_order beheben
    logger.info(f"\n🔧 SCHRITT 2: Duplikate in display_order beheben...")
    
    display_order_map = {}
    for key, control in controls.items():
        order = control.get('display_order')
        if order not in display_order_map:
            display_order_map[order] = []
        display_order_map[order].append(key)
    
    duplicates = {order: keys for order, keys in display_order_map.items() if len(keys) > 1}
    
    if duplicates:
        logger.info(f"   ❌ Gefundene Duplikate: {len(duplicates)}")
        
        # Neu-Nummerierung für Duplikate
        for order, keys in sorted(duplicates.items()):
            logger.info(f"      Duplikat bei order={order}: {keys}")
            # Erste Spalte behält die Order, andere bekommen neue
            for i, key in enumerate(keys[1:], 1):
                new_order = next_order
                old_order = controls[key].get('display_order')
                controls[key]['display_order'] = new_order
                changes.append(f"   {key}: display_order {old_order} → {new_order} (Duplikat behoben)")
                next_order += 1
    else:
        logger.info(f"   ✅ Keine Duplikate gefunden")
    
    # SCHRITT 3: expert_order synchronisieren
    logger.info(f"\n🔧 SCHRITT 3: expert_order mit display_order synchronisieren...")
    
    # STRATEGIE: expert_order = display_order (vereinfachte Sortierung)
    for key, control in controls.items():
        display_order = control.get('display_order')
        expert_order = control.get('expert_order')
        
        if expert_order is None or expert_order != display_order:
            old_value = expert_order if expert_order is not None else 'FEHLT'
            controls[key]['expert_order'] = display_order
            changes.append(f"   {key}: expert_order {old_value} → {display_order}")
    
    # SCHRITT 4: Zusammenfassung
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 ZUSAMMENFASSUNG:")
    logger.info(f"   Anzahl Änderungen: {len(changes)}")
    
    if changes:
        logger.info(f"\n📝 ÄNDERUNGEN:")
        for change in changes[:20]:  # Erste 20 Änderungen
            logger.info(change)
        if len(changes) > 20:
            logger.info(f"   ... und {len(changes) - 20} weitere Änderungen")
    else:
        logger.info(f"   ✅ Keine Änderungen notwendig - Controls sind konsistent!")
    
    # SCHRITT 5: Speichern (nur wenn nicht dry_run)
    if not dry_run and changes:
        logger.info(f"\n💾 Speichere Änderungen...")
        
        try:
            # Controls speichern
            gcs.db.set_value(view_guid, 'controls', controls)
            
            # Projektions-Tabellen neu aufbauen
            gcs.rebuild_projection_tables(view_guid)
            
            # Persistieren
            gcs.db.save_all_values()
            
            logger.info(f"✅ Änderungen erfolgreich gespeichert!")
            logger.info(f"✅ Projektions-Tabellen neu aufgebaut!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return False
    
    elif dry_run and changes:
        logger.info(f"\n⚠️  DRY RUN: Änderungen NICHT gespeichert!")
        logger.info(f"   Führen Sie das Script mit dry_run=False aus, um die Änderungen zu speichern.")
    
    logger.info(f"\n{'='*80}\n")
    
    return True


def repair_all_views(dry_run=True):
    """Repariert alle Views in der Datenbank"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔧 REPARATUR ALLER VIEWS")
    logger.info(f"{'='*80}\n")
    
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return
    
    # Alle Views finden
    all_views = []
    for gruppe in gcs.db.data.keys():
        if 'controls' in gcs.db.data[gruppe]:
            all_views.append(gruppe)
    
    logger.info(f"📊 Gefundene Views: {len(all_views)}\n")
    
    # Repariere jede View
    success_count = 0
    for view_guid in all_views:
        if repair_controls(view_guid, dry_run=dry_run):
            success_count += 1
        logger.info("")  # Leerzeile zwischen Views
    
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ Erfolgreich repariert: {success_count}/{len(all_views)} Views")
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    import sys
    
    # Kommandozeilen-Argument für Live-Modus
    is_live = "--live" in sys.argv
    dry_run = not is_live
    
    if dry_run:
        print("\n⚠️  DRY RUN MODUS - Keine Änderungen werden gespeichert!")
        print("   Führen Sie das Script mit '--live' aus, um Änderungen zu speichern:")
        print("   python repair_controls_data.py --live\n")
    else:
        print("\n🔴 LIVE MODUS - Änderungen werden gespeichert!")
        print("   Drücken Sie Ctrl+C zum Abbrechen...\n")
        import time
        time.sleep(3)
    
    # Repariere alle Views
    repair_all_views(dry_run=dry_run)
