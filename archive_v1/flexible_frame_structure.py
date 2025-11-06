#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Erweiterte Framedaten-Struktur mit flexibler Multi-Tab-Architektur
Unterstützt mehrere Tabs pro Modus mit hierarchischen Gruppierungen
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid


@dataclass
class GroupDefinition:
    """Definition einer Gruppe (kann in verschiedenen Tabs verwendet werden)"""
    
    group_id: str
    group_name: str
    group_description: str = ""
    group_icon: str = ""
    
    # Hierarchie
    parent_group_id: Optional[str] = None  # Übergeordnete Gruppe
    sub_groups: List[str] = field(default_factory=list)  # Untergruppen-IDs
    
    # UI-Eigenschaften
    grouping_style: str = "sections"  # sections, accordion, tabs, inline
    sort_order: int = 100
    collapsible: bool = False
    initially_collapsed: bool = False
    
    # Feldtypen für diese Gruppe
    field_types: List[str] = field(default_factory=list)  # z.B. ["text", "dropdown", "datetime"]
    field_count_estimate: int = 0  # Geschätzte Anzahl Felder
    
    # Sichtbarkeit
    visible: bool = True
    enabled: bool = True
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class TabDefinition:
    """Erweiterte Tab-Definition mit flexibler Gruppenorganisation"""
    
    tab_id: str
    tab_name: str
    tab_type: str  # "view", "inputframe", "settings", "maintenance"
    tab_order: int = 100
    tab_icon: str = ""
    
    # Gruppenzuordnung für diesen Tab
    assigned_groups: List[str] = field(default_factory=list)  # Group-IDs die diesem Tab zugeordnet sind
    primary_group: Optional[str] = None  # Hauptgruppe für diesen Tab
    
    # Sichtbarkeit und Aktivierung
    visible: bool = True
    enabled: bool = True
    start_tab: bool = False  # Ist dies der Start-Tab?
    
    # Verknüpfung zu Datenquellen
    view_guid: Optional[str] = None  # GUID der Viewdaten
    frame_guid: Optional[str] = None  # GUID der Framedaten
    
    # UI-Eigenschaften für diesen Tab
    tab_grouping_style: str = "sections"  # Wie werden Gruppen in diesem Tab dargestellt
    scrollable: bool = True
    max_height: Optional[int] = None
    columns: int = 1  # Anzahl Spalten für Gruppen-Layout
    
    # Modi-spezifische Sichtbarkeit
    visible_modes: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])
    
    # Besondere Eigenschaften
    auto_save: bool = True
    confirm_changes: bool = True
    read_only: bool = False
    
    # Metadaten
    created_at: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ModeConfiguration:
    """Erweiterte Modus-Konfiguration mit flexibler Tab-Struktur"""
    
    mode_id: int
    mode_name: str = ""
    mode_description: str = ""
    mode_icon: str = ""
    
    # Tab-Organisation für diesen Modus
    mode_tabs: List[str] = field(default_factory=list)  # Tab-IDs für diesen Modus
    default_start_tab: Optional[str] = None
    tab_organization: str = "horizontal"  # horizontal, vertical, nested
    
    # Datenbank-Verbindung
    primary_table: Optional[str] = None
    primary_key_field: Optional[str] = None
    
    # Spezielle Eigenschaften
    read_only: bool = False
    requires_admin: bool = False
    max_tabs_count: int = 10  # Maximum Tabs für diesen Modus
    
    # Tab-spezifische Einstellungen
    allow_tab_reordering: bool = True
    show_tab_icons: bool = True
    tab_style: str = "standard"  # standard, compact, vertical
    
    def __post_init__(self):
        # Standard-Modi definieren
        if self.mode_id == 0:
            self.mode_name = "Datenpflege"
            self.mode_description = "Standard Datenbearbeitung mit flexibler Tab-Struktur"
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
class FlexibleFrameStructure:
    """Flexible Framedaten-Struktur mit hierarchischen Gruppen und Multi-Tabs"""
    
    frame_guid: str
    frame_name: str
    frame_version: str = "2.0"  # Erweiterte Version
    
    # Verknüpfung zu Viewdaten
    view_guid: Optional[str] = None
    view_name: Optional[str] = None
    
    # Hierarchische Gruppen-Definition
    groups: Dict[str, GroupDefinition] = field(default_factory=dict)  # group_id -> GroupDefinition
    group_hierarchy: Dict[str, List[str]] = field(default_factory=dict)  # parent_id -> [child_ids]
    
    # Flexible Tab-Definitionen
    tabs: Dict[str, TabDefinition] = field(default_factory=dict)  # tab_id -> TabDefinition
    
    # Modi-Konfigurationen mit flexibler Tab-Zuordnung
    mode_configurations: Dict[int, ModeConfiguration] = field(default_factory=dict)
    
    # Standard-Einstellungen
    default_mode: int = 0
    default_grouping_style: str = "sections"
    
    # UI-Eigenschaften
    dialog_width: int = 1200  # Breiter für Multi-Tabs
    dialog_height: int = 800  # Höher für mehr Inhalt
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
    
    def add_group(self, group: GroupDefinition):
        """Fügt eine Gruppe hinzu"""
        self.groups[group.group_id] = group
        
        # Hierarchie aktualisieren
        if group.parent_group_id:
            if group.parent_group_id not in self.group_hierarchy:
                self.group_hierarchy[group.parent_group_id] = []
            self.group_hierarchy[group.parent_group_id].append(group.group_id)
    
    def add_tab(self, tab: TabDefinition):
        """Fügt einen Tab hinzu"""
        self.tabs[tab.tab_id] = tab
    
    def get_tabs_for_mode(self, mode: int) -> List[TabDefinition]:
        """Gibt alle Tabs für einen bestimmten Modus zurück"""
        mode_config = self.mode_configurations.get(mode)
        if not mode_config:
            return []
        
        result = []
        for tab_id in mode_config.mode_tabs:
            if tab_id in self.tabs:
                tab = self.tabs[tab_id]
                if tab.visible and mode in tab.visible_modes:
                    result.append(tab)
        
        # Nach tab_order sortieren
        return sorted(result, key=lambda t: t.tab_order)
    
    def get_groups_for_tab(self, tab_id: str) -> List[GroupDefinition]:
        """Gibt alle Gruppen für einen bestimmten Tab zurück"""
        tab = self.tabs.get(tab_id)
        if not tab:
            return []
        
        result = []
        for group_id in tab.assigned_groups:
            if group_id in self.groups:
                group = self.groups[group_id]
                if group.visible:
                    result.append(group)
        
        # Nach sort_order sortieren
        return sorted(result, key=lambda g: g.sort_order)
    
    def get_group_hierarchy(self, parent_group_id: str = None) -> List[GroupDefinition]:
        """Gibt die Gruppenhierarchie zurück"""
        if parent_group_id is None:
            # Root-Gruppen (ohne Parent)
            root_groups = [g for g in self.groups.values() if g.parent_group_id is None]
            return sorted(root_groups, key=lambda g: g.sort_order)
        else:
            # Untergruppen
            child_ids = self.group_hierarchy.get(parent_group_id, [])
            child_groups = [self.groups[gid] for gid in child_ids if gid in self.groups]
            return sorted(child_groups, key=lambda g: g.sort_order)
    
    def add_mode_configuration(self, mode_config: ModeConfiguration):
        """Fügt eine Modi-Konfiguration hinzu"""
        self.mode_configurations[mode_config.mode_id] = mode_config


