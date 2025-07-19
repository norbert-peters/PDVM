#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InputControl-Integration für universelle Tab-Dialog-Architektur
Erweitert das bestehende InputControl-System um Tab-basierte Modi
"""

from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InputControlConfig:
    """Erweiterte InputControl-Konfiguration für Tab-Dialog"""
    
    # Basis-Konfiguration
    field_key: str
    ic_type: str = "text"
    label: str = ""
    tooltip: str = ""
    required: bool = False
    readonly: bool = False
    visible: bool = True
    
    # Erweiterte Tab-Dialog-Features
    tab_id: str = ""  # Zu welchem Tab gehört das Feld
    group_id: str = ""  # Zu welcher Gruppe gehört das Feld
    grouping_style: str = "sections"  # Wie wird die Gruppe dargestellt
    
    # Zugriffskontrolle auf IC-Ebene
    access_control: Dict[str, Any] = field(default_factory=dict)
    mode_visibility: List[int] = field(default_factory=list)  # In welchen Modi sichtbar
    
    # Standard IC-Parameter
    historical: bool = True
    display_ti_ab_short: bool = True
    display_ti_val_short: bool = False
    abdatum: bool = True
    conversion_in: Optional[str] = None
    conversion_out: Optional[str] = None
    ui_width_label: Optional[int] = None
    ui_width_value: Optional[int] = None
    ui_indent: int = 0
    
    # Dropdown/ViewTable
    dropdown_config: Dict[str, str] = field(default_factory=dict)
    viewtable_config: Dict[str, str] = field(default_factory=dict)
    help_config: Dict[str, str] = field(default_factory=dict)


class UniversalInputControlManager:
    """
    Manager für InputControl in der universellen Tab-Dialog-Architektur
    
    Konzept:
    1. Alle Datenpflege über InputControl (einheitlich)
    2. Zugriffsberechtigung über Frame-/Menü-Ebene
    3. IC-Parameter können Feld-Level-Rechte steuern
    """
    
    def __init__(self):
        self.ic_configurations: Dict[str, InputControlConfig] = {}
        self.mode_configurations: Dict[int, Dict[str, Any]] = {}
        self.access_policies: Dict[str, Any] = {}
    
    def register_ic_config(self, field_key: str, config: InputControlConfig):
        """Registriert eine InputControl-Konfiguration"""
        self.ic_configurations[field_key] = config
        logger.debug(f"IC-Konfiguration registriert: {field_key}")
    
    def get_ic_config_for_mode(self, mode: int, tab_id: str = None) -> Dict[str, InputControlConfig]:
        """
        Gibt IC-Konfigurationen für einen bestimmten Modus zurück
        
        Args:
            mode: Dialog-Modus (0-5)
            tab_id: Optional spezifischer Tab
        
        Returns:
            Dict von field_key -> InputControlConfig
        """
        result = {}
        
        for field_key, config in self.ic_configurations.items():
            # Modus-Sichtbarkeit prüfen
            if config.mode_visibility and mode not in config.mode_visibility:
                continue
            
            # Tab-Filter prüfen
            if tab_id and config.tab_id and config.tab_id != tab_id:
                continue
            
            # Zugriffskontrolle prüfen
            if not self.check_field_access(field_key, mode):
                continue
            
            result[field_key] = config
        
        return result
    
    def check_field_access(self, field_key: str, mode: int) -> bool:
        """
        Prüft Zugriff auf ein Feld basierend auf Modus und Berechtigung
        
        Args:
            field_key: Feld-Schlüssel
            mode: Dialog-Modus
        
        Returns:
            True wenn Zugriff erlaubt
        """
        config = self.ic_configurations.get(field_key)
        if not config:
            return False
        
        # Basis-Sichtbarkeit
        if not config.visible:
            return False
        
        # Zugriffskontrolle aus IC-Konfiguration
        access_control = config.access_control
        
        # Admin-Modi prüfen
        if mode in [1, 2, 3, 5] and access_control.get("requires_admin", False):
            # Hier würde echte Admin-Prüfung stattfinden
            return True  # Für Demo erlauben
        
        # Standard-Zugriff
        return True
    
    def apply_access_policy(self, field_key: str, mode: int, user_permissions: Dict[str, Any] = None):
        """
        Wendet Zugriffs-Policy auf ein Feld an
        
        Args:
            field_key: Feld-Schlüssel
            mode: Dialog-Modus
            user_permissions: Benutzer-Berechtigungen
        """
        config = self.ic_configurations.get(field_key)
        if not config:
            return
        
        # Beispiel-Policies basierend auf Modus
        if mode == 0:  # Datenpflege
            # Standard-Berechtigung
            pass
        elif mode == 1:  # Frame-Pflege
            # Nur Admin darf Frame-Struktur ändern
            if not user_permissions or not user_permissions.get("is_admin", False):
                config.readonly = True
        elif mode in [2, 3, 5]:  # System-Modi
            # System-relevante Felder nur für Admin
            if field_key.startswith("system_"):
                if not user_permissions or not user_permissions.get("is_admin", False):
                    config.visible = False
        elif mode == 4:  # User-Settings
            # Benutzer kann nur eigene Einstellungen ändern
            if field_key.startswith("global_"):
                config.readonly = True
    
    def generate_ic_for_universal_dialog(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generiert IC-Konfiguration für universellen Dialog
        
        Args:
            call_data: Call-Data des universellen Dialogs
        
        Returns:
            IC-Konfiguration als Dict
        """
        mode = call_data.get("mode", 0)
        framedaten = call_data.get("framedaten", {})
        tabs = framedaten.get("tabs", [])
        
        ic_config = {}
        
        # Für jeden Tab IC-Konfigurationen generieren
        for tab_config in tabs:
            tab_id = tab_config["tab_id"]
            tab_type = tab_config["tab_type"]
            
            if tab_type == "inputframe":
                # InputFrame-spezifische IC-Konfiguration
                tab_ic_config = self.generate_ic_for_tab(tab_config, mode)
                ic_config.update(tab_ic_config)
            elif tab_type == "view":
                # View-spezifische IC-Konfiguration (falls nötig)
                view_ic_config = self.generate_ic_for_view(tab_config, mode)
                ic_config.update(view_ic_config)
        
        return ic_config
    
    def generate_ic_for_tab(self, tab_config: Dict[str, Any], mode: int) -> Dict[str, Any]:
        """Generiert IC-Konfiguration für einen spezifischen Tab"""
        
        tab_id = tab_config["tab_id"]
        grouping_style = tab_config.get("grouping_style", "sections")
        
        ic_config = {}
        
        # Modus-spezifische Feld-Generierung
        if tab_id == "data_maintenance":
            ic_config.update(self.generate_data_maintenance_ic(grouping_style))
        elif tab_id == "frame_maintenance":
            ic_config.update(self.generate_frame_maintenance_ic(grouping_style))
        elif tab_id == "menu_maintenance":
            ic_config.update(self.generate_menu_maintenance_ic(grouping_style))
        elif tab_id == "user_maintenance":
            ic_config.update(self.generate_user_maintenance_ic(grouping_style))
        
        return ic_config
    
    def generate_ic_for_view(self, tab_config: Dict[str, Any], mode: int) -> Dict[str, Any]:
        """Generiert IC-Konfiguration für View-Tab"""
        
        # View-Tabs haben normalerweise keine IC-Konfiguration
        # Können aber Filter-/Such-Felder haben
        return {}
    
    def generate_data_maintenance_ic(self, grouping_style: str) -> Dict[str, Any]:
        """Generiert IC für Datenpflege-Tab"""
        
        return {
            "grunddaten_name": {
                "source_path": "root",
                "historical": True,
                "label": "Name",
                "type": "text",
                "required": True,
                "group_id": "grunddaten",
                "grouping_style": grouping_style,
                "ui_width_label": 100,
                "ui_width_value": 200
            },
            "grunddaten_beschreibung": {
                "source_path": "root",
                "historical": True,
                "label": "Beschreibung",
                "type": "textarea",
                "group_id": "grunddaten",
                "grouping_style": grouping_style,
                "ui_width_value": 300
            },
            "erweitert_kategorie": {
                "source_path": "root",
                "historical": True,
                "label": "Kategorie",
                "type": "dropdown",
                "group_id": "erweiterte_daten",
                "grouping_style": grouping_style,
                "dropdown": {
                    "table": "kategorien",
                    "key": "kategorie_id",
                    "value": "kategorie_name"
                }
            }
        }
    
    def generate_frame_maintenance_ic(self, grouping_style: str) -> Dict[str, Any]:
        """Generiert IC für Frame-Pflege-Tab"""
        
        return {
            "frame_guid": {
                "source_path": "root",
                "historical": False,
                "label": "Frame GUID",
                "type": "text",
                "readonly": True,
                "group_id": "frame_definition",
                "grouping_style": grouping_style
            },
            "frame_name": {
                "source_path": "root",
                "historical": False,
                "label": "Frame Name",
                "type": "text",
                "required": True,
                "group_id": "frame_definition",
                "grouping_style": grouping_style
            },
            "default_grouping": {
                "source_path": "root",
                "historical": False,
                "label": "Standard-Gruppierung",
                "type": "dropdown",
                "group_id": "tab_config",
                "grouping_style": grouping_style,
                "dropdown": {
                    "static_values": {
                        "sections": "Bereiche",
                        "accordion": "Aufklappbar",
                        "tabs": "Tabs",
                        "inline": "Linear"
                    }
                }
            }
        }
    
    def generate_menu_maintenance_ic(self, grouping_style: str) -> Dict[str, Any]:
        """Generiert IC für Menü-Pflege-Tab"""
        
        return {
            "menu_id": {
                "source_path": "root",
                "historical": False,
                "label": "Menü ID",
                "type": "text",
                "required": True,
                "group_id": "menu_basic",
                "grouping_style": grouping_style
            },
            "menu_title": {
                "source_path": "root",
                "historical": False,
                "label": "Menü Titel",
                "type": "text",
                "required": True,
                "group_id": "menu_basic",
                "grouping_style": grouping_style
            },
            "requires_admin": {
                "source_path": "root",
                "historical": False,
                "label": "Erfordert Admin",
                "type": "boolean",
                "group_id": "menu_permissions",
                "grouping_style": grouping_style
            }
        }
    
    def generate_user_maintenance_ic(self, grouping_style: str) -> Dict[str, Any]:
        """Generiert IC für Benutzer-Pflege-Tab"""
        
        return {
            "username": {
                "source_path": "root",
                "historical": False,
                "label": "Benutzername",
                "type": "text",
                "required": True,
                "group_id": "user_basic",
                "grouping_style": grouping_style
            },
            "email": {
                "source_path": "root",
                "historical": False,
                "label": "E-Mail",
                "type": "text",
                "required": True,
                "group_id": "user_basic",
                "grouping_style": grouping_style
            },
            "role": {
                "source_path": "root",
                "historical": False,
                "label": "Rolle",
                "type": "dropdown",
                "group_id": "user_basic",
                "grouping_style": grouping_style,
                "dropdown": {
                    "static_values": {
                        "user": "Benutzer",
                        "admin": "Administrator",
                        "developer": "Entwickler"
                    }
                }
            },
            "active": {
                "source_path": "root",
                "historical": False,
                "label": "Aktiv",
                "type": "boolean",
                "group_id": "user_settings",
                "grouping_style": grouping_style
            }
        }


