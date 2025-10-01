#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Einfacher Test für das Drag & Drop Interface
PDVM-System v0.9 - Isolierter Widget-Test

Testet nur die UI-Komponenten ohne GCS-Abhängigkeiten
"""

import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QLabel, QListWidget, QTreeWidget, 
                           QTreeWidgetItem, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag

# Logging Setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleAvailableColumnsList(QListWidget):
    """Vereinfachte Version der AvailableColumnsListWidget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # Test-Daten hinzufügen
        test_columns = [
            ('familienname', 'Familienname'),
            ('vorname', 'Vorname'),
            ('geburtsdatum', 'Geburtsdatum'),
            ('email', 'E-Mail'),
            ('telefon', 'Telefon'),
            ('plz', 'PLZ'),
            ('ort', 'Ort')
        ]
        
        for column_key, display_name in test_columns:
            self.addItem(f"{display_name}")
            item = self.item(self.count() - 1)
            item.setData(Qt.UserRole, f"{column_key}|{display_name}")

    def startDrag(self, supportedActions):
        """Startet Drag-Operation"""
        current_item = self.currentItem()
        if current_item:
            drag = QDrag(self)
            mimeData = QMimeData()
            
            # Custom MIME data mit column_key|display_name Format
            data = current_item.data(Qt.UserRole)
            mimeData.setText(data)
            drag.setMimeData(mimeData)
            
            logger.debug(f"🎯 Drag gestartet: {data}")
            drag.exec_(supportedActions)

