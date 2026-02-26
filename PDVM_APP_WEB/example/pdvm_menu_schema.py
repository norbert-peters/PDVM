"""
V2 Menu Schema Definition
========================
Container-Struktur für das neue lineare Menüsystem.

Kern-Konzept:
- Keine Tree-Struktur mehr
- 3 getrennte Container: VERTIKAL, GRUND, ZUSATZ
- GUID-basierte Referenzierung
- Vererbung bei ZUSATZ-Menüs

Autor: PDVM V2.0
Datum: 01.11.2025
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class MenuItemType(Enum):
    """Typ eines Menü-Eintrags"""
    BUTTON = "BUTTON"           # Klickbarer Menüpunkt
    SUBMENU = "SUBMENU"         # Hat Untermenü
    SEPARATOR = "SEPARATOR"     # Trennlinie
    SPACER = "SPACER"          # Abstand


@dataclass
class MenuItem:
    """
    Einzelner Menü-Eintrag
    
    3-Ebenen Matrix-Struktur:
    - GUID: Eindeutiger Identifier (EBENE 1)
    - GUID_ABDATUM: Änderungs-Zeitstempel (EBENE 2)
    - GUID_FORMATIERT: Formatiertes AB-Datum (EBENE 3)
    """
    # Pflichtfelder
    GUID: str                           # Eindeutige ID des Menüpunkts
    TYPE: MenuItemType                  # Typ (BUTTON, SUBMENU, etc.)
    LABEL: str                          # Anzeigetext
    SORT_ORDER: int                     # Reihenfolge
    
    # Optionale Felder
    ICON: Optional[str] = None          # Icon-Pfad oder Name
    COMMAND_GUID: Optional[str] = None  # Verknüpfter Command
    ZUSATZ_GUID: Optional[str] = None   # Zusatzmenü für diesen Punkt
    PARENT_GUID: Optional[str] = None   # Parent für Submenüs
    TEMPLATE_GUID: Optional[str] = None # Template-GUID für SPACER Items
    VISIBLE: bool = True                # Sichtbarkeit
    ENABLED: bool = True                # Aktiviert/Deaktiviert
    TOOLTIP: Optional[str] = None       # Tooltip-Text
    
    # 3-Ebenen Matrix für AB-Datum
    ABDATUM: Optional[float] = None              # EBENE 2
    FORMATIERTES_ABDATUM: Optional[str] = None   # EBENE 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für Speicherung"""
        return {
            'GUID': self.GUID,
            'TYPE': self.TYPE.value,
            'LABEL': self.LABEL,
            'SORT_ORDER': self.SORT_ORDER,
            'ICON': self.ICON,
            'COMMAND_GUID': self.COMMAND_GUID,
            'ZUSATZ_GUID': self.ZUSATZ_GUID,
            'PARENT_GUID': self.PARENT_GUID,
            'TEMPLATE_GUID': self.TEMPLATE_GUID,
            'VISIBLE': self.VISIBLE,
            'ENABLED': self.ENABLED,
            'TOOLTIP': self.TOOLTIP,
            'ABDATUM': self.ABDATUM,
            'FORMATIERTES_ABDATUM': self.FORMATIERTES_ABDATUM
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MenuItem':
        """Erstellt MenuItem aus Dictionary"""
        return MenuItem(
            GUID=data['GUID'],
            TYPE=MenuItemType(data['TYPE']),
            LABEL=data['LABEL'],
            SORT_ORDER=data['SORT_ORDER'],
            ICON=data.get('ICON'),
            COMMAND_GUID=data.get('COMMAND_GUID'),
            ZUSATZ_GUID=data.get('ZUSATZ_GUID'),
            PARENT_GUID=data.get('PARENT_GUID'),
            TEMPLATE_GUID=data.get('TEMPLATE_GUID'),
            VISIBLE=data.get('VISIBLE', True),
            ENABLED=data.get('ENABLED', True),
            TOOLTIP=data.get('TOOLTIP'),
            ABDATUM=data.get('ABDATUM'),
            FORMATIERTES_ABDATUM=data.get('FORMATIERTES_ABDATUM')
        )


@dataclass
class MenuCommand:
    """
    Command-Definition mit Security Profile Alternativen
    
    Standard: 888... GUID → Alle dürfen
    Alternativen: Liste von sec-profile GUIDs
    """
    GUID: str                           # Command GUID
    NAME: str                           # Command Name
    HANDLER: str                        # Handler-Funktion (z.B. "open_view")
    PARAMS: Dict[str, Any] = field(default_factory=dict)  # Parameter
    
    # Security
    SEC_PROFILE_DEFAULT: str = "88888888-8888-8888-8888-888888888888"
    SEC_PROFILES: List[str] = field(default_factory=list)  # Alternative GUIDs
    
    # 3-Ebenen Matrix
    ABDATUM: Optional[float] = None
    FORMATIERTES_ABDATUM: Optional[str] = None
    
    def is_allowed_for_user(self, user_sec_profiles: List[str]) -> bool:
        """
        Prüft ob User Command ausführen darf
        
        Standard-GUID (888...) → Immer erlaubt
        Sonst: Mindestens ein Profil muss matchen
        """
        if self.SEC_PROFILE_DEFAULT.startswith("88888888"):
            return True
        
        # Prüfe ob User eines der benötigten Profile hat
        return any(profile in user_sec_profiles for profile in self.SEC_PROFILES)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'GUID': self.GUID,
            'NAME': self.NAME,
            'HANDLER': self.HANDLER,
            'PARAMS': self.PARAMS,
            'SEC_PROFILE_DEFAULT': self.SEC_PROFILE_DEFAULT,
            'SEC_PROFILES': self.SEC_PROFILES,
            'ABDATUM': self.ABDATUM,
            'FORMATIERTES_ABDATUM': self.FORMATIERTES_ABDATUM
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MenuCommand':
        """Erstellt MenuCommand aus Dictionary"""
        return MenuCommand(
            GUID=data['GUID'],
            NAME=data['NAME'],
            HANDLER=data['HANDLER'],
            PARAMS=data.get('PARAMS', {}),
            SEC_PROFILE_DEFAULT=data.get('SEC_PROFILE_DEFAULT', 
                                        "88888888-8888-8888-8888-888888888888"),
            SEC_PROFILES=data.get('SEC_PROFILES', []),
            ABDATUM=data.get('ABDATUM'),
            FORMATIERTES_ABDATUM=data.get('FORMATIERTES_ABDATUM')
        )


@dataclass
class MenuContainer:
    """
    Container für ein komplettes Menü
    
    Struktur in man_db (sys_menudaten):
    {
        "VERTIKAL": [MenuItem, ...],
        "GRUND": [MenuItem, ...],
        "ZUSATZ": [MenuItem, ...],
        "COMMANDS": [MenuCommand, ...]
    }
    """
    MENU_GUID: str                      # Menü-GUID
    MENU_NAME: str                      # Menü-Name
    
    VERTIKAL: List[MenuItem] = field(default_factory=list)
    GRUND: List[MenuItem] = field(default_factory=list)
    ZUSATZ: List[MenuItem] = field(default_factory=list)
    COMMANDS: List[MenuCommand] = field(default_factory=list)
    
    # Metadata
    IS_STARTMENU: bool = False          # Ist dies das Startmenü?
    DESCRIPTION: Optional[str] = None
    
    # 3-Ebenen Matrix
    ABDATUM: Optional[float] = None
    FORMATIERTES_ABDATUM: Optional[str] = None
    
    def get_item_by_guid(self, item_guid: str) -> Optional[MenuItem]:
        """Findet MenuItem über alle Container hinweg"""
        for item in self.VERTIKAL + self.GRUND + self.ZUSATZ:
            if item.GUID == item_guid:
                return item
        return None
    
    def get_command_by_guid(self, command_guid: str) -> Optional[MenuCommand]:
        """Findet MenuCommand über GUID"""
        for cmd in self.COMMANDS:
            if cmd.GUID == command_guid:
                return cmd
        return None
    
    def get_zusatz_for_item(self, item_guid: str) -> List[MenuItem]:
        """
        Holt Zusatzmenü für einen Menüpunkt
        
        Vererbung:
        1. Prüfe ob Item eigenes ZUSATZ_GUID hat
        2. Wenn nicht, traversiere Parents aufwärts
        3. Erstes gefundenes ZUSATZ_GUID wird verwendet
        """
        item = self.get_item_by_guid(item_guid)
        if not item:
            return []
        
        # Suche ZUSATZ_GUID (mit Vererbung)
        zusatz_guid = self._find_zusatz_guid_inherited(item)
        if not zusatz_guid:
            return []
        
        # Filtere ZUSATZ-Items mit diesem Parent
        zusatz_items = [
            z for z in self.ZUSATZ 
            if z.PARENT_GUID == zusatz_guid
        ]
        
        # Sortiere nach SORT_ORDER
        return sorted(zusatz_items, key=lambda x: x.SORT_ORDER)
    
    def _find_zusatz_guid_inherited(self, item: MenuItem) -> Optional[str]:
        """
        Findet ZUSATZ_GUID mit Vererbung
        
        Traversiert Parent-Kette aufwärts bis ZUSATZ_GUID gefunden
        """
        current = item
        max_depth = 20  # Schutz vor Endlosschleife
        depth = 0
        
        while current and depth < max_depth:
            if current.ZUSATZ_GUID:
                return current.ZUSATZ_GUID
            
            # Gehe zu Parent
            if current.PARENT_GUID:
                current = self.get_item_by_guid(current.PARENT_GUID)
            else:
                break
            
            depth += 1
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary für Speicherung"""
        return {
            'MENU_GUID': self.MENU_GUID,
            'MENU_NAME': self.MENU_NAME,
            'VERTIKAL': [item.to_dict() for item in self.VERTIKAL],
            'GRUND': [item.to_dict() for item in self.GRUND],
            'ZUSATZ': [item.to_dict() for item in self.ZUSATZ],
            'COMMANDS': [cmd.to_dict() for cmd in self.COMMANDS],
            'IS_STARTMENU': self.IS_STARTMENU,
            'DESCRIPTION': self.DESCRIPTION,
            'ABDATUM': self.ABDATUM,
            'FORMATIERTES_ABDATUM': self.FORMATIERTES_ABDATUM
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MenuContainer':
        """Erstellt MenuContainer aus Dictionary"""
        return MenuContainer(
            MENU_GUID=data['MENU_GUID'],
            MENU_NAME=data['MENU_NAME'],
            VERTIKAL=[MenuItem.from_dict(i) for i in data.get('VERTIKAL', [])],
            GRUND=[MenuItem.from_dict(i) for i in data.get('GRUND', [])],
            ZUSATZ=[MenuItem.from_dict(i) for i in data.get('ZUSATZ', [])],
            COMMANDS=[MenuCommand.from_dict(c) for c in data.get('COMMANDS', [])],
            IS_STARTMENU=data.get('IS_STARTMENU', False),
            DESCRIPTION=data.get('DESCRIPTION'),
            ABDATUM=data.get('ABDATUM'),
            FORMATIERTES_ABDATUM=data.get('FORMATIERTES_ABDATUM')
        )


# ===== HELPER FUNCTIONS =====

def create_menu_item(
    guid: str,
    label: str,
    item_type: MenuItemType = MenuItemType.BUTTON,
    sort_order: int = 0,
    **kwargs
) -> MenuItem:
    """
    Helper-Funktion zum einfachen Erstellen von MenuItems
    
    Beispiel:
        item = create_menu_item(
            "guid-123",
            "Personen",
            MenuItemType.BUTTON,
            sort_order=1,
            command_guid="cmd-guid-456",
            icon="person.png"
        )
    """
    return MenuItem(
        GUID=guid,
        TYPE=item_type,
        LABEL=label,
        SORT_ORDER=sort_order,
        **kwargs
    )


def create_command(
    guid: str,
    name: str,
    handler: str,
    params: Optional[Dict[str, Any]] = None,
    sec_profiles: Optional[List[str]] = None
) -> MenuCommand:
    """
    Helper-Funktion zum einfachen Erstellen von MenuCommands
    
    Beispiel:
        cmd = create_command(
            "cmd-guid-123",
            "open_personen_view",
            "open_view",
            params={'view_guid': 'view-123'},
            sec_profiles=['sec-guid-admin']
        )
    """
    return MenuCommand(
        GUID=guid,
        NAME=name,
        HANDLER=handler,
        PARAMS=params or {},
        SEC_PROFILES=sec_profiles or []
    )


if __name__ == "__main__":
    # ===== TEST =====
    print("🧪 V2 Menu Schema Test")
    print("=" * 60)
    
    # Test MenuItem
    item = create_menu_item(
        "item-001",
        "Personen",
        MenuItemType.BUTTON,
        sort_order=1,
        COMMAND_GUID="cmd-001",
        ICON="person.png",
        TOOLTIP="Personenverwaltung öffnen"
    )
    print(f"\n✅ MenuItem erstellt: {item.LABEL}")
    print(f"   Type: {item.TYPE.value}")
    print(f"   Command: {item.COMMAND_GUID}")
    
    # Test MenuCommand
    cmd = create_command(
        "cmd-001",
        "open_personen",
        "open_view",
        params={'view_guid': 'view-personen-123'},
        sec_profiles=['sec-admin', 'sec-user']
    )
    print(f"\n✅ MenuCommand erstellt: {cmd.NAME}")
    print(f"   Handler: {cmd.HANDLER}")
    print(f"   Security Profiles: {cmd.SEC_PROFILES}")
    
    # Test MenuContainer
    container = MenuContainer(
        MENU_GUID="menu-main",
        MENU_NAME="Hauptmenü",
        VERTIKAL=[item],
        COMMANDS=[cmd]
    )
    print(f"\n✅ MenuContainer erstellt: {container.MENU_NAME}")
    print(f"   VERTIKAL Items: {len(container.VERTIKAL)}")
    print(f"   Commands: {len(container.COMMANDS)}")
    
    # Test Serialisierung
    data = container.to_dict()
    restored = MenuContainer.from_dict(data)
    print(f"\n✅ Serialisierung/Deserialisierung erfolgreich")
    print(f"   Original GUID: {container.MENU_GUID}")
    print(f"   Restored GUID: {restored.MENU_GUID}")
    
    # Test Vererbung
    parent_item = create_menu_item(
        "item-parent",
        "Stammdaten",
        MenuItemType.SUBMENU,
        sort_order=1,
        ZUSATZ_GUID="zusatz-001"
    )
    child_item = create_menu_item(
        "item-child",
        "Personen",
        MenuItemType.BUTTON,
        sort_order=1,
        PARENT_GUID="item-parent"
    )
    container2 = MenuContainer(
        MENU_GUID="menu-test",
        MENU_NAME="Test",
        GRUND=[parent_item, child_item]
    )
    inherited_zusatz = container2._find_zusatz_guid_inherited(child_item)
    print(f"\n✅ Vererbung Test:")
    print(f"   Parent ZUSATZ_GUID: {parent_item.ZUSATZ_GUID}")
    print(f"   Child inherited: {inherited_zusatz}")
    
    print("\n" + "=" * 60)
    print("🎯 Schema Definition Complete!")
