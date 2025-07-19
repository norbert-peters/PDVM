#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demo-Skript für Tab-Container-Funktionalität
Zeigt die Integration der verschiedenen Komponenten
"""

from pdvm_optimized_data_manager import (
    OptimizedDataManager, TabDefinition, FrameLayoutDefinition
)

def demo_tab_container_setup():
    """Demonstriert die Einrichtung eines Tab-Containers"""
    
    print("=== Tab-Container Demo ===")
    
    # OptimizedDataManager erstellen
    manager = OptimizedDataManager()
    
    # Zentrale Felder hinzufügen
    fields = {
        "name": {"label": "Name", "type": "text", "required": True},
        "email": {"label": "E-Mail", "type": "text", "required": True},
        "telefon": {"label": "Telefon", "type": "text", "required": False},
        "adresse": {"label": "Adresse", "type": "text", "required": True}
    }
    
    for field_id, field_config in fields.items():
        manager.add_central_field(field_id, field_config)
    
    print(f"✓ {len(fields)} zentrale Felder hinzugefügt")
    
    # Gruppen definieren
    groups = {
        "kontakt": {
            "title": "Kontaktdaten",
            "field_assignments": ["name", "email", "telefon"]
        },
        "adresse": {
            "title": "Adressdaten", 
            "field_assignments": ["adresse"]
        }
    }
    
    for group_id, group_config in groups.items():
        manager.add_field_group(group_id, group_config)
    
    print(f"✓ {len(groups)} Feldgruppen definiert")
    
    # Tab-Definitionen erstellen
    tabs = {
        "basic": TabDefinition(
            tab_id="basic",
            tab_name="Grunddaten",
            tab_description="Grundlegende Informationen",
            group_style="sections"
        ),
        "details": TabDefinition(
            tab_id="details", 
            tab_name="Details",
            tab_description="Detaillierte Informationen",
            group_style="accordion"
        )
    }
    
    for tab_id, tab_def in tabs.items():
        manager.add_tab_definition(tab_id, tab_def)
    
    print(f"✓ {len(tabs)} Tab-Definitionen erstellt")
    
    # Gruppen zu Tabs zuordnen
    manager.assign_group_to_tab("kontakt", "basic")
    manager.assign_group_to_tab("adresse", "details")
    
    print("✓ Gruppen zu Tabs zugeordnet")
    
    # Frame-Layout erstellen
    frame_layout = manager.create_frame_layout("TAB_CONTAINER", "mixed")
    
    print(f"✓ Frame-Layout erstellt: {frame_layout.layout_type}")
    print(f"  - Anzahl Tabs: {len(frame_layout.tabs)}")
    print(f"  - Anzahl Gruppen: {len(frame_layout.groups)}")
    
    # Tab-Struktur anzeigen
    print("\n=== Tab-Struktur ===")
    for tab_def in frame_layout.tabs:
        groups_in_tab = manager.get_groups_for_tab(tab_def.tab_id)
        print(f"Tab '{tab_def.tab_name}' ({tab_def.group_style}):")
        for group in groups_in_tab:
            group_title = group.get('title', 'Unbekannt')
            field_count = len(group.get('field_assignments', []))
            print(f"  - Gruppe '{group_title}': {field_count} Felder")
    
    print("\n=== Demo abgeschlossen ===")
    return manager, frame_layout

if __name__ == "__main__":
    demo_tab_container_setup()
