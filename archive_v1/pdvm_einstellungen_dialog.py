#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EINSTELLUNGSMENÜ DIALOG

Dialog für Systemeinstellungen mit:
1. Einstellungen Spalten
2. ExpertModus ein/aus (nur für Admins)
3. Filter ein/aus
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from global_gcs import gcs

logger = logging.getLogger(__name__)

class PdvmEinstellungsDialog:
    """Dialog für Systemeinstellungen"""
    
    def __init__(self, parent=None):
        """
        Initialisierung des Einstellungs-Dialogs
        
        Args:
            parent: Parent-Fenster (optional)
        """
        self.parent = parent
        self.dialog = None
        
        # Tracking-Variablen
        self.expert_mode_var = None
        self.filter_mode_var = None
        
        logger.info("🔧 Einstellungsmenü Dialog erstellt")
    
    def show_dialog(self):
        """Zeige Einstellungsmenü Dialog"""
        try:
            # Dialog-Fenster erstellen
            self.dialog = tk.Toplevel(self.parent) if self.parent else tk.Tk()
            self.dialog.title("Systemeinstellungen")
            self.dialog.geometry("400x300")
            self.dialog.resizable(False, False)
            
            # Dialog zentrieren
            self._center_window()
            
            # GUI erstellen
            self._create_gui()
            
            # Modal machen wenn Parent vorhanden
            if self.parent:
                self.dialog.transient(self.parent)
                self.dialog.grab_set()
            
            logger.info("✅ Einstellungsmenü Dialog angezeigt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anzeigen des Einstellungsmenü Dialogs: {e}")
            messagebox.showerror("Fehler", f"Dialog konnte nicht angezeigt werden:\n{e}")
    
    def _center_window(self):
        """Zentriere Dialog auf dem Bildschirm"""
        try:
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            logger.warning(f"⚠️ Konnte Dialog nicht zentrieren: {e}")
    
    def _create_gui(self):
        """Erstelle GUI-Elemente"""
        try:
            # Hauptframe
            main_frame = ttk.Frame(self.dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Titel
            title_label = ttk.Label(main_frame, text="Systemeinstellungen", 
                                   font=("Arial", 14, "bold"))
            title_label.pack(pady=(0, 20))
            
            # Einstellungen Frame
            settings_frame = ttk.LabelFrame(main_frame, text="Anzeigeeinstellungen", 
                                          padding="10")
            settings_frame.pack(fill=tk.X, pady=(0, 15))
            
            # Button: Einstellungen Spalten
            btn_spalten = ttk.Button(settings_frame, text="Einstellungen Spalten",
                                   command=self._spalten_einstellungen)
            btn_spalten.pack(fill=tk.X, pady=2)
            
            # Admin-Einstellungen Frame (nur für Admins)
            if self.gcs.is_admin:
                admin_frame = ttk.LabelFrame(main_frame, text="Administrator-Einstellungen", 
                                           padding="10")
                admin_frame.pack(fill=tk.X, pady=(0, 15))
                
                # ExpertModus Toggle
                self.expert_mode_var = tk.BooleanVar()
                self.expert_mode_var.set(self.gcs.expert_mode)
                
                expert_check = ttk.Checkbutton(admin_frame, 
                                             text="ExpertModus aktiviert",
                                             variable=self.expert_mode_var,
                                             command=self._toggle_expert_mode)
                expert_check.pack(anchor=tk.W, pady=2)
            
            # Filter-Einstellungen Frame
            filter_frame = ttk.LabelFrame(main_frame, text="Filter-Einstellungen", 
                                        padding="10")
            filter_frame.pack(fill=tk.X, pady=(0, 15))
            
            # Filter Toggle (Platzhalter für zukünftige Implementierung)
            self.filter_mode_var = tk.BooleanVar()
            self.filter_mode_var.set(False)  # Default: aus
            
            filter_check = ttk.Checkbutton(filter_frame, 
                                         text="Filter aktiviert",
                                         variable=self.filter_mode_var,
                                         command=self._toggle_filter_mode,
                                         state="disabled")  # Erstmal deaktiviert
            filter_check.pack(anchor=tk.W, pady=2)
            
            # Info-Label für Filter
            filter_info = ttk.Label(filter_frame, 
                                  text="(Wird in zukünftiger Version implementiert)",
                                  foreground="gray")
            filter_info.pack(anchor=tk.W, pady=(0, 5))
            
            # Button Frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))
            
            # Schließen Button
            btn_close = ttk.Button(button_frame, text="Schließen", 
                                 command=self._close_dialog)
            btn_close.pack(side=tk.RIGHT)
            
            logger.info("✅ GUI-Elemente erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der GUI: {e}")
            raise
    
    def _spalten_einstellungen(self):
        """Öffne Spalten-Einstellungen Dialog"""
        try:
            # Placeholder für zukünftige Spalten-Einstellungen
            messagebox.showinfo("Spalten-Einstellungen", 
                              "Spalten-Einstellungen werden in zukünftiger Version implementiert.")
            logger.info("ℹ️ Spalten-Einstellungen aufgerufen")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Einstellungen: {e}")
            messagebox.showerror("Fehler", f"Spalten-Einstellungen Fehler:\n{e}")
    
    def _toggle_expert_mode(self):
        """ExpertModus ein/aus schalten"""
        try:
            new_mode = self.expert_mode_var.get()
            
            # In GCS speichern
            self.gcs.expert_mode = new_mode
            
            # Feedback an Benutzer
            mode_text = "aktiviert" if new_mode else "deaktiviert"
            messagebox.showinfo("ExpertModus", f"ExpertModus wurde {mode_text}.")
            
            logger.info(f"✅ ExpertModus {mode_text}: {new_mode}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des ExpertModus: {e}")
            messagebox.showerror("Fehler", f"ExpertModus konnte nicht umgeschaltet werden:\n{e}")
            # Zurücksetzen bei Fehler
            if self.expert_mode_var:
                self.expert_mode_var.set(self.gcs.expert_mode)
    
    def _toggle_filter_mode(self):
        """Filter-Modus ein/aus schalten (Platzhalter)"""
        try:
            new_mode = self.filter_mode_var.get()
            mode_text = "aktiviert" if new_mode else "deaktiviert"
            
            # Placeholder - noch nicht implementiert
            messagebox.showinfo("Filter-Modus", 
                              f"Filter-Modus {mode_text} (noch nicht implementiert).")
            
            logger.info(f"ℹ️ Filter-Modus {mode_text}: {new_mode} (Placeholder)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des Filter-Modus: {e}")
            messagebox.showerror("Fehler", f"Filter-Modus konnte nicht umgeschaltet werden:\n{e}")
    
    def _close_dialog(self):
        """Dialog schließen"""
        try:
            if self.dialog:
                self.dialog.destroy()
                self.dialog = None
            logger.info("✅ Einstellungsmenü Dialog geschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Schließen des Dialogs: {e}")

def show_einstellungen_dialog(parent=None):
    """
    Hilfsfunktion zum Anzeigen des Einstellungsmenü Dialogs
    
    Args:
        parent: Parent-Fenster (optional)
    """
    try:
        dialog = PdvmEinstellungsDialog(parent)
        dialog.show_dialog()
        return dialog
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen des Einstellungsmenü Dialogs: {e}")
        messagebox.showerror("Fehler", f"Einstellungsmenü konnte nicht geöffnet werden:\n{e}")
        return None

# Test-Funktion
if __name__ == "__main__":
    import sys
    import os
    
    # Logging konfigurieren
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test nur wenn GCS initialisiert ist
    try:
        from pdvm_central_systemsteuerung import is_gcs_initialized
        if not is_gcs_initialized():
            print("❌ GCS nicht initialisiert - kann Einstellungsmenü nicht testen")
            sys.exit(1)
        
        # Dialog anzeigen
        root = tk.Tk()
        root.withdraw()  # Hauptfenster verstecken
        
        dialog = show_einstellungen_dialog()
        if dialog and dialog.dialog:
            dialog.dialog.mainloop()
        
    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        sys.exit(1)