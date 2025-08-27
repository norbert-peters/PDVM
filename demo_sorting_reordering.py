#!/usr/bin/env python3
"""
Demo-Anwendung für die neue Spalten-Sortierung und -Reordering-Funktionalität
"""

import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SortingReorderingDemo(QWidget):
    """Demo-Widget für Sortierung und Spalten-Reordering"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDVM Sortierung & Spalten-Reordering Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        self.pdvm_widget = None
        self.data_controller = None
        
        self.init_ui()
        self.load_demo_data()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🎯 PDVM Sortierung & Spalten-Reordering")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(title)
        
        # Buttons für Funktionen
        self.demo_sort_btn = QPushButton("📊 Sortierung Demo")
        self.demo_sort_btn.clicked.connect(self.demo_sorting)
        header_layout.addWidget(self.demo_sort_btn)
        
        self.demo_reorder_btn = QPushButton("↔️ Reordering Demo")
        self.demo_reorder_btn.clicked.connect(self.demo_reordering)
        header_layout.addWidget(self.demo_reorder_btn)
        
        self.toggle_expert_btn = QPushButton("🔧 Expert-Mode")
        self.toggle_expert_btn.clicked.connect(self.toggle_expert_mode)
        header_layout.addWidget(self.toggle_expert_btn)
        
        layout.addLayout(header_layout)
        
        # Info-Label
        self.info_label = QLabel(
            "💡 Funktionen:\n"
            "• Klicken Sie auf Spalten-Header zum Sortieren\n"
            "• Rechtsklick auf Header für Kontext-Menü\n"
            "• Spalten nach links/rechts verschieben\n"
            "• Expert-Mode für Original-Spalten\n"
            "• UI-Parameter aus ViewDaten werden berücksichtigt"
        )
        self.info_label.setStyleSheet(
            "background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; "
            "border-radius: 5px; margin: 10px;"
        )
        layout.addWidget(self.info_label)
        
        # PDVM Widget Container
        self.pdvm_container = QWidget()
        layout.addWidget(self.pdvm_container, 1)
        
        self.setLayout(layout)
    
    def load_demo_data(self):
        """Lädt Demo-Daten in das PDVM-Widget"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            from pdvm_modern_view_widget_compact import PdvmModernViewWidget
            
            # Demo-ViewDaten mit UI-Parametern
            demo_felder = [
                {
                    "gruppe": "PersDaten",
                    "feld": "FAMILIENNAME", 
                    "name": "Familienname",
                    "type": "string",
                    "ui": {
                        "sortable": True,
                        "sortDirection": "asc",
                        "sortByOriginal": False,
                        "filterType": "contains",
                        "width": "25%"
                    }
                },
                {
                    "gruppe": "PersDaten",
                    "feld": "VORNAME",
                    "name": "Vorname", 
                    "type": "string",
                    "ui": {
                        "sortable": True,
                        "sortDirection": "asc",
                        "sortByOriginal": False,
                        "filterType": "contains",
                        "width": "20%"
                    }
                },
                {
                    "gruppe": "PersDaten",
                    "feld": "GEBURTSDATUM",
                    "name": "Geburtsdatum",
                    "type": "date",
                    "ui": {
                        "sortable": True,
                        "sortDirection": "desc",
                        "sortByOriginal": True,
                        "filterType": "dateRange",
                        "width": "15%"
                    }
                },
                {
                    "gruppe": "PersDaten",
                    "feld": "ANREDE",
                    "name": "Anrede",
                    "type": "string",
                    "ui": {
                        "sortable": True,
                        "sortDirection": "asc",
                        "sortByOriginal": False,
                        "filterType": "contains",
                        "width": "10%"
                    }
                }
            ]
            
            # Demo-Datensätze
            demo_data = [
                {
                    "uid": "person-001",
                    "daten": {
                        "FAMILIENNAME": "Müller",
                        "VORNAME": "Hans",
                        "GEBURTSDATUM": "1985-03-15",
                        "ANREDE": "Herr"
                    }
                },
                {
                    "uid": "person-002", 
                    "daten": {
                        "FAMILIENNAME": "Schmidt",
                        "VORNAME": "Anna",
                        "GEBURTSDATUM": "1990-07-22",
                        "ANREDE": "Frau"
                    }
                },
                {
                    "uid": "person-003",
                    "daten": {
                        "FAMILIENNAME": "Weber", 
                        "VORNAME": "Peter",
                        "GEBURTSDATUM": "1982-11-08",
                        "ANREDE": "Herr"
                    }
                },
                {
                    "uid": "person-004",
                    "daten": {
                        "FAMILIENNAME": "Fischer",
                        "VORNAME": "Lisa",
                        "GEBURTSDATUM": "1995-01-30",
                        "ANREDE": "Frau"
                    }
                }
            ]
            
            # PDVM-Controller erstellen
            self.data_controller = PdvmCentralDatenbank()
            
            # Demo-Daten für Controller vorbereiten (simuliert DB-Zugriff)
            self.data_controller.data = {row["uid"]: row["daten"] for row in demo_data}
            self.data_controller.felder = demo_felder
            
            # PDVM-Widget erstellen
            self.pdvm_widget = PdvmModernViewWidget()
            self.pdvm_widget.data_controller = self.data_controller
            
            # Layout für PDVM-Widget
            container_layout = QVBoxLayout(self.pdvm_container)
            container_layout.addWidget(self.pdvm_widget)
            
            # Daten laden
            view_data = self.data_controller.get_value_view(demo_felder, demo_data)
            self.pdvm_widget.load_data(view_data, demo_felder, expert_mode=False)
            
            self.info_label.setText(
                "✅ Demo-Daten geladen!\n"
                f"• {len(demo_data)} Datensätze mit {len(demo_felder)} Feldern\n"
                "• UI-Parameter aus ViewDaten integriert\n"
                "• Spalten-Sortierung und -Reordering verfügbar"
            )
            
            logger.info("✅ Demo-Daten erfolgreich geladen")
            
        except Exception as e:
            error_msg = f"❌ Fehler beim Laden der Demo-Daten: {e}"
            self.info_label.setText(error_msg)
            logger.error(error_msg)
    
    def demo_sorting(self):
        """Demonstriert die Sortierungs-Funktionalität"""
        if not self.data_controller:
            return
            
        logger.info("📊 Sortierungs-Demo gestartet")
        
        # Zeige aktuell sortierbare Spalten
        if hasattr(self.data_controller, 'column_control'):
            sortable_cols = self.data_controller.column_control.get_sortable_columns()
            logger.info(f"Sortierbare Spalten: {[col['name'] for col in sortable_cols[:5]]}")
            
            # Ändere Sortierung von Familienname
            if len(sortable_cols) > 0:
                col_name = "familienname_show"
                sort_info = self.data_controller.column_control.get_column_sort_info(col_name)
                if sort_info:
                    new_dir = 'desc' if sort_info['sortDirection'] == 'asc' else 'asc'
                    self.data_controller.column_control.update_sort_settings(col_name, sort_direction=new_dir)
                    logger.info(f"Sortierung geändert: {col_name} -> {new_dir}")
                    
                    # Widget aktualisieren
                    if hasattr(self.pdvm_widget, '_apply_column_sorting'):
                        self.pdvm_widget._apply_column_sorting(col_name, new_dir, sort_info['sortByOriginal'])
        
        self.info_label.setText(
            "📊 Sortierungs-Demo ausgeführt\n"
            "• Familienname-Sortierung umgeschaltet\n"
            "• Klicken Sie auf Header für manuelle Sortierung\n"
            "• Sortierung wird in ColumnControl persistiert"
        )
    
    def demo_reordering(self):
        """Demonstriert die Spalten-Reordering-Funktionalität"""
        if not self.data_controller:
            return
            
        logger.info("↔️ Reordering-Demo gestartet")
        
        if hasattr(self.data_controller, 'column_control'):
            # Zeige aktuelle Reihenfolge
            show_cols = [col for col in self.data_controller.column_control.columns if col.get('show', False)]
            original_order = [col['name'] for col in show_cols]
            logger.info(f"Ursprüngliche Reihenfolge: {original_order}")
            
            # Bewege erste Spalte nach rechts
            if len(show_cols) >= 2:
                first_col = show_cols[0]['name']
                success = self.data_controller.column_control.move_column(first_col, 'right')
                if success:
                    # Neue Reihenfolge zeigen
                    new_show_cols = [col for col in self.data_controller.column_control.columns if col.get('show', False)]
                    new_order = [col['name'] for col in new_show_cols]
                    logger.info(f"Neue Reihenfolge: {new_order}")
                    
                    # Widget neu laden um Änderungen zu zeigen
                    if hasattr(self.pdvm_widget, '_reload_complete_widget'):
                        self.pdvm_widget._reload_complete_widget()
                    
                    self.info_label.setText(
                        f"↔️ Reordering-Demo ausgeführt\n"
                        f"• {first_col} nach rechts bewegt\n"
                        f"• Ursprünglich: {original_order[:3]}...\n"
                        f"• Neu: {new_order[:3]}..."
                    )
                else:
                    logger.warning("Spalten-Bewegung fehlgeschlagen")
    
    def toggle_expert_mode(self):
        """Wechselt zwischen Normal- und Expert-Mode"""
        if not self.pdvm_widget:
            return
            
        current_expert = getattr(self.pdvm_widget, 'expert_mode', False)
        new_expert = not current_expert
        
        # Expert-Mode umschalten
        if hasattr(self.pdvm_widget, 'set_expert_mode'):
            self.pdvm_widget.set_expert_mode(new_expert)
        elif hasattr(self.pdvm_widget, 'expert_mode'):
            self.pdvm_widget.expert_mode = new_expert
            if hasattr(self.pdvm_widget, '_reload_complete_widget'):
                self.pdvm_widget._reload_complete_widget()
        
        mode_text = "Expert" if new_expert else "Normal"
        self.toggle_expert_btn.setText(f"🔧 {mode_text}-Mode")
        
        self.info_label.setText(
            f"🔧 Mode gewechselt: {mode_text}-Mode\n"
            f"• Expert-Mode: Original-Spalten sichtbar\n"
            f"• Normal-Mode: Nur Show-Spalten sichtbar\n"
            f"• UI-Parameter bleiben erhalten"
        )
        
        logger.info(f"Mode gewechselt zu: {mode_text}")


def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    
    # Demo-Fenster erstellen
    demo = SortingReorderingDemo()
    demo.show()
    
    logger.info("🚀 PDVM Sortierung & Reordering Demo gestartet")
    logger.info("💡 Neue Features:")
    logger.info("  • Header-Klick für Sortierung")
    logger.info("  • Rechtsklick-Menü für Spalten-Management") 
    logger.info("  • UI-Parameter aus ViewDaten")
    logger.info("  • Spalten-Reordering mit Persistierung")
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
