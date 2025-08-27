#!/usr/bin/env python3
"""
Debug-Test für das View-Widget in der laufenden PDVM-Anwendung
"""

def debug_view_widget_state():
    """
    Debuggt den Zustand des View-Widgets in einer laufenden PDVM-Anwendung
    """
    print("🔍 DEBUG: View-Widget Zustand")
    print("=" * 40)
    
    try:
        # Test: Kann das Widget importiert werden?
        from pdvm_modern_view_widget_compact import PdvmModernViewWidget
        print("✅ View-Widget kann importiert werden")
        
        # Test: Sind alle neuen Methoden vorhanden?
        new_methods = [
            '_on_header_clicked',
            '_show_column_context_menu', 
            '_move_column',
            '_toggle_column_sort',
            '_apply_column_sorting'
        ]
        
        missing_methods = []
        for method in new_methods:
            if not hasattr(PdvmModernViewWidget, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Fehlende Methoden: {missing_methods}")
        else:
            print("✅ Alle Sortierungs-Methoden vorhanden")
        
        # Test: Überprüfe _load_table_data auf current_columns
        import inspect
        source = inspect.getsource(PdvmModernViewWidget._load_table_data)
        if 'current_columns' in source:
            print("✅ current_columns Integration vorhanden")
        else:
            print("❌ current_columns Integration fehlt")
        
        # Test: Überprüfe Fallback-Logik in Event-Handlers
        source = inspect.getsource(PdvmModernViewWidget._on_header_clicked)
        if 'data_controller' in source and 'fallback' in source.lower():
            print("✅ Fallback-Logik in Header-Handler vorhanden")
        else:
            print("❌ Fallback-Logik in Header-Handler fehlt")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug-Fehler: {e}")
        return False

def suggest_fixes():
    """
    Schlägt Lösungen für häufige Probleme vor
    """
    print("\n🔧 LÖSUNGSVORSCHLÄGE:")
    print("=" * 40)
    
    print("1. Wenn KEINE SPALTEN angezeigt werden:")
    print("   • Prüfen Sie ob view_manager.get_spalten_info() Daten liefert")
    print("   • Fallback: column_info wird aus table_data generiert")
    print("   • Debug: Logging auf DEBUG setzen")
    
    print("\n2. Wenn KEINE INHALTE in den Zellen:")
    print("   • Prüfen Sie ob view_manager.get_aktuelle_tabelle() Daten liefert")
    print("   • Prüfen Sie ob visible_columns korrekt gefiltert werden")
    print("   • Explizite Farbeinstellung in _load_table_data aktiviert")
    
    print("\n3. Wenn Sortierung nicht funktioniert:")
    print("   • data_controller ist optional - Fallback auf Qt-Sortierung")
    print("   • Header-Klick verwendet jetzt Fallback-Mechanismus")
    print("   • Rechtsklick-Menü zeigt einfache Sortier-Optionen")
    
    print("\n4. Wenn Expert-Mode Probleme:")
    print("   • expert_spalten_sichtbar wird aus column_info ermittelt")
    print("   • show=True Expert-Spalten werden angezeigt")
    print("   • Header zeigt interne Namen im Expert-Mode")

def check_common_issues():
    """
    Prüft häufige Probleme
    """
    print("\n🚨 HÄUFIGE PROBLEME:")
    print("=" * 40)
    
    issues_found = []
    
    # 1. Prüfe ob PyQt5 korrekt importiert
    try:
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor, QBrush
    except ImportError as e:
        issues_found.append(f"PyQt5 Import-Fehler: {e}")
    
    # 2. Prüfe ob view_manager Methoden vorhanden
    try:
        from pdvm_view_manager_exakt import PdvmViewManager
        required_methods = ['get_aktuelle_tabelle', 'get_spalten_info']
        
        for method in required_methods:
            if not hasattr(PdvmViewManager, method):
                issues_found.append(f"ViewManager fehlt Methode: {method}")
    except ImportError:
        issues_found.append("PdvmViewManager kann nicht importiert werden")
    
    # 3. Prüfe ColumnControl Integration
    try:
        from pdvm_central_datenbank import ColumnControl
        new_methods = ['move_column', 'update_sort_settings', 'get_column_sort_info']
        
        for method in new_methods:
            if not hasattr(ColumnControl, method):
                issues_found.append(f"ColumnControl fehlt Methode: {method}")
    except ImportError:
        issues_found.append("ColumnControl kann nicht importiert werden")
    
    if issues_found:
        for issue in issues_found:
            print(f"❌ {issue}")
    else:
        print("✅ Keine häufigen Probleme gefunden")
    
    return len(issues_found) == 0

def main():
    """Hauptfunktion für Debug"""
    debug_ok = debug_view_widget_state()
    common_ok = check_common_issues()
    
    suggest_fixes()
    
    print("\n" + "=" * 40)
    if debug_ok and common_ok:
        print("✅ View-Widget Debug erfolgreich!")
        print("\n💡 Das Widget sollte funktionieren.")
        print("Falls es immer noch Probleme gibt:")
        print("• Starten Sie die PDVM-Anwendung neu")
        print("• Prüfen Sie die Log-Ausgaben") 
        print("• Testen Sie pdvm_modern_view() in der App")
    else:
        print("❌ Es wurden Probleme gefunden!")
        print("Verwenden Sie die Lösungsvorschläge oben.")

if __name__ == "__main__":
    main()