def create_universal_ic_manager() -> UniversalInputControlManager:
    """
    Erstellt einen konfigurierten UniversalInputControlManager
    
    Returns:
        Konfigurierter Manager mit Standard-IC-Konfigurationen
    """
    manager = UniversalInputControlManager()
    
    # Standard-IC-Konfigurationen registrieren würde hier passieren
    # Für Demo verwenden wir die generate_*_ic Methoden
    
    logger.info("UniversalInputControlManager erstellt und konfiguriert")
    return manager


# Demo-Funktion
def demo_universal_ic():
    """Demonstriert die universelle IC-Integration"""
    
    print("=== Universelle InputControl-Integration Demo ===")
    
    manager = create_universal_ic_manager()
    
    # Test-Call-Data
    call_data = {
        "mode": 0,
        "framedaten": {
            "tabs": [
                {
                    "tab_id": "data_maintenance",
                    "tab_type": "inputframe",
                    "grouping_style": "sections"
                }
            ]
        }
    }
    
    # IC-Konfiguration generieren
    ic_config = manager.generate_ic_for_universal_dialog(call_data)
    
    print(f"\nGenerierte IC-Konfiguration für Modus {call_data['mode']}:")
    print(f"Anzahl Felder: {len(ic_config)}")
    
    for field_key, field_config in ic_config.items():
        print(f"  • {field_key}: {field_config.get('label', '')} ({field_config.get('type', '')})")
        if field_config.get('group_id'):
            print(f"    Gruppe: {field_config['group_id']} ({field_config.get('grouping_style', '')})")
    
    print("\n=== Demo abgeschlossen ===")


if __name__ == "__main__":
    demo_universal_ic()
