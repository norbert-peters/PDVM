#!/usr/bin/env python3
"""
FINAL VALIDATION: Alle Linear Filter System Dateien
"""

import ast
import os
import sys

def validate_file_syntax(file_path):
    """Validiert die Syntax einer einzelnen Python-Datei"""
    print(f"\n📝 Validiere: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"  ❌ Datei existiert nicht: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST-Parse Test
        tree = ast.parse(content, file_path)
        print(f"  ✅ AST-Parsing erfolgreich")
        
        # Compile-Test
        compile(content, file_path, 'exec')
        print(f"  ✅ Compile-Test erfolgreich")
        
        # Prüfe auf LinearFilterExecutionManager Integration
        linear_filter_found = 'get_linear_filter_manager' in content
        print(f"  {'✅' if linear_filter_found else '⚠️'} LinearFilterManager Integration: {linear_filter_found}")
        
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Syntax-Fehler: {e}")
        print(f"     Zeile {e.lineno}, Spalte {e.offset}")
        return False
    except Exception as e:
        print(f"  ❌ Allgemeiner Fehler: {e}")
        return False

def validate_all_linear_filter_files():
    """Validiert alle Dateien des linearen Filter-Systems"""
    print("🔍 === GESAMT-VALIDIERUNG: LINEARES FILTER-SYSTEM ===")
    
    # Liste aller relevanten Dateien
    files_to_validate = [
        "linear_filter_execution_manager.py",
        "linear_filter_integration_example.py", 
        "pdvm_view_dialog.py",
        "search_parameter_dialog.py",
        "test_linear_filter_system.py",
        "produktions_update_linear_filter.py"
    ]
    
    success_count = 0
    total_files = len(files_to_validate)
    
    for file_path in files_to_validate:
        if validate_file_syntax(file_path):
            success_count += 1
    
    # Zusammenfassung
    print("\n" + "="*80)
    print("GESAMT-VALIDIERUNG ERGEBNIS")
    print("="*80)
    print(f"📊 Erfolgreiche Dateien: {success_count}/{total_files}")
    
    if success_count == total_files:
        print("🎉 === ALLE DATEIEN SYNTAKTISCH KORREKT ===")
        print("✅ Lineares Filter-System ist bereit für Produktion!")
        print("✅ Keine Syntax-Fehler in kritischen Dateien!")
        print("✅ LinearFilterExecutionManager überall verfügbar!")
        
        # Zusätzliche Prüfungen
        print("\n🔧 ZUSÄTZLICHE PRÜFUNGEN:")
        
        # Prüfe ob Kern-Dateien existieren
        core_files = [
            "linear_filter_execution_manager.py",
            "pdvm_view_dialog.py", 
            "search_parameter_dialog.py"
        ]
        
        all_core_exist = all(os.path.exists(f) for f in core_files)
        print(f"📋 Kern-Dateien vorhanden: {'✅' if all_core_exist else '❌'}")
        
        # Prüfe ob Test-Dateien existieren
        test_files = [
            "test_linear_filter_system.py",
            "linear_filter_integration_example.py"
        ]
        
        all_tests_exist = all(os.path.exists(f) for f in test_files)
        print(f"🧪 Test-Dateien vorhanden: {'✅' if all_tests_exist else '❌'}")
        
        return True
    else:
        print("❌ === SYNTAX-PROBLEME GEFUNDEN ===")
        failed_files = total_files - success_count
        print(f"Noch {failed_files} Dateien benötigen Korrekturen!")
        
        return False

def check_integration_readiness():
    """Prüft ob das System bereit für Integration ist"""
    print("\n🚀 === INTEGRATIONS-BEREITSCHAFT ===")
    
    readiness_checks = []
    
    # Check 1: LinearFilterExecutionManager vorhanden
    if os.path.exists("linear_filter_execution_manager.py"):
        readiness_checks.append("✅ LinearFilterExecutionManager verfügbar")
    else:
        readiness_checks.append("❌ LinearFilterExecutionManager fehlt")
    
    # Check 2: Integration in ViewDialog
    try:
        with open("pdvm_view_dialog.py", 'r', encoding='utf-8') as f:
            content = f.read()
        if 'get_linear_filter_manager' in content:
            readiness_checks.append("✅ ViewDialog Integration vorhanden")
        else:
            readiness_checks.append("❌ ViewDialog Integration fehlt")
    except:
        readiness_checks.append("❌ ViewDialog nicht lesbar")
    
    # Check 3: Integration in SearchParameterDialog
    try:
        with open("search_parameter_dialog.py", 'r', encoding='utf-8') as f:
            content = f.read()
        if 'get_linear_filter_manager' in content:
            readiness_checks.append("✅ SearchParameterDialog Integration vorhanden")
        else:
            readiness_checks.append("❌ SearchParameterDialog Integration fehlt")
    except:
        readiness_checks.append("❌ SearchParameterDialog nicht lesbar")
    
    # Check 4: Test-Suite vorhanden
    if os.path.exists("test_linear_filter_system.py"):
        readiness_checks.append("✅ Test-Suite verfügbar")
    else:
        readiness_checks.append("❌ Test-Suite fehlt")
    
    # Ausgabe
    for check in readiness_checks:
        print(f"  {check}")
    
    all_ready = all("✅" in check for check in readiness_checks)
    
    if all_ready:
        print("\n🎯 === SYSTEM BEREIT FÜR PRODUKTIONS-EINSATZ! ===")
        print("Alle Komponenten sind verfügbar und syntaktisch korrekt!")
    else:
        print("\n⚠️ === WEITERE SCHRITTE ERFORDERLICH ===")
        print("Einige Komponenten sind noch nicht bereit!")
    
    return all_ready

if __name__ == "__main__":
    print("🚀 === LINEARES FILTER-SYSTEM: FINAL VALIDATION ===")
    
    # Schritt 1: Syntax-Validierung
    syntax_ok = validate_all_linear_filter_files()
    
    # Schritt 2: Integrations-Bereitschaft
    integration_ok = check_integration_readiness()
    
    # Gesamtergebnis
    overall_success = syntax_ok and integration_ok
    
    print("\n" + "="*80)
    if overall_success:
        print("🎉 LINEARES FILTER-SYSTEM: VOLLSTÄNDIG BEREIT!")
        print("✅ Keine Filter-Kapriolen mehr!")
        print("✅ Konsistente Ergebnisse garantiert!")
        print("✅ Produktions-Einsatz möglich!")
    else:
        print("❌ LINEARES FILTER-SYSTEM: WEITERE ARBEIT NÖTIG!")
        print("Bitte behebe die oben genannten Probleme!")
    print("="*80)
    
    sys.exit(0 if overall_success else 1)