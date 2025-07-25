#!/usr/bin/env python3
"""
Definitive Korrektur für das Tab-Sichtbarkeitsproblem
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer
import logging

logger = logging.getLogger(__name__)

def fix_tab_widget_visibility():
    """
    Korrigiert das Tab-Widget-Sichtbarkeitsproblem durch:
    1. Explizite Größenvergabe
    2. Layout-Update-Erzwingung
    3. Delayed-Visibility-Check
    """
    
    # Enhanced Multi-Tab Widget korrigieren
    widget_file = "pdvm_enhanced_multi_tab_widget.py"
    
    # Problematische Stelle identifiziert: Nach Manager-Init muss das Tab-Widget
    # korrekt dimensioniert und sichtbar gemacht werden
    
    fix_code = '''
    def create_enhanced_input_container(self):
        """Erstellt den erweiterten Input-Container mit Enhanced Multi-Tab"""
        
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header mit erweiterten Controls
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📝 INPUT-BEREICH"))
        header_layout.addStretch()
        
        # Config-Button
        self.config_btn = QPushButton("⚙️")
        self.config_btn.setToolTip("Multi-Tab-Konfiguration")
        self.config_btn.setCheckable(True)
        self.config_btn.clicked.connect(self.toggle_config_panel)
        self.config_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.config_btn)
        
        # Multi-Tab-Button
        self.multi_tab_btn = QPushButton("📱")
        self.multi_tab_btn.setToolTip("Multi-Tab-Modus (F4)")
        self.multi_tab_btn.setCheckable(True)
        self.multi_tab_btn.clicked.connect(self.toggle_multi_tab_mode)
        self.multi_tab_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.multi_tab_btn)
        
        # Input-Lupe-Button
        self.input_lupe_btn = QPushButton("🔍")
        self.input_lupe_btn.setToolTip("Input-Lupe (F2)")
        self.input_lupe_btn.setCheckable(True)
        self.input_lupe_btn.clicked.connect(self.toggle_input_lupe)
        self.input_lupe_btn.setFixedSize(40, 40)
        header_layout.addWidget(self.input_lupe_btn)
        
        layout.addLayout(header_layout)
        
        # Tab-Widget mit echten Daten ZUERST erstellen
        self.input_tabs = QTabWidget()
        self.input_tabs.setMinimumHeight(300)  # Mindesthöhe setzen
        self.create_enhanced_demo_tabs()
        
        # Tab-Widget ZUERST zum Layout hinzufügen
        layout.addWidget(self.input_tabs, 1)
        
        # Enhanced Multi-Tab-Manager NACH Tab-Widget-Setup initialisieren
        self.multi_tab_manager = EnhancedMultiTabManager(
            container, 
            self.input_tabs, 
            self.frame_guid, 
            self.user_guid
        )
        
        # KRITISCH: Tab-Widget sichtbar machen und Size-Policy setzen
        self.input_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_tabs.show()
        self.input_tabs.setVisible(True)
        
        # Timer für delayed visibility check
        QTimer.singleShot(100, self._ensure_tab_visibility)
        
        logger.info("📱 Enhanced Multi-Tab-Manager mit Navigation erfolgreich initialisiert")
        
        return container
    
    def _ensure_tab_visibility(self):
        """Stellt sicher, dass das Tab-Widget nach der Initialisierung sichtbar ist"""
        if hasattr(self, 'input_tabs') and hasattr(self, 'multi_tab_manager'):
            if not self.multi_tab_manager.multi_tab_active:
                self.input_tabs.show()
                self.input_tabs.setVisible(True)
                self.input_tabs.raise_()
                # Layout-Update erzwingen
                if self.input_tabs.parent():
                    self.input_tabs.parent().layout().update()
                logger.info("🔄 Tab-Widget-Sichtbarkeit sichergestellt")
    '''
    
    return fix_code

if __name__ == "__main__":
    fix_code = fix_tab_widget_visibility()
    print("🔧 Korrektur-Code erstellt:")
    print("\nDas Problem liegt in der Initialisierungsreihenfolge:")
    print("1. Tab-Widget muss VOR Manager erstellt werden")
    print("2. Explizite Größenvorgabe ist erforderlich")  
    print("3. Delayed-Visibility-Check verhindert Race-Conditions")
    print("\n📋 Fix-Code:\n")
    print(fix_code)
