#!/usr/bin/env python3
"""
Erweitert das Menüsystem um zentrale Funktionen und Lupe-Modi
"""

import sqlite3
import json
import uuid
from pd_datetime import Pdvm_DateTime

def add_central_functions_menu():
    """Fügt zentrale Funktionen als Zusatzmenü-Einträge hinzu"""
    
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    # Aktueller Zeitstempel
    pdvm_dt = Pdvm_DateTime()
    pdvm_dt.PdvmDateTimeNow()
    current_time = pdvm_dt.PdvmDateTime
    
    # Admin-Startmenü laden
    menu_uid = '5ca6674e-b9ce-4581-9756-64e742883f80'
    cursor.execute("SELECT daten FROM menudaten WHERE uid = ?", (menu_uid,))
    result = cursor.fetchone()
    
    if not result:
        print("❌ Menü nicht gefunden!")
        return
        
    menu_data = json.loads(result[0])
    commands = menu_data.get("PD_commands", {})
    
    # Neue zentrale Funktionen hinzufügen
    new_functions = {
        # === LUPE-FUNKTIONEN (vereinfacht) ===
        "Dialog_🔍 View-Lupe": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('set_view_lupe')",
        "Dialog_📝 Input-Lupe": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('set_input_lupe')",
        "Dialog_⚖️ Position wiederherstellen": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('set_normal_mode')",
        
        # === EINFACHE DIALOG-KOMMANDOS (ohne Emojis, übersetzbar) ===
        "Dialog_View-Lupe": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('set_view_lupe')",
        "Dialog_Input-Lupe": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('set_input_lupe')",
        "Dialog_Position-Normal": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('set_normal_mode')",
        "Dialog_Stichtag": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('stichtag_wechsel')",
        "Dialog_View-Refresh": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('refresh_view')",
        "Dialog_Daten-Speichern": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('save_data')",
        "Dialog_Daten-Export": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('export_data')",
        "Dialog_Menu-Toggle": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('toggle_menu')",
        
        # === BESTEHENDE MENÜ-EINTRÄGE (aus dem Log erkannt) ===
        "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Übersicht": "self.dialog_zusatz('View-Lupe')",
        "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupe Eingaben": "self.dialog_zusatz('Input-Lupe')",
        "Testbereich_Dialog Inputframe_🔍 Lupe Modi_Lupen aus": "self.dialog_zusatz('Position-Normal')",
        
        # === DIALOG ZUSATZ VARIANTEN ===
        "Dialog_Lupe-View": "self.dialog_zusatz('View-Lupe')",
        "Dialog_Lupe-Input": "self.dialog_zusatz('Input-Lupe')",
        "Dialog_Lupe-Aus": "self.dialog_zusatz('Position-Normal')",
        "Dialog_Lupe-Normal": "self.dialog_zusatz('Position-Normal')",
        
        # === ZENTRALE FUNKTIONEN (alte Variante) ===
        "Dialog_🗓️ Stichtag wechseln": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('stichtag_wechsel')",
        "Dialog_🔄 View refreshen": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('refresh_view')",
        "Dialog_💾 Daten speichern": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('save_data')",
        "Dialog_📊 Daten exportieren": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('export_data')",
        "Dialog_🎛️ Menü ausblenden": "widget = self.get_current_unified_widget(); widget and widget.execute_central_function('toggle_menu')"
    }
    
    # Commands hinzufügen
    for key, command in new_functions.items():
        commands[key] = command
        print(f"✅ Hinzugefügt: {key} → {command}")
    
    # Menüstruktur erweitern
    if "PD_zusatz" not in menu_data:
        menu_data["PD_zusatz"] = {"PD_z_Grund": {}, "PD_z_Menu": {}}
    
    if "PD_z_Menu" not in menu_data["PD_zusatz"]:
        menu_data["PD_zusatz"]["PD_z_Menu"] = {}
        
    # Dialog-Untermenü erstellen
    dialog_menu = {
        "🔍 Lupe-Modi": {
            "🔍 View-Lupe": None,
            "📝 Input-Lupe": None,
            "⚖️ Position wiederherstellen": None
        },
        "⚙️ Zentrale Funktionen": {
            "🗓️ Stichtag wechseln": None,
            "🔄 View refreshen": None,
            "💾 Daten speichern": None,
            "📊 Daten exportieren": None
        },
        "🎛️ Ansicht": {
            "🎛️ Menü ausblenden": None
        }
    }
    
    menu_data["PD_zusatz"]["PD_z_Menu"]["Dialog"] = dialog_menu
    
    # Speichern
    updated_json = json.dumps(menu_data, ensure_ascii=False, indent=2)
    cursor.execute("""
        UPDATE menudaten SET 
            daten = ?,
            last_modified = ?
        WHERE uid = ?
    """, (updated_json, current_time, menu_uid))
    
    conn.commit()
    
    print("\n" + "="*60)
    print("🎯 ZENTRALE FUNKTIONEN HINZUGEFÜGT")
    print("="*60)
    print("\n📋 NEUE KOMMANDOS:")
    for key, command in new_functions.items():
        print(f"  • {key}")
        print(f"    → {command}")
        print()
    
    print("\n🎛️ ZUSATZMENÜ-STRUKTUR:")
    print("  Dialog/")
    print("  ├─ 🔍 Lupe-Modi/")
    print("  │  ├─ 🔍 View-Lupe (toggle)")
    print("  │  ├─ 📝 Input-Lupe (toggle)") 
    print("  │  └─ ⚖️ Position wiederherstellen")
    print("  ├─ ⚙️ Zentrale Funktionen/")
    print("  │  ├─ 🗓️ Stichtag wechseln")
    print("  │  ├─ 🔄 View refreshen")
    print("  │  ├─ 💾 Daten speichern")
    print("  │  └─ 📊 Daten exportieren")
    print("  └─ 🎛️ Ansicht/")
    print("     └─ 🎛️ Menü ausblenden")
    
    print("\n✅ Integration erfolgreich!")
    print("💡 Die Funktionen werden verfügbar, sobald das Unified Dialog Widget geladen ist.")
    
    conn.close()

