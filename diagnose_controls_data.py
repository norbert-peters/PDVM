#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSE: Controls-Daten Analyse

Analysiert die Controls-Daten für eine View und zeigt:
- Aktuelle display_order und expert_order Werte
- Inkonsistenzen
- Duplikate
- Fehlende Werte
"""

import logging
import json
from pdvm_central_systemsteuerung import get_gcs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def diagnose_controls(view_guid):
    """Analysiere Controls-Daten für eine View"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 DIAGNOSE: Controls für View '{view_guid}'")
    logger.info(f"{'='*80}\n")
    
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return
    
    # Controls aus DB holen
    controls, _ = gcs.db.get_value(view_guid, 'controls')
    
    if not controls:
        logger.error(f"❌ Keine Controls für View '{view_guid}' gefunden!")
        return
    
    logger.info(f"📊 Anzahl Controls: {len(controls)}\n")
    
    # Analyse-Daten sammeln
    display_orders = {}
    expert_orders = {}
    missing_display = []
    missing_expert = []
    show_true_count = 0
    expert_mode_false_count = 0
    
    # Sortiere Controls nach display_order für bessere Übersicht
    sorted_controls = sorted(
        controls.items(), 
        key=lambda x: x[1].get('display_order', 9999)
    )
    
    print(f"\n{'Key':<30} {'Name':<25} {'Show':<6} {'Expert':<7} {'DispOrd':<8} {'ExpOrd':<8} {'Type':<15}")
    print("="*110)
    
    for key, control in sorted_controls:
        name = control.get('name', key)[:24]
        show = str(control.get('show', False))
        expert_mode = str(control.get('expert_mode', False))
        display_order = control.get('display_order', None)
        expert_order = control.get('expert_order', None)
        control_type = control.get('control_type', control.get('type', ''))[:14]
        
        # Statistik sammeln
        if show == 'True':
            show_true_count += 1
        if expert_mode == 'False':
            expert_mode_false_count += 1
        
        # display_order analysieren
        if display_order is None:
            missing_display.append(key)
            disp_str = "FEHLT!"
        else:
            disp_str = str(display_order)
            if display_order in display_orders:
                display_orders[display_order].append(key)
            else:
                display_orders[display_order] = [key]
        
        # expert_order analysieren
        if expert_order is None:
            missing_expert.append(key)
            exp_str = "FEHLT!"
        else:
            exp_str = str(expert_order)
            if expert_order in expert_orders:
                expert_orders[expert_order].append(key)
            else:
                expert_orders[expert_order] = [key]
        
        # Zeile ausgeben
        print(f"{key:<30} {name:<25} {show:<6} {expert_mode:<7} {disp_str:<8} {exp_str:<8} {control_type:<15}")
    
    # Probleme ausgeben
    print(f"\n{'='*110}")
    print(f"\n📊 STATISTIK:")
    print(f"   Gesamt Controls: {len(controls)}")
    print(f"   show=True: {show_true_count}")
    print(f"   expert_mode=False: {expert_mode_false_count}")
    
    print(f"\n⚠️  PROBLEME:")
    
    # Fehlende display_order
    if missing_display:
        print(f"\n   ❌ Spalten OHNE display_order ({len(missing_display)}):")
        for key in missing_display:
            print(f"      - {key}")
    
    # Fehlende expert_order
    if missing_expert:
        print(f"\n   ⚠️  Spalten OHNE expert_order ({len(missing_expert)}):")
        for key in missing_expert:
            print(f"      - {key}")
    
    # Duplikate display_order
    duplicates_display = {order: keys for order, keys in display_orders.items() if len(keys) > 1}
    if duplicates_display:
        print(f"\n   ❌ DUPLIKATE bei display_order:")
        for order, keys in sorted(duplicates_display.items()):
            print(f"      display_order={order}: {', '.join(keys)}")
    
    # Duplikate expert_order
    duplicates_expert = {order: keys for order, keys in expert_orders.items() if len(keys) > 1}
    if duplicates_expert:
        print(f"\n   ⚠️  DUPLIKATE bei expert_order:")
        for order, keys in sorted(duplicates_expert.items()):
            print(f"      expert_order={order}: {', '.join(keys)}")
    
    # Lücken in display_order
    if display_orders:
        max_order = max(o for o in display_orders.keys() if o is not None and o != 9999)
        gaps = []
        for i in range(max_order + 1):
            if i not in display_orders:
                gaps.append(i)
        
        if gaps:
            print(f"\n   ℹ️  Lücken in display_order: {gaps[:10]}{'...' if len(gaps) > 10 else ''}")
    
    # Keine Probleme
    if not missing_display and not duplicates_display and not duplicates_expert:
        print(f"\n   ✅ Keine kritischen Probleme gefunden!")
    
    print(f"\n{'='*110}\n")
    
    # Empfehlungen
    if missing_display or duplicates_display:
        print("💡 EMPFEHLUNG:")
        print("   Führen Sie 'repair_controls_data.py' aus, um die Controls zu reparieren!")
    
    return controls


def list_all_views():
    """Liste alle verfügbaren View-GUIDs auf"""
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return []
    
    # Alle Gruppen in systemsteuerung DB durchsuchen
    all_views = []
    for gruppe in gcs.db.data.keys():
        # Prüfe ob Gruppe 'controls' Feld hat
        if 'controls' in gcs.db.data[gruppe]:
            all_views.append(gruppe)
    
    return all_views


if __name__ == "__main__":
    # Initialisiere System
    from pdvm_central_systemsteuerung import initialize_gcs
    
    # Test mit bekannter View-GUID
    # ÄNDERN SIE DIESE GUID AUF IHRE VIEW!
    test_view_guid = "54073c2c-0efa-4979-8900-2bd1c53d5014"  # Beispiel
    
    # Liste alle verfügbaren Views
    print("\n🔍 Verfügbare Views in der Datenbank:")
    print("="*80)
    
    views = list_all_views()
    if views:
        for i, view_guid in enumerate(views, 1):
            print(f"{i}. {view_guid}")
        print("="*80)
        
        # Analysiere erste View als Beispiel
        if views:
            print(f"\n📊 Analysiere View: {views[0]}\n")
            diagnose_controls(views[0])
    else:
        print("❌ Keine Views mit Controls gefunden!")
    
    # Wenn Sie eine spezifische View analysieren wollen, kommentieren Sie die Zeile unten ein:
    # diagnose_controls("IHRE-VIEW-GUID-HIER")
