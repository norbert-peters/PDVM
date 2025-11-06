#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Erweiterte Framedaten-Struktur für universellen Tab-Dialog
Unterstützt verschiedene Modi und Gruppierungsarten
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid


@dataclass
class TabDefinition:
    """Definition eines Tabs im universellen Dialog"""
    
    tab_id: str
    tab_name: str
    tab_type: str  # "view", "inputframe", "settings", "maintenance"
    tab_order: int = 100
    tab_icon: str = ""
    
    # Sichtbarkeit und Aktivierung
    visible: bool = True
    enabled: bool = True
    start_tab: bool = False  # Ist dies der Start-Tab?
    
    # Verknüpfung zu Datenquellen
    view_guid: Optional[str] = None  # GUID der Viewdaten
    frame_guid: Optional[str] = None  # GUID der Framedaten
    
    # UI-Eigenschaften
    grouping_style: str = "sections"  # sections, accordion, tabs, inline
    scrollable: bool = True
    max_height: Optional[int] = None
    
    # Modi-spezifische Sichtbarkeit
    visible_modes: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ModeConfiguration:
    """Konfiguration für verschiedene Dialog-Modi"""
    
    mode_id: int
    mode_name: str = ""
    mode_description: str = ""
    mode_icon: str = ""
    
    # Standard-Tab-Konfiguration für diesen Modus
    default_start_tab: Optional[str] = None
    available_tabs: List[str] = field(default_factory=list)
    
    # Datenbank-Verbindung
    primary_table: Optional[str] = None
    primary_key_field: Optional[str] = None
    
    # Spezielle Eigenschaften
    read_only: bool = False
    requires_admin: bool = False
    
    def __post_init__(self):
        # Standard-Modi definieren
        if self.mode_id == 0:
            self.mode_name = "Datenpflege"
            self.mode_description = "Standard Datenbearbeitung"
            self.mode_icon = "📝"
        elif self.mode_id == 1:
            self.mode_name = "Pflege Framedaten"
            self.mode_description = "Verwaltung von Frame-Strukturen"
            self.mode_icon = "🏗️"
            self.requires_admin = True
        elif self.mode_id == 2:
            self.mode_name = "Pflege Menü"
            self.mode_description = "Menü-Konfiguration"
            self.mode_icon = "📋"
            self.requires_admin = True
        elif self.mode_id == 3:
            self.mode_name = "Pflege Anwendung"
            self.mode_description = "Anwendungs-Einstellungen"
            self.mode_icon = "⚙️"
            self.requires_admin = True
        elif self.mode_id == 4:
            self.mode_name = "Pflege Benutzereinstellungen"
            self.mode_description = "Persönliche Einstellungen"
            self.mode_icon = "👤"
        elif self.mode_id == 5:
            self.mode_name = "Pflege Benutzer"
            self.mode_description = "Benutzer-Verwaltung"
            self.mode_icon = "👥"
            self.requires_admin = True
        else:
            self.mode_name = "Unbekannter Modus"
            self.mode_description = "Dieser Modus ist nicht definiert"
            self.mode_icon = "❓"


@dataclass
class UniversalFrameStructure:
    """Universelle Framedaten-Struktur für Tab-basierten Dialog"""
    
    frame_guid: str
    frame_name: str
    frame_version: str = "1.0"
    
    # Verknüpfung zu Viewdaten
    view_guid: Optional[str] = None
    view_name: Optional[str] = None
    
    # Tab-Definitionen
    tabs: List[TabDefinition] = field(default_factory=list)
    
    # Modi-Konfigurationen
    mode_configurations: Dict[int, ModeConfiguration] = field(default_factory=dict)
    
    # Standard-Einstellungen
    default_mode: int = 0
    default_grouping_style: str = "sections"
    
    # UI-Eigenschaften
    dialog_width: int = 1000
    dialog_height: int = 700
    dialog_resizable: bool = True
    
    # Datenbank-Integration
    central_db_instance: Optional[str] = None
    auto_save: bool = True
    confirm_changes: bool = True
    
    # Metadaten
    created_at: str = ""
    created_by: str = ""
    modified_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = self.created_at
        if not self.frame_guid:
            self.frame_guid = str(uuid.uuid4())
    
    def add_tab(self, tab_def: TabDefinition):
        """Fügt einen Tab hinzu"""
        self.tabs.append(tab_def)
    
    def get_tabs_for_mode(self, mode: int) -> List[TabDefinition]:
        """Gibt alle Tabs zurück, die für einen bestimmten Modus sichtbar sind"""
        return [tab for tab in self.tabs if mode in tab.visible_modes and tab.visible]
    
    def get_start_tab_for_mode(self, mode: int) -> Optional[TabDefinition]:
        """Gibt den Start-Tab für einen bestimmten Modus zurück"""
        mode_config = self.mode_configurations.get(mode)
        if mode_config and mode_config.default_start_tab:
            for tab in self.tabs:
                if tab.tab_id == mode_config.default_start_tab:
                    return tab
        
        # Fallback: Erster sichtbarer Tab
        available_tabs = self.get_tabs_for_mode(mode)
        return available_tabs[0] if available_tabs else None
    
    def add_mode_configuration(self, mode_config: ModeConfiguration):
        """Fügt eine Modi-Konfiguration hinzu"""
        self.mode_configurations[mode_config.mode_id] = mode_config


