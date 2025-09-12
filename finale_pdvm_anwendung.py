#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINALE INTEGRATION - Systemstart mit robuster GCS-Architektur

Implementiert die endgültige Lösung:
1. Login und Benutzerdaten-Sammlung
2. GCS-Initialisierung mit user_guid + user_data
3. Stichtag-Bar mit direktem Zugriff auf gcs.st_inst
4. Parametrisierte Properties für flexible Erweiterung
"""

import sys
import logging
from tkinter import *
from tkinter import ttk
import os

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Finale GCS importieren
from pdvm_central_systemsteuerung_final import initialize_gcs, get_gcs, is_gcs_initialized

class FinaleMainApplication:
    """Finale Hauptanwendung mit robuster GCS"""
    
    def __init__(self):
        """Initialisierung der Anwendung"""
        self.root = None
        self.stichtag_bar = None
        self.current_user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"  # Test-GUID
        
        logger.info("🚀 Finale Anwendung gestartet")
    
    def simulate_login(self):
        """
        Simuliere Login-Prozess und sammle Benutzerdaten
        In der echten Anwendung würde hier der Login-Dialog kommen
        """
        logger.info("🔐 Login-Simulation...")
        
        # Simulierte Benutzerdaten nach erfolgreichem Login
        user_data = {
            'username': 'TestUser',
            'country': 'DEU',
            'role': 'admin',
            'language': 'de-de',
            'expert_mode': False,
            'login_time': '2025-09-11 10:00:00'
        }
        
        logger.info(f"✅ Login erfolgreich für User: {self.current_user_guid}")
        return user_data
    
    def initialize_gcs_system(self, user_data):
        """
        Initialisiere das GCS-System nach dem Login
        
        Args:
            user_data: Benutzerdaten vom Login
        """
        logger.info("🏗️ GCS-System wird initialisiert...")
        
        try:
            # GCS initialisieren mit user_guid und user_data
            gcs = initialize_gcs(self.current_user_guid, user_data)
            
            logger.info("✅ GCS erfolgreich initialisiert")
            logger.info(f"📅 Stichtag: {gcs.st_inst.FormTimeStamp}")
            logger.info(f"🌍 Country: {gcs.field_value('country')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ GCS-Initialisierung fehlgeschlagen: {e}")
            return False
    
    def create_main_window(self):
        """Erstelle Hauptfenster"""
        self.root = Tk()
        self.root.title("Finale PDVM-Anwendung")
        self.root.geometry("800x600")
        
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(W, E, N, S))
        
        # Titel
        title_label = ttk.Label(main_frame, text="PDVM - Finale Version", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # GCS-Status
        gcs_status = "✅ Initialisiert" if is_gcs_initialized() else "❌ Nicht initialisiert"
        status_label = ttk.Label(main_frame, text=f"GCS-Status: {gcs_status}")
        status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Stichtag-Bereich erstellen
        self._create_stichtag_section(main_frame)
        
        # Properties-Bereich erstellen
        self._create_properties_section(main_frame)
        
        logger.info("🖼️ Hauptfenster erstellt")
    
    def _create_stichtag_section(self, parent):
        """Erstelle Stichtag-Bereich"""
        # Stichtag-Frame
        stichtag_frame = ttk.LabelFrame(parent, text="Stichtag-Verwaltung", padding="10")
        stichtag_frame.grid(row=2, column=0, columnspan=2, sticky=(W, E), pady=(0, 10))
        
        try:
            gcs = get_gcs()
            
            # Aktuelle Stichtag-Anzeige
            current_label = ttk.Label(stichtag_frame, text="Aktueller Stichtag:")
            current_label.grid(row=0, column=0, sticky=W)
            
            stichtag_display = ttk.Label(stichtag_frame, 
                                       text=gcs.st_inst.FormTimeStamp,
                                       font=('Arial', 10, 'bold'))
            stichtag_display.grid(row=0, column=1, sticky=W, padx=(10, 0))
            
            # Stichtag-Eingabe (vereinfacht)
            entry_label = ttk.Label(stichtag_frame, text="Neuer Stichtag (PDVM-Format):")
            entry_label.grid(row=1, column=0, sticky=W, pady=(10, 0))
            
            self.stichtag_entry = ttk.Entry(stichtag_frame, width=20)
            self.stichtag_entry.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=(10, 0))
            
            # Buttons
            update_btn = ttk.Button(stichtag_frame, text="Stichtag ändern", 
                                  command=self._on_stichtag_update)
            update_btn.grid(row=2, column=0, pady=(10, 0))
            
            refresh_btn = ttk.Button(stichtag_frame, text="Aktualisieren", 
                                   command=self._on_stichtag_refresh)
            refresh_btn.grid(row=2, column=1, padx=(10, 0), pady=(10, 0))
            
            # Speichere Referenz für Updates
            self.stichtag_display = stichtag_display
            
        except Exception as e:
            error_label = ttk.Label(stichtag_frame, text=f"❌ Fehler: {e}", foreground="red")
            error_label.grid(row=0, column=0, columnspan=2)
    
    def _create_properties_section(self, parent):
        """Erstelle Properties-Bereich"""
        # Properties-Frame
        props_frame = ttk.LabelFrame(parent, text="System-Properties", padding="10")
        props_frame.grid(row=3, column=0, columnspan=2, sticky=(W, E))
        
        try:
            gcs = get_gcs()
            
            # Beispiel-Properties anzeigen
            properties = [
                ('Country', 'country'),
                ('Mode', 'mode'),
                ('Language', 'language'),
                ('Expert Mode', 'expert_mode')
            ]
            
            for i, (label, prop_name) in enumerate(properties):
                # Label
                prop_label = ttk.Label(props_frame, text=f"{label}:")
                prop_label.grid(row=i, column=0, sticky=W, pady=2)
                
                # Wert
                value = gcs.field_value(prop_name) or "Nicht gesetzt"
                value_label = ttk.Label(props_frame, text=str(value))
                value_label.grid(row=i, column=1, sticky=W, padx=(10, 0), pady=2)
            
        except Exception as e:
            error_label = ttk.Label(props_frame, text=f"❌ Fehler: {e}", foreground="red")
            error_label.grid(row=0, column=0, columnspan=2)
    
    def _on_stichtag_update(self):
        """Stichtag über field_value ändern"""
        try:
            new_value = self.stichtag_entry.get().strip()
            if not new_value:
                return
            
            gcs = get_gcs()
            
            # Stichtag über parametrisierte Property ändern
            gcs.field_value('stichtag', float(new_value))
            
            # Display aktualisieren
            self.stichtag_display.config(text=gcs.st_inst.FormTimeStamp)
            self.stichtag_entry.delete(0, END)
            
            logger.info(f"✅ Stichtag geändert auf: {gcs.st_inst.FormTimeStamp}")
            
        except Exception as e:
            logger.error(f"❌ Stichtag-Update fehlgeschlagen: {e}")
    
    def _on_stichtag_refresh(self):
        """Stichtag-Anzeige aktualisieren"""
        try:
            gcs = get_gcs()
            self.stichtag_display.config(text=gcs.st_inst.FormTimeStamp)
            
            logger.info(f"🔄 Stichtag aktualisiert: {gcs.st_inst.FormTimeStamp}")
            
        except Exception as e:
            logger.error(f"❌ Stichtag-Refresh fehlgeschlagen: {e}")
    
    def run(self):
        """Starte die Anwendung"""
        logger.info("🚀 Anwendungsstart...")
        
        # 1. Login simulieren
        user_data = self.simulate_login()
        
        # 2. GCS initialisieren
        if not self.initialize_gcs_system(user_data):
            logger.error("❌ Anwendungsstart abgebrochen - GCS-Fehler")
            return
        
        # 3. GUI erstellen
        self.create_main_window()
        
        # 4. Hauptschleife starten
        logger.info("🎯 GUI gestartet")
        self.root.mainloop()

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("🚀 FINALE PDVM-ANWENDUNG")
    print("=" * 60)
    print("✨ Features:")
    print("   - Robuste GCS-Architektur")
    print("   - Parametrisierte Properties")
    print("   - Automatisches Speichern")
    print("   - Spezielle Stichtag-Behandlung")
    print("=" * 60)
    
    app = FinaleMainApplication()
    app.run()

if __name__ == "__main__":
    main()
