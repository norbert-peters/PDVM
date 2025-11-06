#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Menu-Struktur Korrektur Script
Korrigiert die fehlerhaften Zusatzmenü-Strukturen basierend auf der korrekten Logik.
"""

import json
import logging
from pdvm_menu import PdvmMenu

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MenuStructureCorrector:
    """Korrigiert die Menüstruktur"""
    
    def __init__(self, menu_guid="e1e77039-d1b5-46ff-b12b-cced0ae0da7c"):
        self.menu_guid = menu_guid
        self.menu = PdvmMenu(menu_guid)
        
    def analyze_current_structure(self):
        """Analysiert die aktuelle Struktur und zeigt Probleme auf"""
        logger.info("🔍 Analysiere aktuelle Menüstruktur...")
        
        if not hasattr(self.menu, '__pd_structure'):
            logger.error("❌ Keine __pd_structure gefunden!")
            return False
            
        structure = self.menu.__pd_structure
        
        # 1. Prüfe PD_commands - finde Lupe-Kommandos
        lupe_commands = {}
        if 'PD_commands' in structure:
            for cmd_key, cmd_value in structure['PD_commands'].items():
                if cmd_value and ('Lupe' in cmd_key or 'dialog_zusatz' in str(cmd_value)):
                    lupe_commands[cmd_key] = cmd_value
                    logger.info(f"🔍 Gefunden Lupe-Kommando: {cmd_key} = {cmd_value}")
        
        # 2. Analysiere PD_zusatz Struktur
        logger.info("\n📋 Aktuelle PD_zusatz Struktur:")
        if 'PD_zusatz' in structure:
            self._print_structure(structure['PD_zusatz'], "PD_zusatz")
            
        # 3. Finde den korrekten Pfad für Lupe-Zusatzmenü
        logger.info("\n🎯 Erwarteter Pfad für Dialog Inputframe Zusatzmenü:")
        logger.info("   PD_zusatz.PD_z_Grund.Testbereich.Dialog Inputframe")
        
        return True
    
    def _print_structure(self, structure, prefix="", level=0):
        """Druckt Struktur rekursiv"""
        indent = "  " * level
        if isinstance(structure, dict):
            for key, value in structure.items():
                if value is None:
                    logger.info(f"{indent}{prefix}.{key}: null")
                elif isinstance(value, dict):
                    logger.info(f"{indent}{prefix}.{key}:")
                    self._print_structure(value, f"{prefix}.{key}", level + 1)
                else:
                    logger.info(f"{indent}{prefix}.{key}: {value}")
    
    def correct_structure(self):
        """Korrigiert die Menüstruktur"""
        logger.info("🔧 Korrigiere Menüstruktur...")
        
        if not hasattr(self.menu, '__pd_structure'):
            logger.error("❌ Keine __pd_structure gefunden!")
            return False
            
        structure = self.menu.__pd_structure
        
        # 1. Korrigiere PD_zusatz Struktur
        if 'PD_zusatz' not in structure:
            structure['PD_zusatz'] = {}
            
        # Stelle sicher, dass PD_z_Grund und PD_z_Menu existieren
        if 'PD_z_Grund' not in structure['PD_zusatz']:
            structure['PD_zusatz']['PD_z_Grund'] = {}
        if 'PD_z_Menu' not in structure['PD_zusatz']:
            structure['PD_zusatz']['PD_z_Menu'] = {}
            
        # 2. Erstelle den korrekten Pfad für Dialog Inputframe Zusatzmenü
        # Basierend auf: Testbereich -> Dialog Inputframe
        # Sollte sein: PD_zusatz.PD_z_Grund.Testbereich.Dialog Inputframe
        
        zusatz_grund = structure['PD_zusatz']['PD_z_Grund']
        
        # Erstelle Testbereich falls nicht vorhanden
        if 'Testbereich' not in zusatz_grund:
            zusatz_grund['Testbereich'] = {}
            
        # Erstelle Dialog Inputframe falls nicht vorhanden
        if 'Dialog Inputframe' not in zusatz_grund['Testbereich']:
            zusatz_grund['Testbereich']['Dialog Inputframe'] = {}
            
        # Erstelle 🔍 Lupe Modi Untermenü
        lupe_menu = zusatz_grund['Testbereich']['Dialog Inputframe']
        if '🔍 Lupe Modi' not in lupe_menu:
            lupe_menu['🔍 Lupe Modi'] = {}
            
        # Füge die korrekten Lupe-Optionen hinzu
        lupe_submenu = lupe_menu['🔍 Lupe Modi']
        lupe_submenu['Lupe Übersicht'] = None
        lupe_submenu['Lupe Eingaben'] = None
        lupe_submenu['Lupen aus'] = None
        
        # 3. Korrigiere die Kommandos
        if 'PD_commands' not in structure:
            structure['PD_commands'] = {}
            
        commands = structure['PD_commands']
        
        # Entferne fehlerhafte Kommandos und erstelle korrekte
        fehlerhafte_keys = [
            'Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Übersicht',
            'Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Eingaben', 
            'Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupen aus',
            '🔍 Lupe Modi_Lupe Übersicht',
            '🔍 Lupe Modi_Lupe Eingaben',
            '🔍 Lupe Modi_Lupen aus'
        ]
        
        for key in fehlerhafte_keys:
            if key in commands:
                logger.info(f"🗑️ Entferne fehlerhaften Kommando-Key: {key}")
                del commands[key]
        
        # Erstelle korrekte Kommandos
        korrekte_kommandos = {
            'Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Übersicht': "self.dialog_zusatz('View-Lupe')",
            'Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Eingaben': "self.dialog_zusatz('Input-Lupe')",
            'Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupen aus': "self.dialog_zusatz('Position-Normal')"
        }
        
        for cmd_key, cmd_value in korrekte_kommandos.items():
            commands[cmd_key] = cmd_value
            logger.info(f"✅ Erstellt korrekten Kommando: {cmd_key} = {cmd_value}")
        
        # 4. Bereinige fehlerhafte PD_zusatz Einträge
        self._cleanup_invalid_zusatz_entries(structure)
        
        logger.info("✅ Struktur-Korrektur abgeschlossen")
        return True
    
    def _cleanup_invalid_zusatz_entries(self, structure):
        """Bereinigt fehlerhafte Zusatzmenü-Einträge"""
        logger.info("🧹 Bereinige fehlerhafte Zusatzmenü-Einträge...")
        
        # Entferne direkte Lupe-Einträge aus PD_z_Grund (falsche Platzierung)
        if 'PD_zusatz' in structure and 'PD_z_Grund' in structure['PD_zusatz']:
            zusatz_grund = structure['PD_zusatz']['PD_z_Grund']
            
            # Entferne fehlerhafte direkte Lupe-Einträge
            if 'Testbereich_Dialog Inputframe' in zusatz_grund:
                fehlerhaft = zusatz_grund['Testbereich_Dialog Inputframe']
                if isinstance(fehlerhaft, dict) and '🔍 Lupe Modi' in fehlerhaft:
                    logger.info("🗑️ Entferne fehlerhaften direkten Lupe-Eintrag")
                    del zusatz_grund['Testbereich_Dialog Inputframe']
            
            # Bereinige andere fehlerhafte Struktur-Elemente
            fehlerhafte_keys = ['Einstellungen_Layout', 'Einstellungen_Paula', 'Was nun']
            for key in fehlerhafte_keys:
                if key in zusatz_grund:
                    logger.info(f"🗑️ Entferne fehlerhaften Eintrag: {key}")
                    del zusatz_grund[key]
    
    def save_corrected_structure(self):
        """Speichert die korrigierte Struktur"""
        logger.info("💾 Speichere korrigierte Struktur...")
        
        try:
            self.menu.save_to_db()
            logger.info("✅ Struktur erfolgreich gespeichert")
            return True
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return False
    
    def print_corrected_structure(self):
        """Zeigt die korrigierte Struktur an"""
        logger.info("\n📋 Korrigierte Struktur:")
        
        if hasattr(self.menu, '__pd_structure'):
            structure = self.menu.__pd_structure
            
            # Zeige nur relevante Teile
            logger.info("\n🎯 PD_zusatz.PD_z_Grund.Testbereich:")
            if ('PD_zusatz' in structure and 
                'PD_z_Grund' in structure['PD_zusatz'] and
                'Testbereich' in structure['PD_zusatz']['PD_z_Grund']):
                
                testbereich = structure['PD_zusatz']['PD_z_Grund']['Testbereich']
                self._print_structure(testbereich, "Testbereich")
            
            logger.info("\n🔧 Relevante Kommandos:")
            if 'PD_commands' in structure:
                for cmd_key, cmd_value in structure['PD_commands'].items():
                    if 'Lupe' in cmd_key or (cmd_value and 'dialog_zusatz' in str(cmd_value)):
                        logger.info(f"   {cmd_key}: {cmd_value}")

def main():
    """Hauptfunktion"""
    corrector = MenuStructureCorrector()
    
    logger.info("🚀 Starte Menüstruktur-Korrektur...")
    
    # 1. Analysiere aktuelle Struktur
    if not corrector.analyze_current_structure():
        logger.error("❌ Analyse fehlgeschlagen")
        return
    
    # 2. Korrigiere Struktur
    if not corrector.correct_structure():
        logger.error("❌ Korrektur fehlgeschlagen")
        return
    
    # 3. Zeige korrigierte Struktur
    corrector.print_corrected_structure()
    
    # 4. Speichere Änderungen
    if corrector.save_corrected_structure():
        logger.info("🎉 Menüstruktur erfolgreich korrigiert und gespeichert!")
    else:
        logger.error("❌ Speichern fehlgeschlagen")

if __name__ == "__main__":
    main()
