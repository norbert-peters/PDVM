# pdvm_multi_tab_layout.py
# -*- coding: utf-8 -*-

"""
Multi-Tab-Layout für UnifiedPdvmDialogWidget V3
===============================================

Ermöglicht parallele Anzeige von 2-3 Tabs in einem geteilten Layout.
Besonders nützlich in Kombination mit der Lupe-Funktion.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QSplitter, QPushButton, QComboBox, QLabel, QFrame,
    QButtonGroup, QCheckBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class MultiTabLayoutManager:
    """
    Verwaltet die parallele Anzeige von mehreren Tabs in einem geteilten Layout.
    """
    
    def __init__(self, parent_widget, original_tab_widget):
        self.parent = parent_widget
        self.original_tabs = original_tab_widget
        self.multi_tab_active = False
        self.current_layout = None
        self.tab_containers = []
        
        # Sammle alle verfügbaren Tabs
        self.available_tabs = []
        for i in range(self.original_tabs.count()):
            tab_widget = self.original_tabs.widget(i)
            tab_text = self.original_tabs.tabText(i)
            self.available_tabs.append({
                'widget': tab_widget,
                'text': tab_text,
                'index': i
            })
    
    def create_multi_tab_controls(self):
        """Erstellt die Steuerungselemente für das Multi-Tab-Layout"""
        
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        # Multi-Tab aktivieren/deaktivieren
        self.enable_multi_btn = QPushButton("📱 Multi-Tab")
        self.enable_multi_btn.setCheckable(True)
        self.enable_multi_btn.setToolTip("Aktiviert parallele Tab-Anzeige")
        self.enable_multi_btn.clicked.connect(self.toggle_multi_tab_mode)
        controls_layout.addWidget(self.enable_multi_btn)
        
        # Layout-Auswahl (2er oder 3er Layout)
        controls_layout.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["2 Tabs horizontal", "2 Tabs vertikal", "3 Tabs horizontal", "3 Tabs vertikal"])
        self.layout_combo.currentTextChanged.connect(self.on_layout_changed)
        controls_layout.addWidget(self.layout_combo)
        
        # Tab-Auswahl Checkboxen
        controls_layout.addWidget(QLabel("Angezeigte Tabs:"))
        self.tab_checkboxes = []
        for tab_info in self.available_tabs:
            checkbox = QCheckBox(tab_info['text'])
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.on_tab_selection_changed)
            self.tab_checkboxes.append(checkbox)
            controls_layout.addWidget(checkbox)
        
        # Standardmäßig ersten beiden Tabs auswählen
        if len(self.tab_checkboxes) >= 2:
            self.tab_checkboxes[0].setChecked(True)
            self.tab_checkboxes[1].setChecked(True)
        
        controls_layout.addStretch()
        return controls_frame
    
    def toggle_multi_tab_mode(self):
        """Schaltet zwischen Normal- und Multi-Tab-Modus um"""
        
        if self.enable_multi_btn.isChecked():
            self.activate_multi_tab_mode()
        else:
            self.deactivate_multi_tab_mode()
    
    def activate_multi_tab_mode(self):
        """Aktiviert den Multi-Tab-Modus"""
        
        try:
            # Sammle ausgewählte Tabs
            selected_tabs = []
            for i, checkbox in enumerate(self.tab_checkboxes):
                if checkbox.isChecked():
                    selected_tabs.append(self.available_tabs[i])
            
            if len(selected_tabs) < 2:
                logger.warning("⚠️ Mindestens 2 Tabs müssen ausgewählt sein")
                self.enable_multi_btn.setChecked(False)
                return
            
            # Original Tab-Widget verstecken
            self.original_tabs.hide()
            
            # Multi-Tab-Layout erstellen
            self.create_multi_tab_layout(selected_tabs)
            
            self.multi_tab_active = True
            logger.info(f"🎨 Multi-Tab-Modus aktiviert mit {len(selected_tabs)} Tabs")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktivieren des Multi-Tab-Modus: {e}")
            self.enable_multi_btn.setChecked(False)
    
    def deactivate_multi_tab_mode(self):
        """Deaktiviert den Multi-Tab-Modus"""
        
        try:
            # Multi-Tab-Layout entfernen
            if self.current_layout:
                # Tabs zurück ins Original-Widget setzen
                for container in self.tab_containers:
                    if hasattr(container, 'tab_widget'):
                        tab_widget = container.tab_widget
                        tab_text = container.tab_text
                        # Tab zurück ins Original-Widget
                        self.original_tabs.addTab(tab_widget, tab_text)
                
                # Layout-Widget entfernen
                self.current_layout.setParent(None)
                self.current_layout = None
                self.tab_containers = []
            
            # Original Tab-Widget wieder anzeigen
            self.original_tabs.show()
            
            self.multi_tab_active = False
            logger.info("🎨 Multi-Tab-Modus deaktiviert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Deaktivieren des Multi-Tab-Modus: {e}")
    
    def create_multi_tab_layout(self, selected_tabs):
        """Erstellt das geteilte Layout für die ausgewählten Tabs"""
        
        layout_type = self.layout_combo.currentText()
        
        # Layout-Container erstellen
        if "horizontal" in layout_type:
            splitter = QSplitter(Qt.Horizontal)
        else:
            splitter = QSplitter(Qt.Vertical)
        
        self.tab_containers = []
        
        # Für jeden ausgewählten Tab einen Container erstellen
        for tab_info in selected_tabs:
            container = self.create_tab_container(tab_info)
            splitter.addWidget(container)
            self.tab_containers.append(container)
        
        # Gleichmäßige Aufteilung
        tab_count = len(selected_tabs)
        equal_sizes = [100] * tab_count  # Gleiche Größen
        splitter.setSizes(equal_sizes)
        
        # Layout in Parent einfügen
        parent_layout = self.parent.layout()
        if parent_layout:
            # Multi-Tab-Layout an Position des Original-Tabs einfügen
            tab_index = parent_layout.indexOf(self.original_tabs)
            if tab_index >= 0:
                parent_layout.insertWidget(tab_index, splitter)
            else:
                parent_layout.addWidget(splitter)
        
        self.current_layout = splitter
        
        logger.info(f"🎨 Multi-Tab-Layout erstellt: {layout_type} mit {tab_count} Tabs")
    
    def create_tab_container(self, tab_info):
        """Erstellt einen Container für einen einzelnen Tab"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Tab-Header
        header = QLabel(f"📋 {tab_info['text']}")
        header.setStyleSheet("font-weight: bold; padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(header)
        
        # Tab-Widget vom Original-Tab entfernen und hier einfügen
        tab_widget = tab_info['widget']
        original_parent = tab_widget.parent()
        if original_parent:
            # Tab temporär aus Original-Tab-Widget entfernen
            index = self.original_tabs.indexOf(tab_widget)
            if index >= 0:
                self.original_tabs.removeTab(index)
        
        layout.addWidget(tab_widget)
        
        # Container-Eigenschaften für späteren Zugriff
        container.tab_widget = tab_widget
        container.tab_text = tab_info['text']
        container.tab_index = tab_info['index']
        
        return container
    
    def on_layout_changed(self):
        """Reagiert auf Änderung des Layout-Typs"""
        
        if self.multi_tab_active:
            # Layout neu erstellen
            self.deactivate_multi_tab_mode()
            self.activate_multi_tab_mode()
    
    def on_tab_selection_changed(self):
        """Reagiert auf Änderung der Tab-Auswahl"""
        
        if self.multi_tab_active:
            # Layout mit neuer Auswahl neu erstellen
            self.deactivate_multi_tab_mode()
            self.activate_multi_tab_mode()


class MultiTabLayoutWidget(QWidget):
    """
    Wrapper-Widget für Multi-Tab-Layout-Funktionalität
    Kann in bestehende Dialoge integriert werden.
    """
    
    layout_changed = pyqtSignal(str)  # Signal für Layout-Änderungen
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = None
        self.init_ui()
    
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Platzhalter für Steuerungselemente
        self.controls_container = QWidget()
        layout.addWidget(self.controls_container)
        
        # Platzhalter für Tab-Inhalt
        self.content_container = QWidget()
        layout.addWidget(self.content_container)
    
    def setup_multi_tab_manager(self, tab_widget):
        """Initialisiert den Multi-Tab-Manager mit einem Tab-Widget"""
        
        self.manager = MultiTabLayoutManager(self.content_container, tab_widget)
        
        # Steuerungselemente erstellen und anzeigen
        controls = self.manager.create_multi_tab_controls()
        controls_layout = QVBoxLayout(self.controls_container)
        controls_layout.addWidget(controls)
        
        # Tab-Widget in Content-Container einbetten
        content_layout = QVBoxLayout(self.content_container)
        content_layout.addWidget(tab_widget)
        
        logger.info("🎨 Multi-Tab-Manager erfolgreich eingerichtet")
    
    def toggle_controls_visibility(self):
        """Schaltet die Sichtbarkeit der Steuerungselemente um"""
        
        if self.controls_container.isVisible():
            self.controls_container.hide()
        else:
            self.controls_container.show()


# Hilfsfunktion für Integration in bestehende Widgets
def add_multi_tab_support(widget, tab_widget):
    """
    Fügt Multi-Tab-Unterstützung zu einem bestehenden Widget hinzu.
    
    Args:
        widget: Das Widget, dem Multi-Tab-Unterstützung hinzugefügt werden soll
        tab_widget: Das QTabWidget, das erweitert werden soll
    
    Returns:
        MultiTabLayoutManager: Der Manager für Multi-Tab-Funktionalität
    """
    
    try:
        manager = MultiTabLayoutManager(widget, tab_widget)
        
        # Steuerungselemente zu Widget-Layout hinzufügen
        controls = manager.create_multi_tab_controls()
        
        # Layout des Widgets finden und Controls hinzufügen
        layout = widget.layout()
        if layout:
            # Controls vor dem Tab-Widget einfügen
            tab_index = layout.indexOf(tab_widget)
            if tab_index >= 0:
                layout.insertWidget(tab_index, controls)
            else:
                layout.insertWidget(0, controls)  # Am Anfang einfügen
        
        logger.info("🎨 Multi-Tab-Unterstützung erfolgreich hinzugefügt")
        return manager
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Hinzufügen der Multi-Tab-Unterstützung: {e}")
        return None
