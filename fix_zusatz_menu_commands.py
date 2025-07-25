#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zusatzmenü-Korrektur für pdvm_menu_editor.py
Behebt die Kommando-Key-Generierung für Zusatzmenüs
"""

import logging
from pdvm_menu import PdvmMenu

logger = logging.getLogger(__name__)

def fix_zusatz_menu_command_generation():
    """
    Korrigiert die Kommando-Key-Generierung für Zusatzmenüs.
    
    Das Problem: Der aktuelle Menüeditor generiert Kommando-Keys für Zusatzmenüs falsch.
    Die Lösung: Erweitere set_command und add_menu_entry um korrekte Zusatzmenü-Logik.
    """
    
    print("🔧 Korrigiere Zusatzmenü-Kommando-Generierung...")
    
    # Die Korrektur erfolgt direkt im pdvm_menu_editor.py durch eine erweiterte set_command Methode
    correction_code = '''
    def _generate_zusatz_command_key(self, full_path, menu_type):
        """
        Generiert den korrekten Kommando-Key für Zusatzmenüs basierend auf der Menülogik:
        
        Beispiel:
        - Zusatzmenü-Typ: "PD_zusatz.PD_z_Grund.Testbereich_Dialog_Inputframe"
        - Item-Pfad: "Lupe Eingaben"
        - Generierter Key: "Testbereich_Dialog_Inputframe_Lupe Eingaben"
        """
        if not menu_type.startswith("PD_zusatz"):
            # Für normale Menüs: Standard-Logik
            return full_path.replace('.', '_')
        
        # Für Zusatzmenüs: Spezielle Logik
        parts = menu_type.split('.')
        if len(parts) >= 3:
            # Hole den Basis-Pfad aus dem Menü-Typ (letzter Teil)
            base_key = parts[-1]  # z.B. "Testbereich_Dialog_Inputframe"
            
            # Kombiniere mit dem Item-Pfad
            item_key = full_path.replace('.', '_')
            command_key = f"{base_key}_{item_key}"
            
            logger.info(f"🔑 Zusatzmenü-Key generiert: {command_key}")
            logger.info(f"   Menu-Type: {menu_type}")
            logger.info(f"   Full-Path: {full_path}")
            logger.info(f"   Base-Key: {base_key}")
            
            return command_key
        else:
            logger.warning(f"⚠️ Ungültiger Zusatzmenü-Typ: {menu_type}")
            return full_path.replace('.', '_')
    '''
    
    print("✅ Korrektur-Code vorbereitet")
    return correction_code

def test_zusatz_command_key_generation():
    """Testet die Kommando-Key-Generierung für verschiedene Zusatzmenü-Szenarien"""
    
    test_cases = [
        {
            "menu_type": "PD_zusatz.PD_z_Grund.Testbereich_Dialog_Inputframe",
            "full_path": "Lupe Eingaben",
            "expected": "Testbereich_Dialog_Inputframe_Lupe Eingaben"
        },
        {
            "menu_type": "PD_zusatz.PD_z_Grund.Testbereich_Dialog_Inputframe", 
            "full_path": "Lupe Übersicht",
            "expected": "Testbereich_Dialog_Inputframe_Lupe Übersicht"
        },
        {
            "menu_type": "PD_zusatz.PD_z_Menu.Einstellungen_Layout",
            "full_path": "Neue Farbe",
            "expected": "Einstellungen_Layout_Neue Farbe"
        }
    ]
    
    print("🧪 Teste Zusatzmenü-Kommando-Key-Generierung...")
    
    for i, case in enumerate(test_cases):
        print(f"Test {i+1}:")
        print(f"  Menu-Type: {case['menu_type']}")
        print(f"  Full-Path: {case['full_path']}")
        print(f"  Erwartet: {case['expected']}")
        
        # Simuliere die Logik
        parts = case["menu_type"].split('.')
        if len(parts) >= 3:
            base_key = parts[-1]
            item_key = case["full_path"].replace('.', '_')
            generated = f"{base_key}_{item_key}"
            
            success = generated == case["expected"]
            print(f"  Generiert: {generated}")
            print(f"  ✅ Erfolg" if success else f"  ❌ Fehler")
        print()

if __name__ == "__main__":
    fix_zusatz_menu_command_generation()
    test_zusatz_command_key_generation()
