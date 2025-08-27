#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration des optimierten PdvmViewManager in die Hauptanwendung
Beispiel für die Verwendung mit TKinter UI
"""

import tkinter as tk
from tkinter import ttk
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ViewManagerIntegration:
    """
    Beispiel-Integration des PdvmViewManager V2.0 in eine TKinter-Anwendung
    """
    
    def __init__(self, master, central_systemsteuerung):
        self.master = master
        self.central_systemsteuerung = central_systemsteuerung
        self.view_manager = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI-Setup für ViewManager-Integration"""
        
        # Hauptframe
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control-Panel
        control_frame = ttk.LabelFrame(main_frame, text="View-Control", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons für View-Management
        ttk.Button(control_frame, text="View laden", 
                  command=self.load_view).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Spalten verwalten", 
                  command=self.manage_columns).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Expert-Modus", 
                  command=self.toggle_expert_mode).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Reset", 
                  command=self.reset_view).pack(side=tk.LEFT, padx=(0, 5))
        
        # Treeview für Datenausgabe
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.tree = ttk.Treeview(tree_frame, 
                                yscrollcommand=v_scrollbar.set,
                                xscrollcommand=h_scrollbar.set)
        
        # Scrollbar-Konfiguration
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Packing
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status-Label
        self.status_label = ttk.Label(main_frame, text="Bereit für View-Laden...")
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def load_view(self):
        """Lädt eine View mit dem optimierten ViewManager"""
        try:
            from pdvm_view_manager_v2 import PdvmViewManager
            
            # Test-View-Config (in der Praxis aus Konfigurationsdatei laden)
            view_config = {
                "ROOT": {"view_table": "persondaten"},
                "metadata": {
                    "persondaten": {
                        "felder": [
                            {"feld": "VORNAME", "name": "Vorname", "type": "string", "gruppe": "DATEN"},
                            {"feld": "NACHNAME", "name": "Nachname", "type": "string", "gruppe": "DATEN"},
                            {"feld": "GEBURTSDATUM", "name": "Geburtsdatum", "type": "date", "gruppe": "DATEN"}
                        ]
                    }
                }
            }
            
            # ViewManager initialisieren
            self.view_manager = PdvmViewManager(
                view_guid="main_view_001",
                view_config=view_config,
                central_systemsteuerung=self.central_systemsteuerung,
                stichtag=1001.0
            )
            
            # Tabelle aktualisieren
            self.update_table()
            self.status_label.config(text="✅ View erfolgreich geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View: {e}")
            self.status_label.config(text=f"❌ Fehler: {e}")
    
    def update_table(self):
        """Aktualisiert die Treeview mit den aktuellen View-Daten"""
        if not self.view_manager:
            return
        
        # Alte Daten löschen
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Spalten konfigurieren
        display_columns = self.view_manager.get_display_columns()
        self.tree.config(columns=display_columns, show='headings')
        
        # Spalten-Header setzen
        for col in display_columns:
            self.tree.heading(col, text=col.replace('_show', '').replace('_', ' ').title())
            self.tree.column(col, width=120, minwidth=80)
        
        # Daten einfügen
        display_data = self.view_manager.get_display_data()
        for row_data in display_data:
            values = [row_data.get(col, "") for col in display_columns]
            self.tree.insert("", tk.END, values=values)
        
        self.status_label.config(text=f"📊 {len(display_data)} Zeilen, {len(display_columns)} Spalten angezeigt")
    
    def manage_columns(self):
        """Öffnet Dialog für Spalten-Management"""
        if not self.view_manager:
            self.status_label.config(text="❌ Keine View geladen")
            return
        
        # Spalten-Management-Dialog
        dialog = ColumnManagementDialog(self.master, self.view_manager, self.update_table)
    
    def toggle_expert_mode(self):
        """Schaltet Expert-Modus um"""
        if not self.view_manager:
            self.status_label.config(text="❌ Keine View geladen")
            return
        
        # Alle Expert-Spalten zu normalen Spalten umwandeln
        all_columns = self.view_manager.get_all_columns_info()
        expert_columns = [col for col in all_columns if col['expert']]
        
        if expert_columns:
            for col in expert_columns:
                self.view_manager.toggle_expert_mode_column(col['name'], to_normal=True)
            
            self.update_table()
            self.status_label.config(text=f"✅ {len(expert_columns)} Expert-Spalten zu normalen Spalten umgewandelt")
        else:
            self.status_label.config(text="ℹ️ Keine Expert-Spalten vorhanden")
    
    def reset_view(self):
        """Setzt View auf Basis-Konfiguration zurück"""
        if not self.view_manager:
            self.status_label.config(text="❌ Keine View geladen")
            return
        
        self.view_manager.reset_to_basis()
        self.update_table()
        self.status_label.config(text="✅ View auf Basis zurückgesetzt")


