#!/usr/bin/env python3
"""
SYNTAX-FIX: Behebt Einrückungsprobleme in pdvm_view_dialog.py
"""

import re

def fix_indentation_issues():
    """Behebt systematisch alle Einrückungsprobleme"""
    
    file_path = "pdvm_view_dialog.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test vor der Korrektur
        try:
            compile(content, file_path, 'exec')
            print("✅ Datei ist bereits syntaktisch korrekt")
            return True
        except SyntaxError as e:
            print(f"🔧 Behebe Syntax-Fehler: {e}")
        
        # Korrigiere häufige Probleme
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Überspringe leere Zeilen
            if not line.strip():
                fixed_lines.append(line)
                continue
            
            # Korrigiere gemischte Einrückungen (tabs zu spaces)
            line = line.expandtabs(4)
            
            # Entferne trailing whitespaces
            line = line.rstrip()
            
            fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        # Test nach der Korrektur
        try:
            compile(fixed_content, file_path, 'exec')
            
            # Schreibe korrigierte Version
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("✅ Einrückungsprobleme behoben und Datei gespeichert")
            return True
            
        except SyntaxError as e:
            print(f"❌ Syntax-Fehler bleibt bestehen: {e}")
            print(f"   Zeile {e.lineno}: {lines[e.lineno-1] if e.lineno <= len(lines) else 'N/A'}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Beheben der Syntax: {e}")
        return False

if __name__ == "__main__":
    success = fix_indentation_issues()
    
    if success:
        print("🎉 pdvm_view_dialog.py ist jetzt syntaktisch korrekt!")
    else:
        print("❌ Weitere manuelle Korrekturen erforderlich")