class UniversalFrameDataGenerator:
    """Generator für universelle Framedaten-Strukturen"""
    
    @staticmethod
    def create_standard_structure(view_guid: str, view_name: str) -> UniversalFrameStructure:
        """Erstellt eine Standard-Struktur für einen universellen Dialog"""
        
        # Basis-Struktur
        structure = UniversalFrameStructure(
            frame_guid=str(uuid.uuid4()),
            frame_name=f"Universal Dialog für {view_name}",
            view_guid=view_guid,
            view_name=view_name
        )
        
        # Standard-Tabs definieren
        tabs = [
            # 1. View-Tab (immer erster Tab)
            TabDefinition(
                tab_id="view_tab",
                tab_name="Ansicht",
                tab_type="view",
                tab_order=1,
                tab_icon="👁️",
                view_guid=view_guid,
                start_tab=True,
                grouping_style="sections",
                visible_modes=[0, 1, 2, 3, 4, 5]  # In allen Modi sichtbar
            ),
            
            # 2. Datenpflege-Tab
            TabDefinition(
                tab_id="data_maintenance",
                tab_name="Daten bearbeiten",
                tab_type="inputframe",
                tab_order=2,
                tab_icon="📝",
                grouping_style="accordion",
                visible_modes=[0]  # Nur im Datenpflege-Modus
            ),
            
            # 3. Frame-Pflege-Tab
            TabDefinition(
                tab_id="frame_maintenance",
                tab_name="Frame bearbeiten",
                tab_type="inputframe",
                tab_order=3,
                tab_icon="🏗️",
                grouping_style="tabs",
                visible_modes=[1]  # Nur im Frame-Pflege-Modus
            ),
            
            # 4. Menü-Pflege-Tab
            TabDefinition(
                tab_id="menu_maintenance",
                tab_name="Menü bearbeiten",
                tab_type="inputframe",
                tab_order=4,
                tab_icon="📋",
                grouping_style="sections",
                visible_modes=[2]  # Nur im Menü-Pflege-Modus
            ),
            
            # 5. Anwendungs-Pflege-Tab
            TabDefinition(
                tab_id="application_maintenance",
                tab_name="Anwendung konfigurieren",
                tab_type="settings",
                tab_order=5,
                tab_icon="⚙️",
                grouping_style="accordion",
                visible_modes=[3]  # Nur im Anwendungs-Pflege-Modus
            ),
            
            # 6. Benutzereinstellungen-Tab
            TabDefinition(
                tab_id="user_settings",
                tab_name="Meine Einstellungen",
                tab_type="settings",
                tab_order=6,
                tab_icon="👤",
                grouping_style="sections",
                visible_modes=[4]  # Nur im Benutzereinstellungs-Modus
            ),
            
            # 7. Benutzer-Pflege-Tab
            TabDefinition(
                tab_id="user_maintenance",
                tab_name="Benutzer verwalten",
                tab_type="inputframe",
                tab_order=7,
                tab_icon="👥",
                grouping_style="tabs",
                visible_modes=[5]  # Nur im Benutzer-Pflege-Modus
            )
        ]
        
        # Tabs hinzufügen
        for tab in tabs:
            structure.add_tab(tab)
        
        # Modi-Konfigurationen hinzufügen
        for mode_id in range(6):
            mode_config = ModeConfiguration(mode_id=mode_id)
            
            # Start-Tab für jeden Modus festlegen
            if mode_id == 0:
                mode_config.default_start_tab = "view_tab"
                mode_config.available_tabs = ["view_tab", "data_maintenance"]
            elif mode_id == 1:
                mode_config.default_start_tab = "frame_maintenance"
                mode_config.available_tabs = ["view_tab", "frame_maintenance"]
            elif mode_id == 2:
                mode_config.default_start_tab = "menu_maintenance"
                mode_config.available_tabs = ["view_tab", "menu_maintenance"]
            elif mode_id == 3:
                mode_config.default_start_tab = "application_maintenance"
                mode_config.available_tabs = ["view_tab", "application_maintenance"]
            elif mode_id == 4:
                mode_config.default_start_tab = "user_settings"
                mode_config.available_tabs = ["view_tab", "user_settings"]
            elif mode_id == 5:
                mode_config.default_start_tab = "user_maintenance"
                mode_config.available_tabs = ["view_tab", "user_maintenance"]
            
            structure.add_mode_configuration(mode_config)
        
        return structure
    
    @staticmethod
    def create_call_data(view_guid: str, mode: int = 0, start_tab: str = None,
                        user_guid: str = None, language: str = "de") -> Dict[str, Any]:
        """Erstellt Call-Data für den universellen Dialog"""
        
        # Framedaten-Struktur generieren
        view_name = f"View_{view_guid[:8]}"  # Vereinfacht für Demo
        frame_structure = UniversalFrameDataGenerator.create_standard_structure(view_guid, view_name)
        
        # Start-Tab bestimmen
        if start_tab:
            # Explizit angegebener Start-Tab
            selected_start_tab = start_tab
        else:
            # Start-Tab basierend auf Modus
            start_tab_def = frame_structure.get_start_tab_for_mode(mode)
            selected_start_tab = start_tab_def.tab_id if start_tab_def else "view_tab"
        
        # Call-Data zusammenstellen
        call_data = {
            "user_guid": user_guid or str(uuid.uuid4()),
            "frame_guid": frame_structure.frame_guid,
            "view_guid": view_guid,
            "mode": mode,
            "start_tab": selected_start_tab,
            "language": language,
            
            # Framedaten-Struktur
            "framedaten": {
                "frame_info": {
                    "frame_guid": frame_structure.frame_guid,
                    "frame_name": frame_structure.frame_name,
                    "frame_version": frame_structure.frame_version,
                    "view_guid": frame_structure.view_guid,
                    "view_name": frame_structure.view_name
                },
                
                "dialog_config": {
                    "dialog_type": "universal_tab_dialog",
                    "mode": mode,
                    "default_width": frame_structure.dialog_width,
                    "default_height": frame_structure.dialog_height,
                    "resizable": frame_structure.dialog_resizable,
                    "auto_save": frame_structure.auto_save,
                    "confirm_changes": frame_structure.confirm_changes
                },
                
                "tabs": [
                    {
                        "tab_id": tab.tab_id,
                        "tab_name": tab.tab_name,
                        "tab_type": tab.tab_type,
                        "tab_order": tab.tab_order,
                        "tab_icon": tab.tab_icon,
                        "visible": tab.visible and mode in tab.visible_modes,
                        "enabled": tab.enabled,
                        "start_tab": tab.tab_id == selected_start_tab,
                        "view_guid": tab.view_guid,
                        "frame_guid": tab.frame_guid,
                        "grouping_style": tab.grouping_style,
                        "scrollable": tab.scrollable,
                        "max_height": tab.max_height
                    }
                    for tab in frame_structure.get_tabs_for_mode(mode)
                ],
                
                "mode_config": {
                    "mode_id": mode,
                    "mode_name": frame_structure.mode_configurations[mode].mode_name,
                    "mode_description": frame_structure.mode_configurations[mode].mode_description,
                    "mode_icon": frame_structure.mode_configurations[mode].mode_icon,
                    "read_only": frame_structure.mode_configurations[mode].read_only,
                    "requires_admin": frame_structure.mode_configurations[mode].requires_admin
                },
                
                "database_config": {
                    "central_db_instance": frame_structure.central_db_instance,
                    "primary_table": frame_structure.mode_configurations[mode].primary_table,
                    "primary_key_field": frame_structure.mode_configurations[mode].primary_key_field
                }
            }
        }
        
        return call_data