class SimpleSortingTree(QTreeWidget):
    """Vereinfachte Version der SortingTreeWidget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setHeaderLabels(['Sortier-Reihenfolge', 'Richtung'])
        self.grouping_enabled = False
        
    def dragEnterEvent(self, event):
        """Drag-Enter Event"""
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Drag-Move Event"""
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Drop Event"""
        if event.mimeData().hasText():
            try:
                data = event.mimeData().text()
                parts = data.split('|')
                
                if len(parts) >= 2:
                    column_key = parts[0]
                    display_name = parts[1]
                    
                    # Prüfe Duplikate
                    for i in range(self.topLevelItemCount()):
                        existing_item = self.topLevelItem(i)
                        if existing_item.data(0, Qt.UserRole) == column_key:
                            logger.info(f"⚠️ Spalte '{display_name}' bereits vorhanden")
                            event.ignore()
                            return
                    
                    # Neues Item hinzufügen
                    item = QTreeWidgetItem([display_name, "Aufsteigend"])
                    item.setData(0, Qt.UserRole, column_key)
                    
                    # Gruppierung-Symbol hinzufügen falls aktiviert
                    if self.grouping_enabled:
                        item.setText(0, f"🏷️ {display_name}")
                        item.setToolTip(0, "Diese Spalte wird für Gruppierung verwendet")
                    
                    self.addTopLevelItem(item)
                    
                    event.accept()
                    logger.debug(f"✅ Drop erfolgreich: {column_key} → {display_name}")
                else:
                    event.ignore()
                    
            except Exception as e:
                logger.error(f"❌ Fehler beim Drop: {e}")
                event.ignore()
        else:
            event.ignore()
    
    def set_grouping_enabled(self, enabled):
        """Aktiviert/Deaktiviert Gruppierung-Modus"""
        self.grouping_enabled = enabled
        
        # Aktualisiere alle vorhandenen Items
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            current_text = item.text(0)
            
            if enabled:
                if not current_text.startswith("🏷️ "):
                    item.setText(0, f"🏷️ {current_text}")
                    item.setToolTip(0, "Diese Spalte wird für Gruppierung verwendet")
            else:
                if current_text.startswith("🏷️ "):
                    clean_text = current_text.replace("🏷️ ", "")
                    item.setText(0, clean_text)
                    item.setToolTip(0, "Sortierung")

class SimpleDragDropTest(QMainWindow):
    """Einfaches Test-Fenster für Drag & Drop"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 Drag & Drop Test - Isoliert")
        self.setGeometry(100, 100, 800, 600)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header_label = QLabel("📊 Drag & Drop Test: Spalten nach rechts ziehen")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Hauptbereich: Links Verfügbare Spalten, Rechts Sortier-Queue
        main_layout = QHBoxLayout()
        
        # Links: Verfügbare Spalten
        left_group = QGroupBox("📋 Verfügbare Spalten")
        left_layout = QVBoxLayout(left_group)
        self.available_list = SimpleAvailableColumnsList()
        left_layout.addWidget(self.available_list)
        main_layout.addWidget(left_group)
        
        # Rechts: Sortier-Queue
        right_group = QGroupBox("📊 Sortier-Reihenfolge")
        right_layout = QVBoxLayout(right_group)
        self.sorting_tree = SimpleSortingTree()
        right_layout.addWidget(self.sorting_tree)
        main_layout.addWidget(right_group)
        
        layout.addLayout(main_layout)
        
        # Gruppierung-Optionen
        grouping_group = QGroupBox("🏷️ Gruppierung")
        grouping_layout = QVBoxLayout(grouping_group)
        
        self.enable_grouping_checkbox = QCheckBox("Gruppierung aktivieren")
        self.enable_grouping_checkbox.toggled.connect(self.on_grouping_toggled)
        grouping_layout.addWidget(self.enable_grouping_checkbox)
        
        self.show_sums_checkbox = QCheckBox("Gruppen-Summen anzeigen")
        self.show_sums_checkbox.setEnabled(False)
        grouping_layout.addWidget(self.show_sums_checkbox)
        
        layout.addWidget(grouping_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("🗑️ Queue leeren")
        clear_button.clicked.connect(self.clear_queue)
        button_layout.addWidget(clear_button)
        
        button_layout.addStretch()
        
        test_button = QPushButton("🧪 Test Log")
        test_button.clicked.connect(self.show_test_log)
        button_layout.addWidget(test_button)
        
        layout.addLayout(button_layout)
        
        logger.info("✅ Test-Fenster initialisiert")
    
    def on_grouping_toggled(self, enabled):
        """Behandelt Gruppierung-Aktivierung"""
        self.show_sums_checkbox.setEnabled(enabled)
        self.sorting_tree.set_grouping_enabled(enabled)
        
        logger.info(f"🏷️ Gruppierung {'aktiviert' if enabled else 'deaktiviert'}")
    
    def clear_queue(self):
        """Leert die Sortier-Queue"""
        self.sorting_tree.clear()
        logger.info("🗑️ Sortier-Queue geleert")
    
    def show_test_log(self):
        """Zeigt aktuellen Status"""
        queue_count = self.sorting_tree.topLevelItemCount()
        grouping_enabled = self.enable_grouping_checkbox.isChecked()
        
        logger.info(f"📊 Status: {queue_count} Spalten in Queue, Gruppierung: {grouping_enabled}")
        
        # Liste alle Items auf
        for i in range(queue_count):
            item = self.sorting_tree.topLevelItem(i)
            column_key = item.data(0, Qt.UserRole)
            display_name = item.text(0)
            logger.info(f"  - {i+1}: {column_key} → {display_name}")

def main():
    """Hauptfunktion"""
    print("🧪 PDVM Drag & Drop Test - Isoliert")
    print("=" * 50)
    print("Features:")
    print("- 📊 Drag & Drop Interface (isoliert)")
    print("- 🏷️ Gruppierung-Aktivierung")
    print("- 🎯 Queue-Management")
    print("- 🧪 Keine GCS-Abhängigkeiten")
    print("=" * 50)
    print("ANLEITUNG:")
    print("1. Spalten von links nach rechts ziehen")
    print("2. Gruppierung aktivieren/deaktivieren")
    print("3. Queue mit Button leeren")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # Test-Fenster
    window = SimpleDragDropTest()
    window.show()
    
    logger.info("🚀 Isolierter Drag & Drop Test gestartet")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()