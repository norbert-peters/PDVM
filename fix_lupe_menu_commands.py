"""
Fix Lupe Menu Commands - Repariert fehlende Lupe-Kommandos
==========================================================

Dieses Skript fügt die fehlenden dialog_zusatz-Kommandos für die 
bestehenden Lupe-Modi-Menüeinträge hinzu.

Author: Generated for MyApplication
Date: 2024
"""

import sys
import os
import json
import sqlite3
import logging

# Logger-Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Holt eine Datenbankverbindung"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "PdvmManager.db")
        conn = sqlite3.connect(db_path)
        logger.info(f"✅ Datenbankverbindung hergestellt: {db_path}")
        return conn
    except Exception as e:
        logger.error(f"❌ Fehler bei Datenbankverbindung: {e}")
        return None

def fix_lupe_commands():
    """Repariert die fehlenden Lupe-Kommandos in der Datenbank"""
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Lade die aktuelle Menüstruktur
        cursor.execute("SELECT daten FROM menudaten WHERE uid = ?", 
                      ("d7748b79-0a4e-47b4-9cf9-98e4f7a35068",))
        result = cursor.fetchone()
        
        if not result:
            logger.error("❌ Menüdaten nicht gefunden")
            return False
        
        menu_data = json.loads(result[0])
        commands = menu_data.get("PD_commands", {})
        
        # Definiere die fehlenden Kommandos
        missing_commands = {
            "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Übersicht": "self.dialog_zusatz('View-Lupe')",
            "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Eingaben": "self.dialog_zusatz('Input-Lupe')",
            "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupen aus": "self.dialog_zusatz('Position-Normal')",
        }
        
        # Zusätzliche flexible Kommandos
        additional_commands = {
            "Dialog_View-Lupe": "self.dialog_zusatz('View-Lupe')",
            "Dialog_Input-Lupe": "self.dialog_zusatz('Input-Lupe')",
            "Dialog_Position-Normal": "self.dialog_zusatz('Position-Normal')",
            "Dialog_Lupe-View": "self.dialog_zusatz('View-Lupe')",
            "Dialog_Lupe-Input": "self.dialog_zusatz('Input-Lupe')",
            "Dialog_Lupe-Aus": "self.dialog_zusatz('Position-Normal')",
            "Dialog_Lupe-Normal": "self.dialog_zusatz('Position-Normal')",
        }
        
        # Kombiniere alle neuen Kommandos
        all_new_commands = {**missing_commands, **additional_commands}
        
        # Füge die Kommandos hinzu (überschreibe nur wenn leer oder None)
        added_count = 0
        updated_count = 0
        
        for command_key, command_value in all_new_commands.items():
            if command_key not in commands or commands[command_key] is None or commands[command_key] == "":
                commands[command_key] = command_value
                added_count += 1
                logger.info(f"✅ Hinzugefügt: {command_key}")
            else:
                # Kommando existiert bereits, prüfe ob Update nötig
                if commands[command_key] != command_value:
                    old_value = commands[command_key]
                    commands[command_key] = command_value
                    updated_count += 1
                    logger.info(f"🔄 Aktualisiert: {command_key}")
                    logger.info(f"   Alt: {old_value}")
                    logger.info(f"   Neu: {command_value}")
        
        # Speichere die aktualisierten Daten zurück
        menu_data["PD_commands"] = commands
        updated_struktur = json.dumps(menu_data, ensure_ascii=False, indent=2)
        
        cursor.execute(
            "UPDATE menudaten SET daten = ? WHERE uid = ?",
            (updated_struktur, "d7748b79-0a4e-47b4-9cf9-98e4f7a35068")
        )
        
        conn.commit()
        
        logger.info(f"🎯 Fix abgeschlossen:")
        logger.info(f"   - Hinzugefügte Kommandos: {added_count}")
        logger.info(f"   - Aktualisierte Kommandos: {updated_count}")
        logger.info(f"   - Gesamt verarbeitete Kommandos: {len(all_new_commands)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Reparieren der Lupe-Kommandos: {e}")
        return False
    finally:
        conn.close()

def verify_commands():
    """Überprüft ob die Kommandos korrekt gespeichert wurden"""
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT daten FROM menudaten WHERE uid = ?", 
                      ("d7748b79-0a4e-47b4-9cf9-98e4f7a35068",))
        result = cursor.fetchone()
        
        if not result:
            logger.error("❌ Menüdaten nicht gefunden")
            return False
        
        menu_data = json.loads(result[0])
        commands = menu_data.get("PD_commands", {})
        
        # Prüfe die wichtigsten Lupe-Kommandos
        test_commands = [
            "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Übersicht",
            "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Eingaben",
            "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupen aus",
        ]
        
        logger.info("🔍 Verifikation der Lupe-Kommandos:")
        all_ok = True
        
        for cmd in test_commands:
            if cmd in commands and commands[cmd] is not None and commands[cmd] != "":
                logger.info(f"   ✅ {cmd}: {commands[cmd]}")
            else:
                logger.error(f"   ❌ {cmd}: FEHLT oder LEER")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        logger.error(f"❌ Fehler bei der Verifikation: {e}")
        return False
    finally:
        conn.close()

def main():
    """Hauptfunktion"""
    
    logger.info("🔧 Fix Lupe Menu Commands gestartet")
    
    # 1. Repariere die Kommandos
    if fix_lupe_commands():
        logger.info("✅ Lupe-Kommandos erfolgreich repariert")
        
        # 2. Verifikation
        if verify_commands():
            logger.info("✅ Verifikation erfolgreich - alle Lupe-Kommandos sind verfügbar")
        else:
            logger.warning("⚠️ Verifikation zeigt noch fehlende Kommandos")
    else:
        logger.error("❌ Fehler beim Reparieren der Lupe-Kommandos")
    
    logger.info("🏁 Fix Lupe Menu Commands beendet")

if __name__ == "__main__":
    main()
