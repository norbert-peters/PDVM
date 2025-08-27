#!/usr/bin/env python3
"""
Debug-Tool für PDVM show_order Problem
Prüft die echten Daten im System
"""

import sys
from pathlib import Path

# Aktueller Pfad für Import
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def debug_pdvm_show_order():
    """Debuggt das show_order Problem im echten System"""
    print("🔍 Debug PDVM show_order Problem")
    
    try:
        # Lade das echte PDVM System
        from PDVM_Systemstart import main_window_class
        from PyQt5.QtWidgets import QApplication
        import sys
        
        # QApplication erstellen
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        
        # Erstelle Hauptfenster aber zeige es nicht an
        main_window = main_window_class()
        
        # Prüfe ob PDVM verfügbar ist
        if not hasattr(main_window, 'pdvm_widget') or not main_window.pdvm_widget:
            print("❌ PDVM Widget nicht verfügbar")
            return
            
        pdvm_widget = main_window.pdvm_widget
        view_manager = pdvm_widget.view_manager
        
        print("✅ PDVM System geladen")
        print(f"📊 ViewManager Typ: {type(view_manager).__name__}")
        
        # Prüfe display_view_control
        if not view_manager.display_view_control:
            print("❌ Keine display_view_control verfügbar")
            return
            
        print(f"📋 Display-Control Spalten: {len(view_manager.display_view_control.columns)}")
        
        # Prüfe Expert-Modus Status
        expert_active = view_manager.is_expert_mode_active()
        print(f"🔧 Expert-Modus aktiv: {expert_active}")
        
        # Analysiere alle Spalten
        print("\n📊 SPALTEN-ANALYSE:")
        for i, col in enumerate(view_manager.display_view_control.columns):
            name = col.get('name', 'UNBEKANNT')
            show = col.get('show', False)
            expert = col.get('expert', False)
            order = col.get('order', 'N/A')
            show_order = col.get('show_order', 'N/A')
            
            status = "🔧" if expert else "👤"
            visible = "✅" if show else "❌"
            
            print(f"   {status} {name}: show={visible}, expert={expert}, order={order}, show_order={show_order}")
        
        # Teste _get_order_for_mode Funktion
        print("\n🧪 TESTE _get_order_for_mode:")
        
        normal_cols = [col for col in view_manager.display_view_control.columns 
                      if col.get('show', False) and not col.get('expert', False)]
        
        print(f"📋 Normal-Mode Spalten ({len(normal_cols)}):")
        for col in normal_cols:
            name = col['name']
            order_expert = view_manager._get_order_for_mode(name, expert_mode=True)
            order_normal = view_manager._get_order_for_mode(name, expert_mode=False)
            print(f"   {name}: Expert-Mode={order_expert}, Normal-Mode={order_normal}")
        
        # Teste Sortierung
        print("\n📊 TESTE SORTIERUNG:")
        expert_sorted = sorted(normal_cols, key=lambda col: view_manager._get_order_for_mode(col['name'], expert_mode=True))
        normal_sorted = sorted(normal_cols, key=lambda col: view_manager._get_order_for_mode(col['name'], expert_mode=False))
        
        print(f"Expert-Mode Reihenfolge: {[col['name'] for col in expert_sorted]}")
        print(f"Normal-Mode Reihenfolge: {[col['name'] for col in normal_sorted]}")
        
        if [col['name'] for col in expert_sorted] == [col['name'] for col in normal_sorted]:
            print("❌ PROBLEM: Beide Modi haben identische Reihenfolgen!")
        else:
            print("✅ OK: Modi haben unterschiedliche Reihenfolgen")
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
    except Exception as e:
        print(f"❌ Allgemeiner Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pdvm_show_order()