# Demo-Funktionen
def demo_universal_structure():
    """Demonstriert die universelle Struktur"""
    
    print("=== Universelle Framedaten-Struktur Demo ===")
    
    # Test-GUID für View
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    # Call-Data für verschiedene Modi generieren
    modes_to_test = [0, 1, 2, 3, 4, 5, 6]  # 6 ist undefined
    
    for mode in modes_to_test:
        print(f"\n--- Modus {mode} ---")
        
        try:
            call_data = UniversalFrameDataGenerator.create_call_data(
                view_guid=test_view_guid,
                mode=mode,
                user_guid="test-user-guid"
            )
            
            framedaten = call_data["framedaten"]
            mode_config = framedaten["mode_config"]
            tabs = framedaten["tabs"]
            
            print(f"Modus: {mode_config['mode_name']} {mode_config['mode_icon']}")
            print(f"Beschreibung: {mode_config['mode_description']}")
            print(f"Anzahl Tabs: {len(tabs)}")
            print(f"Start-Tab: {call_data['start_tab']}")
            
            if mode_config["requires_admin"]:
                print("⚠️  Erfordert Admin-Berechtigung")
            
            print("Verfügbare Tabs:")
            for tab in tabs:
                start_marker = "🔸" if tab["start_tab"] else "  "
                print(f"  {start_marker} {tab['tab_icon']} {tab['tab_name']} ({tab['grouping_style']})")
                
        except Exception as e:
            print(f"❌ Fehler bei Modus {mode}: {e}")
    
    print("\n=== Demo abgeschlossen ===")


if __name__ == "__main__":
    demo_universal_structure()