class ColumnManagementDialog:
    """Dialog für erweiterte Spalten-Verwaltung"""
    
    def __init__(self, parent, view_manager, update_callback):
        self.view_manager = view_manager
        self.update_callback = update_callback
        
        # Dialog-Fenster
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Spalten verwalten")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        self.load_columns()
    
    def setup_dialog(self):
        """Setup des Spalten-Management-Dialogs"""
        
        # Hauptframe
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instruktionen
        ttk.Label(main_frame, text="Spalten-Sichtbarkeit verwalten:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Spalten-Liste
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox mit Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button-Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Sichtbarkeit umschalten", 
                  command=self.toggle_visibility).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Expert ↔ Normal", 
                  command=self.toggle_expert).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Schließen", 
                  command=self.close_dialog).pack(side=tk.RIGHT)
    
    def load_columns(self):
        """Lädt alle verfügbaren Spalten in die Liste"""
        all_columns = self.view_manager.get_all_columns_info()
        
        self.listbox.delete(0, tk.END)
        self.columns_data = all_columns
        
        for col in all_columns:
            status = "✅" if col['show'] else "❌"
            expert = "🔧" if col['expert'] else "👤"
            text = f"{status} {expert} {col['name']} ({col['type']})"
            self.listbox.insert(tk.END, text)
    
    def toggle_visibility(self):
        """Schaltet Sichtbarkeit der ausgewählten Spalte um"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        col_data = self.columns_data[index]
        
        # Sichtbarkeit umschalten
        new_visibility = not col_data['show']
        self.view_manager.set_column_visibility(col_data['name'], new_visibility)
        
        # Dialog und Haupttabelle aktualisieren
        self.load_columns()
        self.update_callback()
    
    def toggle_expert(self):
        """Schaltet Expert-Modus der ausgewählten Spalte um"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        col_data = self.columns_data[index]
        
        # Expert-Modus umschalten
        to_normal = col_data['expert']
        self.view_manager.toggle_expert_mode_column(col_data['name'], to_normal)
        
        # Dialog und Haupttabelle aktualisieren
        self.load_columns()
        self.update_callback()
    
    def close_dialog(self):
        """Schließt den Dialog"""
        self.dialog.destroy()


# Beispiel für die Verwendung
if __name__ == "__main__":
    
    # Mock-Systemsteuerung für Demonstration
    class MockSystemsteuerung:
        def __init__(self):
            self.data = {}
        
        def get_value(self, gruppe, feld, ab_zeit=None):
            key = f"{gruppe}.{feld}"
            return {"wert": self.data.get(key)} if key in self.data else {}
        
        def set_value(self, gruppe, feld, wert, ab_zeit=None):
            key = f"{gruppe}.{feld}"
            self.data[key] = wert
        
        def save_values(self):
            pass
    
    # Hauptanwendung
    root = tk.Tk()
    root.title("PdvmViewManager V2.0 - Integration Demo")
    root.geometry("1000x600")
    
    # Systemsteuerung
    systemsteuerung = MockSystemsteuerung()
    
    # Integration
    app = ViewManagerIntegration(root, systemsteuerung)
    
    root.mainloop()