def create_menu_integration_example():
    """Erstellt Beispiel-Code für die Menü-Integration"""
    
    integration_code = '''
# === INTEGRATION IN HAUPTANWENDUNG ===

class MainApp:
    def __init__(self):
        self.unified_widget = None  # Wird gesetzt wenn Dialog geöffnet
        
    def open_unified_dialog(self):
        """Öffnet Unified Dialog und setzt Referenz für Menü-Kommandos"""
        call_data = {
            'app': self,
            'frame_guid': '4078079f-4028-45ed-879c-3c779ecf3d0d',
            'user_guid': '4886ad26-061b-4662-a762-c8c83f36692d'
        }
        
        self.unified_widget = UnifiedPdvmDialogWidget(call_data)
        self.unified_widget.show()
        
        # Zusatzmenü für Dialog-Kontext laden
        self.load_dialog_context_menu()
    
    def load_dialog_context_menu(self):
        """Lädt kontextspezifisches Zusatzmenü für Dialog"""
        try:
            dialog_menu = self.menu.get_submenu("PD_zusatz.PD_z_Menu.Dialog")
            self.update_horizontal_menu(dialog_menu)
            logger.info("✅ Dialog-Zusatzmenü geladen")
        except Exception as e:
            logger.warning(f"⚠️ Dialog-Zusatzmenü konnte nicht geladen werden: {e}")

# === KOMMANDO-AUSFÜHRUNG ===

def execute_unified_command(self, command_key):
    """Führt Unified Dialog Kommandos aus"""
    if not self.unified_widget:
        self.show_message("❌ Kein Dialog geöffnet")
        return
        
    # Kommando an Dialog weiterleiten
    if "execute_central_function" in command_key:
        # Extrahiere Funktionsname
        func_name = command_key.split("'")[1]
        result = self.unified_widget.execute_central_function(func_name)
        
        if result:
            self.show_message(f"✅ Funktion '{func_name}' ausgeführt")
        else:
            self.show_message(f"❌ Fehler bei Funktion '{func_name}'")
    '''
    
    with open("menu_integration_example.py", "w", encoding="utf-8") as f:
        f.write(integration_code)
    
    print("\n📝 Integration-Beispiel erstellt: menu_integration_example.py")

if __name__ == "__main__":
    print("🎛️ ERWEITERE MENÜSYSTEM UM ZENTRALE FUNKTIONEN")
    print("="*50)
    
    add_central_functions_menu()
    create_menu_integration_example()
    
    print("\n🚀 NÄCHSTE SCHRITTE:")
    print("1. Hauptanwendung starten")
    print("2. Unified Dialog öffnen") 
    print("3. Splitter auf gewünschte Position ziehen (z.B. 30/70)")
    print("4. Lupe-Modi mit F1, F2 testen (toggle)")
    print("5. F3 für Zurück zur benutzerdefinierten Position")
