# enhanced_multi_tab_navigation_demo.py
# -*- coding: utf-8 -*-

"""
Demo für Enhanced Multi-Tab Navigation
====================================

Testet die neue Tab-Navigation im Multi-Tab-Modus:
- Button-Navigation für alle Tabs
- Dropdown für Tab-Wechsel  
- Keyboard-Shortcuts (Ctrl+←/→, Alt+1-9)
- Smart Tab-Anzeige mit dynamischem Update
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
import logging

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_enhanced_navigation():
    """Testet die Enhanced Multi-Tab Navigation"""
    
    print("🎨 Enhanced Multi-Tab Navigation Demo")
    print("=" * 50)
    print()
    
    # Demo Call-Daten erstellen
    call_daten = {
        "user_guid": "demo-user-guid-12345",
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "language": "de",
        "stichtag": "2025185"
    }
    
    try:
        from pdvm_enhanced_multi_tab_widget import EnhancedUnifiedPdvmDialogWidget
        
        app = QApplication(sys.argv)
        
        # Enhanced Widget erstellen
        widget = EnhancedUnifiedPdvmDialogWidget(call_daten)
        widget.show()
        
        print("✅ Enhanced Multi-Tab Widget geladen!")
        print()
        print("NAVIGATION-FEATURES:")
        print("==================")
        print("📱 F4: Multi-Tab-Modus aktivieren/deaktivieren")
        print("⚙️ F5: Konfigurations-Panel öffnen")
        print()
        print("TAB-NAVIGATION IM MULTI-TAB-MODUS:")
        print("----------------------------------")
        print("🔘 Buttons: Klick auf Tab-Buttons für Wechsel")
        print("📋 Dropdown: Tab auswählen und wechseln")
        print("◀▶ Buttons: 'Vorheriger'/'Nächster' für Navigation")
        print()
        print("KEYBOARD-SHORTCUTS:")
        print("------------------")
        print("⌨️ Ctrl+← / Ctrl+→: Vorheriger/Nächster Tab")
        print("🔢 Alt+1 bis Alt+9: Direkt zu Tab 1-9 springen")
        print("🔍 F1/F2: View/Input-Lupe")
        print("🔄 F3: Standard-Position wiederherstellen")
        print()
        print("ANLEITUNG:")
        print("----------")
        print("1. F4 drücken für Multi-Tab-Modus")
        print("2. Navigation-Bereich erscheint oben")
        print("3. Tab-Wechsel per Buttons, Dropdown oder Shortcuts")
        print("4. Beobachten Sie die dynamische Tab-Anzeige")
        print("5. F4 erneut für Rückkehr zu Standard-Modus")
        print()
        
        # Widget-Titel setzen
        widget.setWindowTitle("Enhanced Multi-Tab Navigation Demo")
        
        # Initial Status
        if hasattr(widget, 'show_status_message'):
            widget.show_status_message("🎯 Navigation-Demo bereit - F4 für Multi-Tab!")
        
        # Demo-Instruktionen als separates Fenster
        demo_window = create_demo_instructions()
        demo_window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Demo: {e}")
        print("Stellen Sie sicher, dass pdvm_enhanced_multi_tab_widget.py verfügbar ist.")

def create_demo_instructions():
    """Erstellt ein Instruktions-Fenster für die Demo"""
    
    window = QWidget()
    window.setWindowTitle("📋 Navigation Demo - Anleitung")
    window.resize(600, 500)
    
    layout = QVBoxLayout(window)
    
    # Titel
    title = QLabel("🎨 Enhanced Multi-Tab Navigation")
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3; margin: 10px;")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    
    # Anleitung
    instructions = QLabel("""
<b>🚀 TEST-SZENARIO:</b><br>
Sie haben 4 Tabs (Stammdaten, Geschäft, Zusatz, Dokumente)<br>
Im Multi-Tab-Modus werden nur 2-3 parallel angezeigt<br><br>

<b>📱 MULTI-TAB AKTIVIEREN:</b><br>
• <b>F4</b> drücken → Multi-Tab-Modus startet<br>
• Navigation-Bereich erscheint oben<br>
• Aktuelle Tabs werden parallel angezeigt<br><br>

<b>🔄 TAB-NAVIGATION TESTEN:</b><br>
• <b>Buttons</b>: Grüne = aktiv, Graue = verfügbar<br>
• <b>Dropdown</b>: Tab auswählen → automatischer Wechsel<br>
• <b>◀ ▶ Buttons</b>: Sequenzieller Tab-Wechsel<br><br>

<b>⌨️ KEYBOARD-SHORTCUTS:</b><br>
• <b>Ctrl+←/→</b>: Schnelle Tab-Navigation<br>
• <b>Alt+1-4</b>: Direkt zu Tab 1, 2, 3 oder 4<br>
• <b>F4</b>: Multi-Tab ein/aus<br>
• <b>F5</b>: Konfiguration<br><br>

<b>🎯 WAS ZU BEOBACHTEN:</b><br>
• Tab-Auswahl passt sich dynamisch an<br>
• Smart-Algorithmus: Aktiver Tab + nächste rechts<br>
• Wraparound: Nach letztem Tab kommt wieder erster<br>
• Status-Nachrichten unten<br><br>

<b>✅ ERFOLG WENN:</b><br>
• Tab-Wechsel ohne Multi-Tab-Modus zu verlassen<br>
• Flüssige Navigation zwischen allen 4 Tabs<br>
• Korrekte Anzeige der parallelen Tab-Inhalte
    """)
    
    instructions.setWordWrap(True)
    instructions.setStyleSheet("font-size: 12px; margin: 10px; line-height: 1.4;")
    layout.addWidget(instructions)
    
    # Test-Buttons
    button_layout = QHBoxLayout()
    
    test_btn = QPushButton("🎯 Demo starten")
    test_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
    test_btn.clicked.connect(lambda: print("Demo läuft bereits! Verwenden Sie das Haupt-Widget."))
    button_layout.addWidget(test_btn)
    
    close_btn = QPushButton("❌ Schließen")
    close_btn.clicked.connect(window.close)
    button_layout.addWidget(close_btn)
    
    layout.addLayout(button_layout)
    
    return window

if __name__ == "__main__":
    test_enhanced_navigation()