class FlexibleFrameDataGenerator:
    """Generator für flexible Framedaten-Strukturen mit Multi-Tab-Support"""
    
    @staticmethod
    def create_datenpflege_structure(view_guid: str, view_name: str) -> FlexibleFrameStructure:
        """
        Erstellt eine flexible Struktur für Datenpflege (Modus 0) mit mehreren Tabs
        
        Beispiel: Personendaten aufgeteilt auf:
        - Tab 1: Grunddaten (Name, Adresse, Kontakt)
        - Tab 2: Finanz-/Geschäftsdaten (Umsatz, Konditionen, etc.)
        - Tab 3: Zusätzliche Informationen (Notizen, Dokumente, etc.)
        """
        
        structure = FlexibleFrameStructure(
            frame_guid=str(uuid.uuid4()),
            frame_name=f"Flexible Datenpflege für {view_name}",
            view_guid=view_guid,
            view_name=view_name
        )
        
        # === GRUPPEN DEFINIEREN ===
        
        # 1. Grunddaten-Gruppen
        basic_groups = [
            GroupDefinition(
                group_id="person_basic",
                group_name="Personen-Grunddaten",
                group_description="Name, Anrede, Titel",
                group_icon="👤",
                grouping_style="sections",
                sort_order=10,
                field_types=["text", "dropdown"],
                field_count_estimate=5
            ),
            GroupDefinition(
                group_id="address_data",
                group_name="Adressdaten",
                group_description="Straße, PLZ, Ort, Land",
                group_icon="🏠",
                grouping_style="sections",
                sort_order=20,
                field_types=["text", "dropdown"],
                field_count_estimate=8
            ),
            GroupDefinition(
                group_id="contact_data",
                group_name="Kontaktdaten",
                group_description="Telefon, E-Mail, Website",
                group_icon="📞",
                grouping_style="sections",
                sort_order=30,
                field_types=["text", "email", "url"],
                field_count_estimate=6
            )
        ]
        
        # 2. Finanz-/Geschäftsdaten-Gruppen
        business_groups = [
            GroupDefinition(
                group_id="financial_basic",
                group_name="Finanz-Grunddaten",
                group_description="Zahlungsbedingungen, Währung",
                group_icon="💰",
                grouping_style="accordion",
                sort_order=10,
                field_types=["number", "dropdown", "boolean"],
                field_count_estimate=8
            ),
            GroupDefinition(
                group_id="business_conditions",
                group_name="Geschäftskonditionen",
                group_description="Rabatte, Limits, Bedingungen",
                group_icon="📊",
                grouping_style="accordion",
                sort_order=20,
                field_types=["number", "percentage", "dropdown"],
                field_count_estimate=10
            ),
            GroupDefinition(
                group_id="accounting_data",
                group_name="Buchhaltung",
                group_description="Konten, Kostenstellen, Steuern",
                group_icon="📈",
                grouping_style="sections",
                sort_order=30,
                field_types=["text", "dropdown", "number"],
                field_count_estimate=12
            )
        ]
        
        # 3. Zusätzliche Informationen-Gruppen
        additional_groups = [
            GroupDefinition(
                group_id="notes_comments",
                group_name="Notizen & Kommentare",
                group_description="Interne Notizen, Kommentare",
                group_icon="📝",
                grouping_style="sections",
                sort_order=10,
                field_types=["textarea", "richtext"],
                field_count_estimate=3
            ),
            GroupDefinition(
                group_id="documents_files",
                group_name="Dokumente & Dateien",
                group_description="Angehängte Dokumente",
                group_icon="📎",
                grouping_style="sections",
                sort_order=20,
                field_types=["file", "url"],
                field_count_estimate=4
            ),
            GroupDefinition(
                group_id="system_data",
                group_name="System-Daten",
                group_description="Erstellt, Geändert, Status",
                group_icon="⚙️",
                grouping_style="inline",
                sort_order=30,
                field_types=["datetime", "text", "readonly"],
                field_count_estimate=6
            )
        ]
        
        # Alle Gruppen hinzufügen
        all_groups = basic_groups + business_groups + additional_groups
        for group in all_groups:
            structure.add_group(group)
        
        # === TABS DEFINIEREN ===
        
        tabs = [
            # View-Tab (immer vorhanden)
            TabDefinition(
                tab_id="view_tab",
                tab_name="Ansicht",
                tab_type="view",
                tab_order=1,
                tab_icon="👁️",
                view_guid=view_guid,
                start_tab=True,
                tab_grouping_style="sections",
                visible_modes=[0]
            ),
            
            # Tab 1: Grunddaten
            TabDefinition(
                tab_id="grunddaten_tab",
                tab_name="Grunddaten",
                tab_type="inputframe",
                tab_order=2,
                tab_icon="👤",
                assigned_groups=["person_basic", "address_data", "contact_data"],
                primary_group="person_basic",
                tab_grouping_style="sections",
                columns=2,  # 2-spaltig für bessere Übersicht
                visible_modes=[0]
            ),
            
            # Tab 2: Geschäftsdaten
            TabDefinition(
                tab_id="geschaeft_tab",
                tab_name="Geschäftsdaten",
                tab_type="inputframe",
                tab_order=3,
                tab_icon="💼",
                assigned_groups=["financial_basic", "business_conditions", "accounting_data"],
                primary_group="financial_basic",
                tab_grouping_style="accordion",  # Aufklappbar für bessere Organisation
                visible_modes=[0]
            ),
            
            # Tab 3: Zusätzliches
            TabDefinition(
                tab_id="zusaetzlich_tab",
                tab_name="Zusätzliches",
                tab_type="inputframe",
                tab_order=4,
                tab_icon="📋",
                assigned_groups=["notes_comments", "documents_files", "system_data"],
                primary_group="notes_comments",
                tab_grouping_style="sections",
                visible_modes=[0]
            )
        ]
        
        # Tabs hinzufügen
        for tab in tabs:
            structure.add_tab(tab)
        
        # === MODUS-KONFIGURATION ===
        
        mode_config = ModeConfiguration(
            mode_id=0,
            mode_tabs=["view_tab", "grunddaten_tab", "geschaeft_tab", "zusaetzlich_tab"],
            default_start_tab="view_tab",
            tab_organization="horizontal",
            allow_tab_reordering=True,
            show_tab_icons=True,
            tab_style="standard"
        )
        structure.add_mode_configuration(mode_config)
        
        return structure
    
    @staticmethod
    def create_frame_pflege_structure(view_guid: str, view_name: str) -> FlexibleFrameStructure:
        """
        Erstellt eine flexible Struktur für Frame-Pflege (Modus 1) mit mehreren Tabs
        
        Beispiel: Frame-Verwaltung aufgeteilt auf:
        - Tab 1: Frame-Definition (Basis-Eigenschaften)
        - Tab 2: Tab-Verwaltung (Tab-Definitionen, Reihenfolge)
        - Tab 3: Gruppen-Verwaltung (Gruppen-Definitionen, Hierarchie)
        - Tab 4: IC-Konfiguration (InputControl-Parameter)
        """
        
        structure = FlexibleFrameStructure(
            frame_guid=str(uuid.uuid4()),
            frame_name=f"Frame-Pflege für {view_name}",
            view_guid=view_guid,
            view_name=view_name
        )
        
        # Gruppen für Frame-Pflege
        frame_groups = [
            GroupDefinition(
                group_id="frame_definition",
                group_name="Frame-Definition",
                group_icon="🏗️",
                grouping_style="sections",
                sort_order=10
            ),
            GroupDefinition(
                group_id="tab_management",
                group_name="Tab-Verwaltung",
                group_icon="🗂️",
                grouping_style="tabs",
                sort_order=20
            ),
            GroupDefinition(
                group_id="group_management",
                group_name="Gruppen-Verwaltung",
                group_icon="📁",
                grouping_style="accordion",
                sort_order=30
            ),
            GroupDefinition(
                group_id="ic_configuration",
                group_name="IC-Konfiguration",
                group_icon="⚙️",
                grouping_style="sections",
                sort_order=40
            )
        ]
        
        for group in frame_groups:
            structure.add_group(group)
        
        # Tabs für Frame-Pflege
        tabs = [
            TabDefinition(
                tab_id="view_tab",
                tab_name="Ansicht",
                tab_type="view",
                tab_order=1,
                tab_icon="👁️",
                view_guid=view_guid,
                start_tab=True,
                visible_modes=[1]
            ),
            TabDefinition(
                tab_id="frame_def_tab",
                tab_name="Frame-Definition",
                tab_type="inputframe",
                tab_order=2,
                tab_icon="🏗️",
                assigned_groups=["frame_definition"],
                visible_modes=[1]
            ),
            TabDefinition(
                tab_id="tab_mgmt_tab",
                tab_name="Tab-Verwaltung",
                tab_type="inputframe",
                tab_order=3,
                tab_icon="🗂️",
                assigned_groups=["tab_management"],
                tab_grouping_style="tabs",
                visible_modes=[1]
            ),
            TabDefinition(
                tab_id="group_mgmt_tab",
                tab_name="Gruppen-Verwaltung",
                tab_type="inputframe",
                tab_order=4,
                tab_icon="📁",
                assigned_groups=["group_management"],
                tab_grouping_style="accordion",
                visible_modes=[1]
            ),
            TabDefinition(
                tab_id="ic_config_tab",
                tab_name="IC-Konfiguration",
                tab_type="inputframe",
                tab_order=5,
                tab_icon="⚙️",
                assigned_groups=["ic_configuration"],
                visible_modes=[1]
            )
        ]
        
        for tab in tabs:
            structure.add_tab(tab)
        
        # Modus-Konfiguration
        mode_config = ModeConfiguration(
            mode_id=1,
            mode_tabs=["view_tab", "frame_def_tab", "tab_mgmt_tab", "group_mgmt_tab", "ic_config_tab"],
            default_start_tab="frame_def_tab",
            tab_organization="horizontal",
            max_tabs_count=8
        )
        structure.add_mode_configuration(mode_config)
        
        return structure
    
    @staticmethod
    def create_call_data_flexible(view_guid: str, mode: int = 0, start_tab: str = None,
                                 user_guid: str = None, language: str = "de") -> Dict[str, Any]:
        """Erstellt Call-Data für flexible Multi-Tab-Struktur"""
        
        # Struktur basierend auf Modus erstellen
        if mode == 0:
            view_name = f"Datenpflege_{view_guid[:8]}"
            frame_structure = FlexibleFrameDataGenerator.create_datenpflege_structure(view_guid, view_name)
        elif mode == 1:
            view_name = f"Frame_Pflege_{view_guid[:8]}"
            frame_structure = FlexibleFrameDataGenerator.create_frame_pflege_structure(view_guid, view_name)
        else:
            # Für andere Modi eine Standard-Struktur erstellen
            view_name = f"Standard_{view_guid[:8]}"
            frame_structure = FlexibleFrameStructure(
                frame_guid=str(uuid.uuid4()),
                frame_name=f"Standard für {view_name}",
                view_guid=view_guid,
                view_name=view_name
            )
        
        # Start-Tab bestimmen
        mode_config = frame_structure.mode_configurations.get(mode)
        if start_tab:
            selected_start_tab = start_tab
        elif mode_config and mode_config.default_start_tab:
            selected_start_tab = mode_config.default_start_tab
        else:
            available_tabs = frame_structure.get_tabs_for_mode(mode)
            selected_start_tab = available_tabs[0].tab_id if available_tabs else "view_tab"
        
        # Call-Data zusammenstellen
        call_data = {
            "user_guid": user_guid or str(uuid.uuid4()),
            "frame_guid": frame_structure.frame_guid,
            "view_guid": view_guid,
            "mode": mode,
            "start_tab": selected_start_tab,
            "language": language,
            
            # Erweiterte Framedaten-Struktur
            "framedaten": {
                "frame_info": {
                    "frame_guid": frame_structure.frame_guid,
                    "frame_name": frame_structure.frame_name,
                    "frame_version": frame_structure.frame_version,
                    "view_guid": frame_structure.view_guid,
                    "view_name": frame_structure.view_name
                },
                
                "dialog_config": {
                    "dialog_type": "flexible_multi_tab_dialog",
                    "mode": mode,
                    "default_width": frame_structure.dialog_width,
                    "default_height": frame_structure.dialog_height,
                    "resizable": frame_structure.dialog_resizable,
                    "auto_save": frame_structure.auto_save,
                    "confirm_changes": frame_structure.confirm_changes
                },
                
                # Alle verfügbaren Gruppen
                "groups": {
                    group_id: {
                        "group_id": group.group_id,
                        "group_name": group.group_name,
                        "group_description": group.group_description,
                        "group_icon": group.group_icon,
                        "parent_group_id": group.parent_group_id,
                        "sub_groups": group.sub_groups,
                        "grouping_style": group.grouping_style,
                        "sort_order": group.sort_order,
                        "collapsible": group.collapsible,
                        "initially_collapsed": group.initially_collapsed,
                        "field_types": group.field_types,
                        "field_count_estimate": group.field_count_estimate,
                        "visible": group.visible,
                        "enabled": group.enabled
                    }
                    for group_id, group in frame_structure.groups.items()
                },
                
                # Alle verfügbaren Tabs für diesen Modus
                "tabs": [
                    {
                        "tab_id": tab.tab_id,
                        "tab_name": tab.tab_name,
                        "tab_type": tab.tab_type,
                        "tab_order": tab.tab_order,
                        "tab_icon": tab.tab_icon,
                        "assigned_groups": tab.assigned_groups,
                        "primary_group": tab.primary_group,
                        "visible": tab.visible,
                        "enabled": tab.enabled,
                        "start_tab": tab.tab_id == selected_start_tab,
                        "view_guid": tab.view_guid,
                        "frame_guid": tab.frame_guid,
                        "tab_grouping_style": tab.tab_grouping_style,
                        "scrollable": tab.scrollable,
                        "max_height": tab.max_height,
                        "columns": tab.columns,
                        "auto_save": tab.auto_save,
                        "confirm_changes": tab.confirm_changes,
                        "read_only": tab.read_only,
                        
                        # Gruppen-Details für diesen Tab
                        "groups_detail": [
                            frame_structure.groups[group_id]
                            for group_id in tab.assigned_groups
                            if group_id in frame_structure.groups
                        ]
                    }
                    for tab in frame_structure.get_tabs_for_mode(mode)
                ],
                
                # Modus-Konfiguration
                "mode_config": {
                    "mode_id": mode,
                    "mode_name": mode_config.mode_name if mode_config else f"Modus {mode}",
                    "mode_description": mode_config.mode_description if mode_config else "",
                    "mode_icon": mode_config.mode_icon if mode_config else "❓",
                    "mode_tabs": mode_config.mode_tabs if mode_config else [],
                    "tab_organization": mode_config.tab_organization if mode_config else "horizontal",
                    "allow_tab_reordering": mode_config.allow_tab_reordering if mode_config else False,
                    "show_tab_icons": mode_config.show_tab_icons if mode_config else True,
                    "tab_style": mode_config.tab_style if mode_config else "standard",
                    "read_only": mode_config.read_only if mode_config else False,
                    "requires_admin": mode_config.requires_admin if mode_config else False
                },
                
                "database_config": {
                    "central_db_instance": frame_structure.central_db_instance,
                    "primary_table": mode_config.primary_table if mode_config else None,
                    "primary_key_field": mode_config.primary_key_field if mode_config else None
                }
            }
        }
        
        return call_data


