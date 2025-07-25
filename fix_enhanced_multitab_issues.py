# fix_enhanced_multitab_issues.py
# -*- coding: utf-8 -*-

"""
Behebt die Enhanced Multi-Tab Probleme
====================================

1. Buttons nicht sichtbar
2. F4 deaktiviert Multi-Tab
3. Kein Inhalt in Multi-Tab
4. Gleiches Verhalten in Test und Live
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
import logging

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_enhanced_widget_problems():
    """Testet die Enhanced Widget Probleme systematisch"""
    
    app = QApplication(sys.argv)
    
    # Demo Call-Daten
    call_daten = {
        "user_guid": "demo-user-guid-12345",
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "language": "de",
        "stichtag": "2025185"
    }
    
    try:
        # Enhanced Widget laden
        from pdvm_enhanced_multi_tab_widget import EnhancedUnifiedPdvmDialogWidget
        
        print("🔧 Erstelle Enhanced Widget...")
        widget = EnhancedUnifiedPdvmDialogWidget(call_daten)
        widget.show()
        
        print("✅ Widget erstellt!")
        
        # Problem 1: Buttons prüfen
        print("\n🔍 PROBLEM 1: Buttons prüfen")
        print("-" * 30)
        
        if hasattr(widget, 'config_btn'):
            print(f"✅ Config-Button vorhanden: {widget.config_btn.text()} - Sichtbar: {widget.config_btn.isVisible()}")
        else:
            print("❌ Config-Button fehlt")
            
        if hasattr(widget, 'multi_tab_btn'):
            print(f"✅ Multi-Tab-Button vorhanden: {widget.multi_tab_btn.text()} - Sichtbar: {widget.multi_tab_btn.isVisible()}")
        else:
            print("❌ Multi-Tab-Button fehlt")
            
        if hasattr(widget, 'input_lupe_btn'):
            print(f"✅ Input-Lupe-Button vorhanden: {widget.input_lupe_btn.text()} - Sichtbar: {widget.input_lupe_btn.isVisible()}")
        else:
            print("❌ Input-Lupe-Button fehlt")
        
        # Problem 2: Multi-Tab-Manager prüfen
        print("\n🔍 PROBLEM 2: Multi-Tab-Manager prüfen")
        print("-" * 40)
        
        if hasattr(widget, 'multi_tab_manager') and widget.multi_tab_manager:
            manager = widget.multi_tab_manager
            print(f"✅ Manager vorhanden - Multi-Tab aktiv: {manager.multi_tab_active}")
            print(f"📊 Tabs gesammelt: {len(manager.all_tab_widgets)}")
            print(f"📝 Tab-Namen: {manager.all_tab_texts}")
            print(f"⚙️ Konfiguration: {manager.config}")
        else:
            print("❌ Multi-Tab-Manager fehlt")
        
        # Problem 3: Tab-Inhalte prüfen
        print("\n🔍 PROBLEM 3: Tab-Inhalte prüfen")
        print("-" * 35)
        
        if hasattr(widget, 'input_tabs'):
            tabs = widget.input_tabs
            print(f"📱 Tab-Widget vorhanden: {tabs.count()} Tabs")
            for i in range(tabs.count()):
                tab_widget = tabs.widget(i)
                tab_text = tabs.tabText(i)
                print(f"   Tab {i+1}: '{tab_text}' - Widget: {type(tab_widget).__name__}")
                
                # Inhalt des Tabs prüfen
                if hasattr(tab_widget, 'layout') and tab_widget.layout():
                    layout = tab_widget.layout()
                    child_count = layout.count()
                    print(f"      → Layout-Kinder: {child_count}")
                else:
                    print(f"      → Kein Layout oder Inhalt")
        else:
            print("❌ input_tabs fehlt")
        
        # Interaktive Tests
        test_window = create_interactive_test_window(widget)
        test_window.show()
        
        print("\n🎯 INTERAKTIVE TESTS verfügbar!")
        print("   Verwenden Sie das Test-Fenster für manuelle Prüfungen")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"❌ Test-Fehler: {e}")
        import traceback
        traceback.print_exc()

def create_interactive_test_window(main_widget):
    """Erstellt interaktives Test-Fenster"""
    
    test_window = QWidget()
    test_window.setWindowTitle("🔧 Enhanced Multi-Tab Problem-Debugging")
    test_window.resize(500, 400)
    
    layout = QVBoxLayout(test_window)
    
    # Titel
    title = QLabel("🔧 Enhanced Multi-Tab Debugging")
    title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)
    
    # Problem-Tests
    test_layout = QVBoxLayout()
    
    # Test 1: Button-Sichtbarkeit
    btn_test = QPushButton("🔍 Test 1: Button-Sichtbarkeit prüfen")
    btn_test.clicked.connect(lambda: test_button_visibility(main_widget))
    test_layout.addWidget(btn_test)
    
    # Test 2: Multi-Tab manuell aktivieren
    mt_test = QPushButton("📱 Test 2: Multi-Tab manuell aktivieren")
    mt_test.clicked.connect(lambda: test_manual_multitab(main_widget))
    test_layout.addWidget(mt_test)
    
    # Test 3: Tab-Inhalte sichern und wiederherstellen
    content_test = QPushButton("📝 Test 3: Tab-Inhalte sichern/wiederherstellen")
    content_test.clicked.connect(lambda: test_tab_content_preservation(main_widget))
    test_layout.addWidget(content_test)
    
    # Test 4: Layout-Problem prüfen
    layout_test = QPushButton("🔧 Test 4: Layout-Hierarchie prüfen")
    layout_test.clicked.connect(lambda: test_layout_hierarchy(main_widget))
    test_layout.addWidget(layout_test)
    
    # Test 5: F4-Shortcut direkt testen
    f4_test = QPushButton("⌨️ Test 5: F4-Shortcut simulieren")
    f4_test.clicked.connect(lambda: test_f4_shortcut(main_widget))
    test_layout.addWidget(f4_test)
    
    layout.addLayout(test_layout)
    
    # Ergebnis-Bereich
    result_area = QLabel("🔄 Bereit für Debugging...")
    result_area.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
    result_area.setWordWrap(True)
    result_area.setMinimumHeight(150)
    layout.addWidget(result_area)
    
    test_window.result_area = result_area
    
    return test_window

def test_button_visibility(widget):
    """Test 1: Button-Sichtbarkeit"""
    results = []
    results.append("🔍 BUTTON-SICHTBARKEITS-TEST:")
    
    # Alle relevanten Buttons prüfen
    buttons = [
        ('config_btn', '⚙️ Konfiguration'),
        ('multi_tab_btn', '📱 Multi-Tab'),
        ('input_lupe_btn', '🔍 Input-Lupe'),
        ('view_lupe_btn', '🔍 View-Lupe')
    ]
    
    for btn_attr, btn_name in buttons:
        if hasattr(widget, btn_attr):
            btn = getattr(widget, btn_attr)
            visible = btn.isVisible()
            enabled = btn.isEnabled()
            parent_widget = btn.parent()
            parent_visible = parent_widget.isVisible() if parent_widget else False
            
            results.append(f"   {btn_name}: {'✅' if visible else '❌'} sichtbar, {'✅' if enabled else '❌'} aktiv")
            results.append(f"      Parent: {type(parent_widget).__name__ if parent_widget else 'None'} {'✅' if parent_visible else '❌'}")
        else:
            results.append(f"   {btn_name}: ❌ FEHLT")
    
    update_result_area("\n".join(results))

def test_manual_multitab(widget):
    """Test 2: Multi-Tab manuell aktivieren"""
    results = []
    results.append("📱 MULTI-TAB MANUELLER TEST:")
    
    try:
        if hasattr(widget, 'multi_tab_manager') and widget.multi_tab_manager:
            manager = widget.multi_tab_manager
            
            # Aktueller Status
            before_status = manager.multi_tab_active
            results.append(f"   Status vorher: {'🟢 Aktiv' if before_status else '🔴 Inaktiv'}")
            
            # Multi-Tab aktivieren
            if not before_status:
                manager.activate_multi_tab()
                after_status = manager.multi_tab_active
                results.append(f"   Status nachher: {'🟢 Aktiv' if after_status else '🔴 Inaktiv'}")
                
                if after_status:
                    results.append("   ✅ Multi-Tab erfolgreich aktiviert")
                    results.append(f"   📊 Angezeigte Tabs: {getattr(manager, 'displayed_tab_indices', 'N/A')}")
                else:
                    results.append("   ❌ Multi-Tab-Aktivierung fehlgeschlagen")
            else:
                results.append("   ℹ️ Multi-Tab war bereits aktiv")
                
        else:
            results.append("   ❌ Multi-Tab-Manager nicht verfügbar")
            
    except Exception as e:
        results.append(f"   ❌ Fehler: {e}")
    
    update_result_area("\n".join(results))

def test_tab_content_preservation(widget):
    """Test 3: Tab-Inhalte sichern und wiederherstellen"""
    results = []
    results.append("📝 TAB-INHALT ERHALTUNGS-TEST:")
    
    try:
        if hasattr(widget, 'input_tabs'):
            tabs = widget.input_tabs
            
            # Tab-Inhalte vor Multi-Tab dokumentieren
            tab_contents_before = []
            for i in range(tabs.count()):
                tab_widget = tabs.widget(i)
                tab_text = tabs.tabText(i)
                
                # Inhalt zählen
                content_count = 0
                if hasattr(tab_widget, 'layout') and tab_widget.layout():
                    content_count = tab_widget.layout().count()
                
                tab_contents_before.append((tab_text, content_count, type(tab_widget).__name__))
                results.append(f"   Tab '{tab_text}': {content_count} Layout-Elemente ({type(tab_widget).__name__})")
            
            results.append("")
            results.append("   📊 Tab-Inhalte erfasst - bereit für Multi-Tab-Test")
            
        else:
            results.append("   ❌ input_tabs nicht verfügbar")
            
    except Exception as e:
        results.append(f"   ❌ Fehler: {e}")
    
    update_result_area("\n".join(results))

def test_layout_hierarchy(widget):
    """Test 4: Layout-Hierarchie prüfen"""
    results = []
    results.append("🔧 LAYOUT-HIERARCHIE TEST:")
    
    try:
        # Haupt-Layout prüfen
        main_layout = widget.layout()
        if main_layout:
            results.append(f"   Haupt-Layout: {type(main_layout).__name__}")
            results.append(f"   Layout-Kinder: {main_layout.count()}")
            
            # Splitter finden
            if hasattr(widget, 'main_splitter'):
                splitter = widget.main_splitter
                results.append(f"   Main-Splitter: {type(splitter).__name__}")
                results.append(f"   Splitter-Bereiche: {splitter.count()}")
                results.append(f"   Splitter-Größen: {splitter.sizes()}")
                
                # Input-Container prüfen
                if hasattr(widget, 'input_container'):
                    input_container = widget.input_container
                    results.append(f"   Input-Container: sichtbar={input_container.isVisible()}")
                    
                    # Input-Container Layout
                    if input_container.layout():
                        layout = input_container.layout()
                        results.append(f"   Input-Layout-Kinder: {layout.count()}")
                        
                        # Durch Layout-Kinder iterieren
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if item.widget():
                                w = item.widget()
                                results.append(f"      Kind {i}: {type(w).__name__} sichtbar={w.isVisible()}")
                
        else:
            results.append("   ❌ Kein Haupt-Layout gefunden")
            
    except Exception as e:
        results.append(f"   ❌ Fehler: {e}")
    
    update_result_area("\n".join(results))

def test_f4_shortcut(widget):
    """Test 5: F4-Shortcut simulieren"""
    results = []
    results.append("⌨️ F4-SHORTCUT SIMULATIONS-TEST:")
    
    try:
        if hasattr(widget, 'toggle_multi_tab_mode'):
            # Status vor F4
            if hasattr(widget, 'multi_tab_manager') and widget.multi_tab_manager:
                before = widget.multi_tab_manager.multi_tab_active
                results.append(f"   Status vor F4: {'🟢 Aktiv' if before else '🔴 Inaktiv'}")
                
                # F4 simulieren
                widget.toggle_multi_tab_mode()
                
                # Status nach F4
                after = widget.multi_tab_manager.multi_tab_active
                results.append(f"   Status nach F4: {'🟢 Aktiv' if after else '🔴 Inaktiv'}")
                
                if before != after:
                    results.append("   ✅ F4-Toggle funktioniert")
                else:
                    results.append("   ❌ F4-Toggle ohne Wirkung")
                    
                # Button-Status prüfen
                if hasattr(widget, 'multi_tab_btn'):
                    btn_checked = widget.multi_tab_btn.isChecked()
                    results.append(f"   Button-Status: {'🟢 Gedrückt' if btn_checked else '🔴 Nicht gedrückt'}")
                    
                    if btn_checked == after:
                        results.append("   ✅ Button-Status synchron")
                    else:
                        results.append("   ❌ Button-Status nicht synchron")
                        
            else:
                results.append("   ❌ Multi-Tab-Manager nicht verfügbar")
        else:
            results.append("   ❌ toggle_multi_tab_mode Methode fehlt")
            
    except Exception as e:
        results.append(f"   ❌ Fehler: {e}")
    
    update_result_area("\n".join(results))

def update_result_area(message):
    """Aktualisiert Ergebnis-Bereich"""
    # Global result_area finden
    app = QApplication.instance()
    for widget in app.allWidgets():
        if hasattr(widget, 'result_area'):
            widget.result_area.setText(message)
            break
    print(message)

if __name__ == "__main__":
    test_enhanced_widget_problems()
