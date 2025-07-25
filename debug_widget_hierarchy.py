#!/usr/bin/env python3
"""
Letzte Debugging-Schritte für das Tab-Widget-Sichtbarkeitsproblem
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from pdvm_enhanced_multi_tab_widget import EnhancedUnifiedPdvmDialogWidget

def debug_widget_hierarchy():
    """Debuggt die Widget-Hierarchie im Detail"""
    
    app = QApplication(sys.argv)
    
    call_daten = {
        "app": app,
        "user_guid": "demo-user-guid-12345",
        "frame_guid": "4078079f-4028-45ed-879c-3c779ecf3d0d",
        "language": "de",
        "stichtag": "2025185"
    }
    
    print("🔧 Erstelle Enhanced Widget...")
    widget = EnhancedUnifiedPdvmDialogWidget(call_daten)
    
    print("\n🔍 DETAILLIERTE HIERARCHIE-ANALYSE:")
    
    # Haupt-Widget
    print(f"Haupt-Widget sichtbar: {widget.isVisible()}")
    print(f"Haupt-Widget Größe: {widget.size()}")
    
    # Main-Splitter
    if hasattr(widget, 'main_splitter'):
        splitter = widget.main_splitter
        print(f"\nMain-Splitter:")
        print(f"   Sichtbar: {splitter.isVisible()}")
        print(f"   Größe: {splitter.size()}")
        print(f"   Bereiche: {splitter.count()}")
        print(f"   Größen: {splitter.sizes()}")
        
        # Input-Container
        if splitter.count() > 1:
            input_container = splitter.widget(1)  # Zweiter Bereich
            print(f"\nInput-Container:")
            print(f"   Sichtbar: {input_container.isVisible()}")
            print(f"   Größe: {input_container.size()}")
            print(f"   Layout: {input_container.layout()}")
            
            # Layout des Input-Containers
            if input_container.layout():
                layout = input_container.layout()
                print(f"   Layout-Typ: {type(layout).__name__}")
                print(f"   Layout-Kinder: {layout.count()}")
                
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget():
                        child = item.widget()
                        print(f"      Kind {i}: {type(child).__name__} - Sichtbar: {child.isVisible()} - Größe: {child.size()}")
                        
                        # Wenn es das Tab-Widget ist
                        if hasattr(child, 'count') and hasattr(child, 'tabText'):
                            print(f"         >>> TAB-WIDGET GEFUNDEN <<<")
                            print(f"         Tab-Anzahl: {child.count()}")
                            print(f"         Minimale Größe: {child.minimumSize()}")
                            print(f"         Maximum Größe: {child.maximumSize()}")
                            print(f"         Size Policy: {child.sizePolicy().horizontalPolicy()}, {child.sizePolicy().verticalPolicy()}")
                            print(f"         Parent: {child.parent()}")
                            print(f"         Geometry: {child.geometry()}")
                            
                            # Expliziter Sichtbarkeits-Test
                            print(f"\n         🧪 EXPLIZITER SICHTBARKEITS-TEST:")
                            child.setVisible(True)
                            child.show()
                            child.raise_()
                            child.setMinimumHeight(200)
                            child.resize(400, 200)
                            child.updateGeometry()
                            
                            print(f"         Nach expliziter Korrektur: {child.isVisible()}")
                            print(f"         Nach expliziter Korrektur Größe: {child.size()}")
    
    # Widget anzeigen
    widget.show()
    widget.resize(1000, 700)
    
    print("\n✅ Widget angezeigt - prüfen Sie das Ergebnis")
    
    # Manual test
    import time
    QApplication.processEvents()
    time.sleep(1)
    
    # Final check
    if hasattr(widget, 'input_tabs'):
        print(f"\n🎯 FINAL CHECK:")
        print(f"   Tab-Widget sichtbar: {widget.input_tabs.isVisible()}")
        print(f"   Tab-Widget Größe: {widget.input_tabs.size()}")
        print(f"   Tab-Widget Geometry: {widget.input_tabs.geometry()}")
    
    app.exec_()

if __name__ == "__main__":
    debug_widget_hierarchy()
