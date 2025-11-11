"""
PDVM Menu-Editor Dialog
=======================

Hauptdialog für Menü-Bearbeitung mit:
- 2 Tabs (Vertikalmenü, Grundmenü)
- Template-basierte Item-Bearbeitung
- Live-Vorschau
- Drag & Drop Sortierung

Ablauf:
1. Lädt Menü aus man_db.sys_menudaten
2. Zeigt 2 Tabs mit Item-Listen
3. Live-Vorschau rechts
4. Speichert zurück in Datenbank

Autor: PDVM V2.0
Datum: 07.11.2025
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QSplitter, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from pdvm_central_systemsteuerung import get_gcs
from pdvm_menu_schema import MenuContainer
from pdvm_menu_items_editor import PdvmMenuItemsEditor
from pdvm_menu_preview import PdvmMenuPreview

logger = logging.getLogger(__name__)


class PdvmMenuEditorDialog(QDialog):
    """
    Hauptdialog für Menu-Bearbeitung
    
    Struktur:
    - Links: TabWidget mit Vertikalmenü + Grundmenü Editoren
    - Rechts: Live-Vorschau
    - Unten: Button-Bar (Speichern, Abbrechen, Rückgängig)
    """
    
    menu_saved = pyqtSignal(str)  # Signal wenn Menü gespeichert
    
    def __init__(self, menu_guid: str, parent=None):
        super().__init__(parent)
        self.menu_guid = menu_guid
        self.gcs = get_gcs()
        self.menu_container = None
        self.original_container = None  # Für Undo
        self.has_changes = False
        
        self._init_ui()
        self._load_menu()
    
    def _init_ui(self):
        """Erstellt UI-Struktur"""
        self.setWindowTitle("Menu-Editor: Lädt...")
        self.setModal(True)
        self.resize(1200, 800)
        
        # Haupt-Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Menu-Editor")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Splitter: Editor links, Vorschau rechts
        splitter = QSplitter(Qt.Horizontal)
        
        # LINKS: Tab-Widget mit Editoren
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Tab 1: Vertikalmenü
        self.vertikal_editor = PdvmMenuItemsEditor(
            container_type='VERTIKAL',
            parent=self
        )
        self.vertikal_editor.items_changed.connect(self._on_items_changed)
        self.tabs.addTab(self.vertikal_editor, "📋 Vertikalmenü")
        
        # Tab 2: Grundmenü
        self.grund_editor = PdvmMenuItemsEditor(
            container_type='GRUND',
            parent=self
        )
        self.grund_editor.items_changed.connect(self._on_items_changed)
        self.tabs.addTab(self.grund_editor, "📋 Grundmenü")
        
        splitter.addWidget(self.tabs)
        
        # RECHTS: Vorschau
        self.preview = PdvmMenuPreview(parent=self)
        splitter.addWidget(self.preview)
        
        # Splitter-Verhältnis: 60% Editor, 40% Vorschau
        splitter.setSizes([720, 480])
        
        layout.addWidget(splitter)
        
        # Button-Bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn_save.clicked.connect(self._save_menu)
        self.btn_save.setEnabled(False)
        
        self.btn_cancel = QPushButton("❌ Abbrechen")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_undo = QPushButton("↶ Rückgängig")
        self.btn_undo.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        self.btn_undo.clicked.connect(self._undo_changes)
        self.btn_undo.setEnabled(False)
        
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_undo)
        button_layout.addStretch()
        
        self.status_label = QLabel("Status: Bereit")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        button_layout.addWidget(self.status_label)
        
        layout.addLayout(button_layout)
    
    def _load_menu(self):
        """Lädt Menü aus Datenbank"""
        try:
            logger.info(f"🔧 Lade Menü: {self.menu_guid}")
            
            # Menü-Datenbank laden (aus man_db.sys_menudaten)
            menu_db = self.gcs._get_database_instance(
                'sys_menudaten',
                self.menu_guid
            )
            
            # Alle Daten holen
            menu_data_raw = menu_db.get_all_data()
            
            logger.info(f"📊 Menü-Daten geladen: {len(menu_data_raw)} Properties")
            
            # MenuContainer aus Daten erstellen
            # Format: VERTIKAL, GRUND, ZUSATZ, COMMANDS, etc.
            menu_data = {
                'MENU_GUID': self.menu_guid,
                'MENU_NAME': menu_data_raw.get('MENU_NAME', 'Unbekanntes Menü'),
                'VERTIKAL': menu_data_raw.get('VERTIKAL', []),
                'GRUND': menu_data_raw.get('GRUND', []),
                'ZUSATZ': menu_data_raw.get('ZUSATZ', []),
                'COMMANDS': menu_data_raw.get('COMMANDS', []),
                'IS_STARTMENU': menu_data_raw.get('IS_STARTMENU', False),
                'DESCRIPTION': menu_data_raw.get('DESCRIPTION'),
                'ABDATUM': menu_data_raw.get('ABDATUM'),
                'FORMATIERTES_ABDATUM': menu_data_raw.get('FORMATIERTES_ABDATUM')
            }
            
            self.menu_container = MenuContainer.from_dict(menu_data)
            
            # Original für Undo speichern
            self.original_container = MenuContainer.from_dict(menu_data)
            
            # Titel aktualisieren
            self.setWindowTitle(
                f"Menu-Editor: {self.menu_container.MENU_NAME}"
            )
            
            # Daten in Editoren laden
            self.vertikal_editor.set_items(self.menu_container.VERTIKAL)
            self.grund_editor.set_items(self.menu_container.GRUND)
            
            # Vorschau aktualisieren
            self._update_preview()
            
            logger.info("✅ Menü geladen")
            self.status_label.setText(
                f"Status: Geladen - {len(self.menu_container.VERTIKAL)} "
                f"Vertikal, {len(self.menu_container.GRUND)} Grund"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Fehler",
                f"Menü konnte nicht geladen werden:\n\n{str(e)}"
            )
            self.reject()
    
    def _on_items_changed(self):
        """Items wurden geändert"""
        self.has_changes = True
        self.btn_save.setEnabled(True)
        self.btn_undo.setEnabled(True)
        self.status_label.setText("Status: Ungespeicherte Änderungen *")
        self.status_label.setStyleSheet("color: #ff6600; font-style: italic; font-weight: bold;")
        
        # Vorschau aktualisieren
        self._update_preview()
    
    def _update_preview(self):
        """Aktualisiert Live-Vorschau"""
        try:
            vertikal_items = self.vertikal_editor.get_items()
            grund_items = self.grund_editor.get_items()
            
            self.preview.update_menu(
                vertikal_items=vertikal_items,
                grund_items=grund_items
            )
            
            logger.debug("🔄 Vorschau aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Vorschau-Update: {e}")
    
    def _save_menu(self):
        """Speichert Menü in Datenbank"""
        try:
            logger.info("💾 Speichere Menü...")
            
            # Items aus Editoren holen
            self.menu_container.VERTIKAL = self.vertikal_editor.get_items()
            self.menu_container.GRUND = self.grund_editor.get_items()
            
            # Validierung
            if not self._validate_menu():
                return
            
            # In Datenbank speichern
            menu_db = self.gcs._get_database_instance(
                'sys_menudaten',
                self.menu_guid
            )
            
            # MenuContainer zu Dictionary konvertieren
            menu_data = self.menu_container.to_dict()
            
            # Alle Werte setzen
            for key, value in menu_data.items():
                menu_db.set_value(key, value)
            
            # Speichern
            menu_db.save_all_values()
            
            # Status zurücksetzen
            self.has_changes = False
            self.btn_save.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.status_label.setText("Status: Gespeichert ✓")
            self.status_label.setStyleSheet("color: #4CAF50; font-style: italic; font-weight: bold;")
            
            # Original aktualisieren (für Undo)
            self.original_container = MenuContainer.from_dict(menu_data)
            
            logger.info("✅ Menü gespeichert")
            
            # Signal aussenden
            self.menu_saved.emit(self.menu_guid)
            
            QMessageBox.information(
                self,
                "Erfolg",
                f"Menü '{self.menu_container.MENU_NAME}' wurde erfolgreich gespeichert!\n\n"
                f"Vertikalmenü: {len(self.menu_container.VERTIKAL)} Items\n"
                f"Grundmenü: {len(self.menu_container.GRUND)} Items"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Fehler",
                f"Menü konnte nicht gespeichert werden:\n\n{str(e)}"
            )
    
    def _validate_menu(self) -> bool:
        """
        Validiert Menü vor dem Speichern
        
        Prüfungen:
        - Pflichtfelder vorhanden
        - Labels eindeutig
        - Commands existieren (optional)
        
        Returns:
            True wenn valide
        """
        try:
            # Sammle alle Items
            all_items = (
                self.menu_container.VERTIKAL + 
                self.menu_container.GRUND
            )
            
            # Prüfe Pflichtfelder
            for item in all_items:
                if not item.LABEL or not item.LABEL.strip():
                    QMessageBox.warning(
                        self,
                        "Validierung fehlgeschlagen",
                        "Alle Menüpunkte benötigen eine Beschriftung!"
                    )
                    return False
            
            # Prüfe Eindeutigkeit (optional - Warnung)
            labels = [item.LABEL for item in all_items]
            duplicates = set([l for l in labels if labels.count(l) > 1])
            
            if duplicates:
                reply = QMessageBox.question(
                    self,
                    "Doppelte Beschriftungen",
                    f"Folgende Beschriftungen kommen mehrfach vor:\n"
                    f"{', '.join(duplicates)}\n\n"
                    f"Trotzdem speichern?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return False
            
            logger.info("✅ Validierung erfolgreich")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Validierung: {e}")
            return False
    
    def _undo_changes(self):
        """Macht Änderungen rückgängig"""
        reply = QMessageBox.question(
            self,
            "Änderungen verwerfen?",
            "Möchten Sie alle Änderungen seit dem letzten Speichern verwerfen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Original wiederherstellen
            if self.original_container:
                self.menu_container = MenuContainer.from_dict(
                    self.original_container.to_dict()
                )
                
                # Editoren neu laden
                self.vertikal_editor.set_items(self.menu_container.VERTIKAL)
                self.grund_editor.set_items(self.menu_container.GRUND)
                
                # Vorschau aktualisieren
                self._update_preview()
            
            self.has_changes = False
            self.btn_save.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.status_label.setText("Status: Zurückgesetzt")
            self.status_label.setStyleSheet("color: #666; font-style: italic;")
            
            logger.info("↶ Änderungen rückgängig gemacht")
    
    def closeEvent(self, event):
        """Beim Schließen prüfen ob ungespeicherte Änderungen"""
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                "Es gibt ungespeicherte Änderungen.\n"
                "Möchten Sie trotzdem schließen?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        logger.info("🚪 Menu-Editor geschlossen")
        event.accept()


if __name__ == "__main__":
    print("🧪 PdvmMenuEditorDialog Test")
    print("=" * 60)
    print("Dieser Dialog kann nur in der Anwendung getestet werden.")
    print("\nFunktionen:")
    print("- 2 Tabs: Vertikalmenü, Grundmenü")
    print("- Live-Vorschau")
    print("- Speichern/Laden aus man_db.sys_menudaten")