# Demo-Funktionen
def demo_flexible_structure():
    """Demonstriert die flexible Multi-Tab-Struktur"""
    
    print("=== Flexible Multi-Tab-Struktur Demo ===")
    
    # Test-GUID für View
    test_view_guid = "12345678-1234-1234-1234-123456789abc"
    
    # Verschiedene Modi testen
    for mode in [0, 1]:
        print(f"\n--- Modus {mode} ---")
        
        try:
            call_data = FlexibleFrameDataGenerator.create_call_data_flexible(
                view_guid=test_view_guid,
                mode=mode,
                user_guid="test-user-guid"
            )
            
            framedaten = call_data["framedaten"]
            mode_config = framedaten["mode_config"]
            tabs = framedaten["tabs"]
            groups = framedaten["groups"]
            
            print(f"Modus: {mode_config['mode_name']} {mode_config['mode_icon']}")
            print(f"Beschreibung: {mode_config['mode_description']}")
            print(f"Anzahl Tabs: {len(tabs)}")
            print(f"Anzahl Gruppen: {len(groups)}")
            print(f"Start-Tab: {call_data['start_tab']}")
            print(f"Tab-Organisation: {mode_config['tab_organization']}")
            
            print("\nTab-Struktur:")
            for tab in tabs:
                start_marker = "🔸" if tab["start_tab"] else "  "
                group_count = len(tab["assigned_groups"])
                print(f"  {start_marker} {tab['tab_icon']} {tab['tab_name']} ({tab['tab_grouping_style']}) - {group_count} Gruppen")
                
                for group_id in tab["assigned_groups"]:
                    if group_id in groups:
                        group = groups[group_id]
                        field_estimate = group.get("field_count_estimate", 0)
                        print(f"      • {group.get('group_icon', '')} {group.get('group_name', '')} (~{field_estimate} Felder)")
                
        except Exception as e:
            print(f"❌ Fehler bei Modus {mode}: {e}")
    
    print("\n=== Demo abgeschlossen ===")


if __name__ == "__main__":
    demo_flexible_structure()
