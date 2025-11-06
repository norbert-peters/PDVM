"""
PDVM Menü-Kommandos Update - Flexible und übersetzbare Struktur
==============================================================

Dieses Skript aktualisiert die Menü-Kommando-Struktur für flexiblere,
übersetzbare und besser wartbare Dialog-Funktionen.

Features:
- Einfache Kommandos ohne Emojis (übersetzbar)
- Unterstützung für dialog_zusatz() Methode
- Rückwärtskompatibilität mit bestehenden Emoji-Kommandos
- Erweiterte parameterisierte Kommandos

Author: Generated for MyApplication
Date: 2024
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def update_menu_commands_flexible():
    """
    Aktualisiert die Menü-Kommando-Struktur für mehr Flexibilität.
    
    Neue Struktur:
    1. Einfache Dialog_XXX Kommandos (ohne Emojis)
    2. dialog_zusatz('XXX') Integration  
    3. Parameterisierte Kommandos
    4. Rückwärtskompatibilität
    """
    
    # === NEUE FLEXIBLE KOMMANDO-STRUKTUR ===
    flexible_commands = {
        # === BASIS-DIALOG-KOMMANDOS (einfach, übersetzbar) ===
        "Dialog_Input-Lupe": {
            "code": "self.dialog_zusatz('Input-Lupe')",
            "description": "Aktiviert Input-Lupe Modus",
            "category": "Dialog-Steuerung",
            "translatable": True
        },
        
        "Dialog_View-Lupe": {
            "code": "self.dialog_zusatz('View-Lupe')",
            "description": "Aktiviert View-Lupe Modus", 
            "category": "Dialog-Steuerung",
            "translatable": True
        },
        
        "Dialog_Position-Normal": {
            "code": "self.dialog_zusatz('Position-Normal')",
            "description": "Setzt normale Position zurück",
            "category": "Dialog-Steuerung",
            "translatable": True
        },
        
        "Dialog_Speichern": {
            "code": "self.dialog_zusatz('Speichern')",
            "description": "Speichert aktuelle Daten",
            "category": "Daten-Management",
            "translatable": True
        },
        
        "Dialog_Export": {
            "code": "self.dialog_zusatz('Export')",
            "description": "Exportiert Daten",
            "category": "Daten-Management", 
            "translatable": True
        },
        
        "Dialog_Refresh": {
            "code": "self.dialog_zusatz('Refresh')",
            "description": "Aktualisiert View",
            "category": "Ansicht",
            "translatable": True
        },
        
        "Dialog_Menu-Toggle": {
            "code": "self.dialog_zusatz('Menu-Toggle')",
            "description": "Toggelt Menü-Sichtbarkeit",
            "category": "Interface",
            "translatable": True
        },
        
        "Dialog_Stichtag": {
            "code": "self.dialog_zusatz('Stichtag')",
            "description": "Wechselt Stichtag",
            "category": "Daten-Filter",
            "translatable": True
        },
        
        # === ERWEITERTE KOMMANDOS ===
        "Dialog_Layout-Reset": {
            "code": "self.dialog_zusatz('Layout', action='reset')",
            "description": "Setzt Layout zurück",
            "category": "Layout",
            "translatable": True
        },
        
        "Dialog_Vollbild": {
            "code": "self.dialog_zusatz('Layout', action='fullscreen')",
            "description": "Toggelt Vollbild-Modus",
            "category": "Layout",
            "translatable": True
        },
        
        # === PARAMETERISIERTE KOMMANDOS (Beispiele) ===
        "Dialog_Lupe-Input": {
            "code": "self.dialog_zusatz('Lupe', mode='input')",
            "description": "Lupe mit Input-Parameter",
            "category": "Dialog-Steuerung",
            "translatable": True
        },
        
        "Dialog_Lupe-View": {
            "code": "self.dialog_zusatz('Lupe', mode='view')",
            "description": "Lupe mit View-Parameter",
            "category": "Dialog-Steuerung",
            "translatable": True
        },
        
        "Dialog_Daten-Save": {
            "code": "self.dialog_zusatz('Dialog', action='save')",
            "description": "Dialog-Aktion: Speichern",
            "category": "Daten-Management",
            "translatable": True
        },
        
        "Dialog_Daten-Export": {
            "code": "self.dialog_zusatz('Dialog', action='export')",
            "description": "Dialog-Aktion: Export",
            "category": "Daten-Management",
            "translatable": True
        },
    }
    
    # === LEGACY-KOMPATIBILITÄT (mit Emojis) ===
    legacy_commands = {
        "Dialog_🔍 View-Lupe": {
            "code": "self.dialog_zusatz('View-Lupe')",
            "description": "Aktiviert View-Lupe (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
        
        "Dialog_📝 Input-Lupe": {
            "code": "self.dialog_zusatz('Input-Lupe')",
            "description": "Aktiviert Input-Lupe (Legacy)",
            "category": "Legacy", 
            "translatable": False
        },
        
        "Dialog_⚖️ Position wiederherstellen": {
            "code": "self.dialog_zusatz('Position-Normal')",
            "description": "Position zurücksetzen (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
        
        "Dialog_💾 Daten speichern": {
            "code": "self.dialog_zusatz('Speichern')",
            "description": "Daten speichern (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
        
        "Dialog_📊 Daten exportieren": {
            "code": "self.dialog_zusatz('Export')",
            "description": "Daten exportieren (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
        
        "Dialog_🔄 View refreshen": {
            "code": "self.dialog_zusatz('Refresh')",
            "description": "View aktualisieren (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
        
        "Dialog_🎛️ Menü ausblenden": {
            "code": "self.dialog_zusatz('Menu-Toggle')",
            "description": "Menü toggeln (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
        
        "Dialog_🗓️ Stichtag wechseln": {
            "code": "self.dialog_zusatz('Stichtag')",
            "description": "Stichtag wechseln (Legacy)",
            "category": "Legacy",
            "translatable": False
        },
    }
    
    # === KOMBINIERTE KOMMANDO-LISTE ===
    all_commands = {**flexible_commands, **legacy_commands}
    
    logger.info(f"Flexible Menü-Kommando-Struktur erstellt:")
    logger.info(f"- Flexible Kommandos: {len(flexible_commands)}")
    logger.info(f"- Legacy Kommandos: {len(legacy_commands)}")
    logger.info(f"- Gesamt: {len(all_commands)}")
    
    return all_commands


def get_translatable_commands(all_commands: Dict) -> Dict:
    """
    Filtert übersetzbare Kommandos.
    
    Args:
        all_commands: Alle verfügbaren Kommandos
        
    Returns:
        Dict: Nur übersetzbare Kommandos
    """
    translatable = {
        name: cmd for name, cmd in all_commands.items() 
        if cmd.get('translatable', False)
    }
    
    logger.info(f"Übersetzbare Kommandos: {len(translatable)}")
    return translatable


def get_commands_by_category(all_commands: Dict, category: str) -> Dict:
    """
    Filtert Kommandos nach Kategorie.
    
    Args:
        all_commands: Alle verfügbaren Kommandos
        category: Gewünschte Kategorie
        
    Returns:
        Dict: Kommandos der Kategorie
    """
    filtered = {
        name: cmd for name, cmd in all_commands.items()
        if cmd.get('category') == category
    }
    
    logger.info(f"Kommandos in Kategorie '{category}': {len(filtered)}")
    return filtered


def generate_menu_code(all_commands: Dict, exclude_legacy: bool = False) -> str:
    """
    Generiert Python-Code für die Menü-Funktionen.
    
    Args:
        all_commands: Alle Kommandos
        exclude_legacy: Legacy-Kommandos ausschließen
        
    Returns:
        str: Python-Code
    """
    if exclude_legacy:
        commands = {
            name: cmd for name, cmd in all_commands.items()
            if cmd.get('category') != 'Legacy'
        }
    else:
        commands = all_commands
    
    code_lines = [
        "# === GENERIERTE MENÜ-FUNKTIONEN ===",
        "# Automatisch generiert - nicht manuell bearbeiten",
        "",
        "def add_dialog_menu_functions(menu_handler):",
        '    """Fügt flexible Dialog-Funktionen zum Menü hinzu."""',
        "    new_functions = {"
    ]
    
    for name, cmd in commands.items():
        description = cmd.get('description', 'Keine Beschreibung')
        code = cmd.get('code', 'pass')
        category = cmd.get('category', 'Unbekannt')
        
        code_lines.append(f'        # {category}: {description}')
        code_lines.append(f'        "{name}": "{code}",')
        code_lines.append("")
    
    code_lines.extend([
        "    }",
        "",
        "    # Funktionen zum Menü hinzufügen",
        "    for name, code in new_functions.items():",
        "        menu_handler.add_function(name, code)",
        "",
        '    print(f"✅ {len(new_functions)} Dialog-Funktionen hinzugefügt")',
        "",
        "    return new_functions"
    ])
    
    return "\n".join(code_lines)


def main():
    """Hauptfunktion für Tests und Demos."""
    # Kommando-Struktur erstellen
    all_commands = update_menu_commands_flexible()
    
    # Übersetzbare Kommandos anzeigen
    translatable = get_translatable_commands(all_commands)
    print(f"\n🌐 Übersetzbare Kommandos ({len(translatable)}):")
    for name in sorted(translatable.keys()):
        print(f"  - {name}")
    
    # Kategorien anzeigen
    categories = set(cmd.get('category', 'Unbekannt') for cmd in all_commands.values())
    print(f"\n📁 Verfügbare Kategorien:")
    for category in sorted(categories):
        count = len(get_commands_by_category(all_commands, category))
        print(f"  - {category}: {count} Kommandos")
    
    # Code generieren (ohne Legacy)
    code = generate_menu_code(all_commands, exclude_legacy=True)
    print(f"\n💻 Generierter Code (ohne Legacy):")
    print(code[:500] + "..." if len(code) > 500 else code)


if __name__ == "__main__":
    main()
